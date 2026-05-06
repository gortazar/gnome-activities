"""Window monitor for GNOME Activities daemon."""

from __future__ import annotations
import logging
import threading
import time
from typing import Optional

from gnome_activities.core.manager import ActivityManager
from gnome_activities.core.tracker import AppTracker

logger = logging.getLogger(__name__)


class WindowMonitor:
    """Periodically monitors open windows and updates current activity state."""

    def __init__(self, manager: ActivityManager, interval: int = 5):
        self._manager = manager
        self._tracker = AppTracker()
        self._interval = interval
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=self._interval + 1)

    def _run(self) -> None:
        while self._running:
            self._poll()
            time.sleep(self._interval)

    def _poll(self) -> None:
        try:
            current = self._manager.get_current()
            if current:
                apps = self._tracker.snapshot_current_state()
                self._manager.update_app_state(current.name, apps)
        except Exception as e:
            logger.warning("Monitor poll error: %s", e)
