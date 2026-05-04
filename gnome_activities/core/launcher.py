"""Application launcher for GNOME Activities."""
from __future__ import annotations
import os
import shlex
import signal
import subprocess
from typing import List, Optional

from gnome_activities.core.activity import AppState


class AppLauncher:
    """Launches and closes applications."""

    def launch_app(self, app_state: AppState) -> Optional[subprocess.Popen]:
        """Launch an application with its associated files."""
        if not app_state.command:
            return None
        try:
            cmd = app_state.command
            for f in app_state.files:
                if f not in cmd:
                    cmd = f"{cmd} {shlex.quote(f)}"
            args = shlex.split(cmd)
            proc = subprocess.Popen(args, start_new_session=True)
            return proc
        except (OSError, ValueError):
            return None

    def close_app(self, pid: int) -> bool:
        """Close an application gracefully (SIGTERM)."""
        try:
            os.kill(pid, signal.SIGTERM)
            return True
        except (OSError, ProcessLookupError):
            return False

    def close_all_except(self, always_available: List[str]) -> List[int]:
        """Close all open windows except always-available apps."""
        closed_pids = []
        try:
            output = subprocess.check_output(
                ["wmctrl", "-lp"], stderr=subprocess.DEVNULL, text=True
            )
            for line in output.splitlines():
                parts = line.split(None, 4)
                if len(parts) >= 3:
                    try:
                        pid = int(parts[2])
                        if pid <= 0:
                            continue
                        app_name = self._get_app_name(pid)
                        if app_name and app_name not in always_available:
                            if self.close_app(pid):
                                closed_pids.append(pid)
                    except (ValueError, IndexError):
                        continue
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return closed_pids

    def _get_app_name(self, pid: int) -> str:
        try:
            with open(f"/proc/{pid}/comm", "r") as f:
                return f.read().strip()
        except (OSError, IOError):
            return ""
