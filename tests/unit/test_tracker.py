"""Unit tests for AppTracker."""

import io
import pytest
from unittest.mock import patch
from gnome_activities.core.tracker import AppTracker


@pytest.fixture
def tracker():
    return AppTracker()


def test_get_app_command_from_proc(tracker):
    fake_cmdline = b"gedit\x00/tmp/foo.txt\x00"
    with patch("builtins.open", return_value=io.BytesIO(fake_cmdline)):
        cmd = tracker.get_app_command(12345)
    assert "gedit" in cmd


def test_get_open_windows_empty_when_no_wmctrl(tracker):
    with patch("subprocess.check_output", side_effect=FileNotFoundError):
        windows = tracker.get_open_windows()
    assert windows == []


def test_get_open_windows_parse_output(tracker):
    fake_output = "0x00000001  0 1234 hostname  Window Title\n"
    with patch("subprocess.check_output", return_value=fake_output):
        with patch.object(tracker, "_get_app_name", return_value="gedit"):
            with patch.object(tracker, "_get_wm_class", return_value="gedit"):
                windows = tracker.get_open_windows()
    assert len(windows) == 1
    assert windows[0] == (1234, "gedit", "gedit")


def test_get_open_files_no_permission(tracker):
    with patch("pathlib.Path.iterdir", side_effect=PermissionError):
        files = tracker.get_open_files(1)
    assert files == []


def test_snapshot_empty_no_wmctrl(tracker):
    with patch.object(tracker, "get_open_windows", return_value=[]):
        states = tracker.snapshot_current_state()
    assert states == []


def test_snapshot_with_windows(tracker):
    with patch.object(tracker, "get_open_windows", return_value=[(1234, "gedit", "gedit")]):
        with patch.object(tracker, "get_app_command", return_value="gedit /tmp/foo.txt"):
            with patch.object(tracker, "get_open_files", return_value=["/tmp/foo.txt"]):
                states = tracker.snapshot_current_state()
    assert len(states) == 1
    assert states[0].app_id == "gedit"
    assert "/tmp/foo.txt" in states[0].files
