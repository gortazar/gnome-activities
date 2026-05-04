#!/usr/bin/env python3
"""Native messaging host for GNOME Activities Firefox extension."""
from __future__ import annotations
import json
import os
import struct
import sys
import logging
import threading
from typing import Any, Dict, List, Optional

logging.basicConfig(
    filename=os.path.expanduser("~/.local/share/gnome-activities/native-host.log"),
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


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
    """Send a native messaging message to stdout."""
    encoded = json.dumps(message).encode("utf-8")
    length = struct.pack("=I", len(encoded))
    sys.stdout.buffer.write(length)
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()


def get_dbus_connection():
    """Get D-Bus connection to the gnome-activities daemon."""
    try:
        import dbus
        bus = dbus.SessionBus()
        proxy = bus.get_object("org.gnome.Activities", "/org/gnome/Activities")
        iface = dbus.Interface(proxy, "org.gnome.Activities")
        return iface
    except Exception as e:
        logger.warning("D-Bus connection failed: %s", e)
        return None


def subscribe_activity_changed(dbus_iface) -> None:
    """Subscribe to the ActivityChanged D-Bus signal and relay it to Firefox."""
    try:
        import dbus

        def _on_activity_changed(old_name, new_name):
            logger.debug("ActivityChanged: '%s' -> '%s'", old_name, new_name)
            try:
                # Retrieve tabs to close (from old activity) and open (for new activity).
                old_tabs: List[str] = []
                new_tabs: List[str] = []
                if dbus_iface:
                    if old_name:
                        result = str(dbus_iface.GetActivityTabs(old_name))
                        parsed = json.loads(result) if result else []
                        old_tabs = parsed if isinstance(parsed, list) else []
                    if new_name:
                        result = str(dbus_iface.GetActivityTabs(new_name))
                        parsed = json.loads(result) if result else []
                        new_tabs = parsed if isinstance(parsed, list) else []
            except Exception as e:
                logger.warning("Failed to fetch tabs for activity switch: %s", e)

            send_message({
                "type": "activity_changed",
                "old_activity": str(old_name),
                "new_activity": str(new_name),
                "close_tabs": old_tabs,
                "urls_to_open": new_tabs,
            })

        bus = dbus.SessionBus()
        bus.add_signal_receiver(
            _on_activity_changed,
            dbus_interface="org.gnome.Activities",
            signal_name="ActivityChanged",
        )
        logger.debug("Subscribed to ActivityChanged signal")
    except Exception as e:
        logger.warning("Failed to subscribe to ActivityChanged: %s", e)


def handle_message(message: Dict[str, Any], dbus_iface) -> None:
    """Handle an incoming message from Firefox."""
    msg_type = message.get("type")
    logger.debug("Received message type: %s", msg_type)

    if msg_type == "tabs_snapshot":
        tabs = message.get("tabs", [])
        urls = [t.get("url", "") for t in tabs if t.get("url")]
        if dbus_iface:
            try:
                current_json = str(dbus_iface.Current())
                current = json.loads(current_json)
                if current and isinstance(current, dict):
                    act_name = current.get("name", "")
                    if act_name:
                        dbus_iface.SetActivityTabs(act_name, json.dumps(urls))
                        logger.debug("Saved %d tabs for activity '%s'", len(urls), act_name)
            except Exception as e:
                logger.warning("Failed to update activity tabs: %s", e)

    elif msg_type in ("tab_opened", "tab_updated"):
        tab = message.get("tab", {})
        url = tab.get("url", "")
        logger.debug("Tab event %s: %s", msg_type, url)
        if dbus_iface and url:
            try:
                current_json = str(dbus_iface.Current())
                current = json.loads(current_json)
                if current and isinstance(current, dict):
                    act_name = current.get("name", "")
                    if act_name:
                        tabs_json = str(dbus_iface.GetActivityTabs(act_name))
                        urls = json.loads(tabs_json) if tabs_json else []
                        if url not in urls:
                            urls.append(url)
                            dbus_iface.SetActivityTabs(act_name, json.dumps(urls))
            except Exception as e:
                logger.warning("Failed to track tab event: %s", e)

    elif msg_type == "tab_closed":
        tab_id = message.get("tabId")
        url = message.get("url", "")
        logger.debug("Tab closed: %s url=%s", tab_id, url)
        if dbus_iface and url:
            try:
                current_json = str(dbus_iface.Current())
                current = json.loads(current_json)
                if current and isinstance(current, dict):
                    act_name = current.get("name", "")
                    if act_name:
                        tabs_json = str(dbus_iface.GetActivityTabs(act_name))
                        urls = json.loads(tabs_json) if tabs_json else []
                        urls = [u for u in urls if u != url]
                        dbus_iface.SetActivityTabs(act_name, json.dumps(urls))
            except Exception as e:
                logger.warning("Failed to remove closed tab: %s", e)


def _run_glib_loop() -> None:
    """Run a GLib main loop for D-Bus signal reception in a background thread."""
    try:
        from gi.repository import GLib
        loop = GLib.MainLoop()
        loop.run()
    except Exception as e:
        logger.warning("GLib main loop error: %s", e)


def main() -> None:
    """Main loop for the native messaging host."""
    logger.info("GNOME Activities native host started (PID %d)", os.getpid())
    dbus_iface = get_dbus_connection()
    subscribe_activity_changed(dbus_iface)

    # Run a GLib event loop in a daemon thread to receive D-Bus signals.
    glib_thread = threading.Thread(target=_run_glib_loop, daemon=True)
    glib_thread.start()

    while True:
        message = read_message()
        if message is None:
            logger.info("No more messages, exiting")
            break
        try:
            handle_message(message, dbus_iface)
        except Exception as e:
            logger.error("Error handling message: %s", e)

    logger.info("GNOME Activities native host exiting")


if __name__ == "__main__":
    main()
