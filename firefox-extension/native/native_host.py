#!/usr/bin/env python3
"""Native messaging host for GNOME Activities Firefox extension."""
from __future__ import annotations
import json
import os
import struct
import sys
import logging
from typing import Any, Dict, Optional

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


def handle_message(message: Dict[str, Any], dbus_iface) -> None:
    """Handle an incoming message from Firefox."""
    msg_type = message.get("type")
    logger.debug("Received message type: %s", msg_type)

    if msg_type == "tabs_snapshot":
        tabs = message.get("tabs", [])
        urls = [t.get("url", "") for t in tabs if t.get("url")]
        if dbus_iface:
            try:
                current = json.loads(str(dbus_iface.Current()))
                if current and isinstance(current, dict):
                    act_name = current.get("name", "")
                    logger.debug("Updating tab URLs for activity '%s'", act_name)
            except Exception as e:
                logger.warning("Failed to update activity tabs: %s", e)

    elif msg_type in ("tab_opened", "tab_updated"):
        tab = message.get("tab", {})
        url = tab.get("url", "")
        logger.debug("Tab event %s: %s", msg_type, url)

    elif msg_type == "tab_closed":
        tab_id = message.get("tabId")
        logger.debug("Tab closed: %s", tab_id)


def main() -> None:
    """Main loop for the native messaging host."""
    logger.info("GNOME Activities native host started (PID %d)", os.getpid())
    dbus_iface = get_dbus_connection()

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
