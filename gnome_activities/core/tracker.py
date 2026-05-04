"""Application and window tracker for GNOME Activities."""
from __future__ import annotations
import os
import subprocess
from pathlib import Path
from typing import List, Tuple

from gnome_activities.core.activity import AppState


class AppTracker:
    """Tracks open applications and their associated files."""

    def get_open_windows(self) -> List[Tuple[int, str, str]]:
        """Return list of (pid, app_name, wm_class) for open windows."""
        windows = []
        try:
            output = subprocess.check_output(
                ["wmctrl", "-lp"], stderr=subprocess.DEVNULL, text=True
            )
            pids_seen = set()
            for line in output.splitlines():
                parts = line.split(None, 4)
                if len(parts) >= 3:
                    try:
                        pid = int(parts[2])
                        if pid > 0 and pid not in pids_seen:
                            pids_seen.add(pid)
                            app_name = self._get_app_name(pid)
                            wm_class = self._get_wm_class(pid)
                            windows.append((pid, app_name, wm_class))
                    except (ValueError, IndexError):
                        continue
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return windows

    def get_app_command(self, pid: int) -> str:
        """Get the launch command for a process."""
        try:
            cmdline_path = f"/proc/{pid}/cmdline"
            with open(cmdline_path, "rb") as f:
                data = f.read()
            args = data.split(b"\x00")
            return " ".join(a.decode("utf-8", errors="replace") for a in args if a)
        except (OSError, IOError):
            return ""

    def _get_app_name(self, pid: int) -> str:
        """Get application name from /proc."""
        try:
            with open(f"/proc/{pid}/comm", "r") as f:
                return f.read().strip()
        except (OSError, IOError):
            return ""

    def _get_wm_class(self, pid: int) -> str:
        """Get WM class hint for a process."""
        return self._get_app_name(pid)

    def get_open_files(self, pid: int) -> List[str]:
        """Get list of regular files open by a process."""
        files = []
        try:
            fd_dir = Path(f"/proc/{pid}/fd")
            for fd_entry in fd_dir.iterdir():
                try:
                    target = os.readlink(str(fd_entry))
                    if target.startswith("/") and os.path.isfile(target):
                        if not target.startswith(("/proc", "/dev", "/sys", "/run")):
                            files.append(target)
                except (OSError, IOError):
                    continue
        except (OSError, IOError, PermissionError):
            pass
        return list(set(files))

    def snapshot_current_state(self) -> List[AppState]:
        """Snapshot all open windows and their files."""
        states = []
        seen_apps = {}
        for pid, app_name, wm_class in self.get_open_windows():
            if not app_name:
                continue
            command = self.get_app_command(pid)
            files = self.get_open_files(pid)
            key = app_name or wm_class
            if key in seen_apps:
                seen_apps[key].files.extend(files)
                seen_apps[key].windows += 1
            else:
                state = AppState(
                    app_id=key,
                    command=command,
                    files=files,
                    windows=1,
                )
                seen_apps[key] = state
                states.append(state)
        return states
