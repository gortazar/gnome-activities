#!/usr/bin/env python3
"""Native messaging host for GNOME Activities Firefox extension."""

from __future__ import annotations

import json
import logging
import os
import queue
import struct
import sys
import threading
from typing import Any, Dict, Optional

logging.basicConfig(
    filename=os.path.expanduser("~/.local/share/gnome-activities/native-host.log"),
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# Thread-safe queue used to push outgoing messages from signal callbacks to the
# main write loop, avoiding concurrent writes to sys.stdout.
_outgoing: queue.SimpleQueue = queue.SimpleQueue()


def read_message() -> Optional[Dict[str, Any]]:
    """Read a native messaging message from stdin."""
    raw_length = sys.stdin.buffer.read(4)
    if not raw_length or len(raw_length) < 4:
        return None
    message_length = struct.unpack("=I", raw_length)[0]
    message = sys.stdin.buffer.read(message_length)
    if not message:
        return None
    try:
        return json.loads(message.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.error("Failed to decode message: %s", e)
        return None


def send_message(message: Dict[str, Any]) -> None:
    """Send a native messaging message to stdout (must be called from main thread)."""
    encoded = json.dumps(message).encode("utf-8")
    length = struct.pack("=I", len(encoded))
    sys.stdout.buffer.write(length)
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()


def _enqueue_message(message: Dict[str, Any]) -> None:
    """Queue an outgoing message from any thread (e.g. a D-Bus signal callback)."""
    _outgoing.put(message)


def get_dbus_connection():
    """Get D-Bus connection to the gnome-activities daemon."""
    try:
        import dbus

        bus = dbus.SessionBus()
        proxy = bus.get_object("org.gnome.Activities", "/org/gnome/Activities")
        iface = dbus.Interface(proxy, "org.gnome.Activities")
        return bus, iface
    except Exception as e:
        logger.warning("D-Bus connection failed: %s", e)
        return None, None


def _register_signal(bus) -> None:
    """Register the ActivityChanged signal handler after the main loop starts."""
    if bus is None:
        return
    try:
        bus.add_signal_receiver(
            lambda new_name: _enqueue_message({"type": "activity_changed", "activity": new_name}),
            dbus_interface="org.gnome.Activities",
            signal_name="ActivityChanged",
        )
        logger.debug("Registered ActivityChanged signal handler")
    except Exception as e:
        logger.warning("Could not register signal handler: %s", e)


# Tabs belonging to the current activity, keyed by tab-id.
_current_tabs: Dict[int, str] = {}


def handle_message(message: Dict[str, Any], dbus_iface) -> Optional[Dict[str, Any]]:
    """Handle an incoming message from Firefox; return the response (or None)."""
    msg_type = message.get("type")
    logger.debug("Received message type: %s", msg_type)

    if msg_type == "tabs_snapshot":
        tabs = message.get("tabs", [])
        _current_tabs.clear()
        for tab in tabs:
            if tab.get("id") and tab.get("url"):
                _current_tabs[tab["id"]] = tab["url"]
        if dbus_iface:
            try:
                import dbus

                # Forward each open URL so the daemon can restore tabs on switch.
                for url in _current_tabs.values():
                    dbus_iface.TrackAppOpened("firefox-tab", "firefox", dbus.Array([url], signature="s"))
                logger.debug("Snapshot: sent %d tab URLs to daemon", len(_current_tabs))
            except Exception as e:
                logger.warning("Failed to store tab snapshot: %s", e)
        return {"type": "ok"}

    elif msg_type in ("tab_opened", "tab_updated"):
        tab = message.get("tab", {})
        tab_id = tab.get("id")
        url = tab.get("url", "")
        if tab_id and url:
            _current_tabs[tab_id] = url
            if dbus_iface:
                try:
                    import dbus

                    dbus_iface.TrackAppOpened("firefox-tab", "firefox", dbus.Array([url], signature="s"))
                except Exception as e:
                    logger.warning("TrackAppOpened failed: %s", e)
        logger.debug("Tab event %s: %s", msg_type, url)
        return {"type": "ok"}

    elif msg_type == "tab_closed":
        tab_id = message.get("tabId")
        _current_tabs.pop(tab_id, None)
        logger.debug("Tab closed: %s", tab_id)
        return {"type": "ok"}

    elif msg_type == "get_current_activity":
        if dbus_iface:
            try:
                result = json.loads(str(dbus_iface.GetActiveActivity()))
                return {"type": "current_activity", "activity": result}
            except Exception as e:
                logger.warning("GetActiveActivity failed: %s", e)
        return {"type": "current_activity", "activity": None}

    else:
        logger.debug("Unknown message type: %s", msg_type)
        return {"type": "error", "message": f"Unknown type: {msg_type}"}


def _dbus_main_loop(bus) -> None:
    """Run the GLib main loop in a background thread to dispatch D-Bus signals."""
    try:
        from gi.repository import GLib

        loop = GLib.MainLoop()
        loop.run()
    except Exception as e:
        logger.debug("GLib main loop error: %s", e)


def main() -> None:
    """Main loop for the native messaging host."""
    logger.info("GNOME Activities native host started (PID %d)", os.getpid())
    bus, dbus_iface = get_dbus_connection()

    # Register the ActivityChanged signal handler now that we are ready.
    _register_signal(bus)

    # Run a GLib event loop in a daemon thread so D-Bus signals are dispatched.
    if bus is not None:
        t = threading.Thread(target=_dbus_main_loop, args=(bus,), daemon=True)
        t.start()

    while True:
        # Flush any queued outgoing messages first (e.g. from D-Bus signal callbacks).
        while not _outgoing.empty():
            try:
                send_message(_outgoing.get_nowait())
            except queue.Empty:
                break

        message = read_message()
        if message is None:
            logger.info("No more messages, exiting")
            break
        try:
            response = handle_message(message, dbus_iface)
            if response is not None:
                send_message(response)
        except Exception as e:
            logger.error("Error handling message: %s", e)
            send_message({"type": "error", "message": str(e)})

    logger.info("GNOME Activities native host exiting")


if __name__ == "__main__":
    main()
