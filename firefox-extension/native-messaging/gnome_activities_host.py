#!/usr/bin/env python3
"""
Native messaging host for GNOME Activities Firefox extension.

Reads messages from stdin using Firefox native messaging format:
  - 4-byte little-endian length prefix
  - JSON payload

Bridges to gnome-activities CLI.
"""
import json
import struct
import sys
import logging
import subprocess
from pathlib import Path

_log_dir = Path.home() / ".cache" / "gnome-activities"
_log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=str(_log_dir / "native-host.log"),
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def read_message() -> dict | None:
    """Read one native messaging message from stdin."""
    raw_length = sys.stdin.buffer.read(4)
    if len(raw_length) < 4:
        return None
    message_length = struct.unpack("<I", raw_length)[0]
    raw_message = sys.stdin.buffer.read(message_length)
    if len(raw_message) < message_length:
        return None
    return json.loads(raw_message.decode("utf-8"))


def send_message(message: dict) -> None:
    """Send one native messaging message to stdout."""
    encoded = json.dumps(message).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("<I", len(encoded)))
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()


def run_cli(*args) -> tuple[int, str]:
    """Run the gnome-activities CLI and return (returncode, stdout)."""
    try:
        result = subprocess.run(
            ["gnome-activities"] + list(args),
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode, result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        logger.warning(f"CLI invocation failed: {e}")
        return 1, ""


def handle_message(message: dict) -> dict:
    """Handle an incoming message and return a response dict."""
    msg_type = message.get("type", "")
    logger.debug(f"Received message: {msg_type}")

    if msg_type == "tab_opened":
        url = message.get("url", "")
        title = message.get("title", "")
        logger.info(f"Tab opened: {title} ({url})")
        return {"status": "ok", "type": "tab_opened"}

    elif msg_type == "tab_closed":
        tab_id = message.get("tabId")
        logger.info(f"Tab closed: {tab_id}")
        return {"status": "ok", "type": "tab_closed"}

    elif msg_type == "tab_updated":
        url = message.get("url", "")
        title = message.get("title", "")
        logger.info(f"Tab updated: {title} ({url})")
        return {"status": "ok", "type": "tab_updated"}

    elif msg_type == "get_activities":
        rc, output = run_cli("list")
        return {"status": "ok", "activities": output.splitlines()}

    elif msg_type == "get_active":
        rc, output = run_cli("status")
        return {"status": "ok", "active": output}

    else:
        logger.warning(f"Unknown message type: {msg_type}")
        return {"status": "error", "error": f"Unknown message type: {msg_type}"}


def main():
    logger.info("GNOME Activities native messaging host started")
    while True:
        try:
            message = read_message()
            if message is None:
                logger.info("stdin closed, exiting")
                break
            response = handle_message(message)
            send_message(response)
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            try:
                send_message({"status": "error", "error": str(e)})
            except Exception:
                pass
            break


if __name__ == "__main__":
    main()
