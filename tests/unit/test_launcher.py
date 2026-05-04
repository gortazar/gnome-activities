"""Unit tests for AppLauncher."""
import signal
import pytest
from unittest.mock import patch, MagicMock
from gnome_activities.core.launcher import AppLauncher
from gnome_activities.core.activity import AppState


@pytest.fixture
def launcher():
    return AppLauncher()


def test_launch_app_no_command(launcher):
    state = AppState(app_id="test", command="")
    result = launcher.launch_app(state)
    assert result is None


def test_launch_app_with_command(launcher):
    state = AppState(app_id="gedit", command="gedit")
    mock_proc = MagicMock()
    with patch("subprocess.Popen", return_value=mock_proc) as mock_popen:
        result = launcher.launch_app(state)
    assert result == mock_proc
    mock_popen.assert_called_once()


def test_launch_app_with_files(launcher):
    state = AppState(app_id="gedit", command="gedit", files=["/tmp/foo.txt"])
    mock_proc = MagicMock()
    with patch("subprocess.Popen", return_value=mock_proc) as mock_popen:
        launcher.launch_app(state)
    call_args = mock_popen.call_args[0][0]
    assert "/tmp/foo.txt" in call_args


def test_close_app_sends_sigterm(launcher):
    with patch("os.kill") as mock_kill:
        result = launcher.close_app(1234)
    assert result is True
    mock_kill.assert_called_once_with(1234, signal.SIGTERM)


def test_close_app_no_such_process(launcher):
    with patch("os.kill", side_effect=ProcessLookupError):
        result = launcher.close_app(9999)
    assert result is False


def test_close_all_except_no_wmctrl(launcher):
    with patch("subprocess.check_output", side_effect=FileNotFoundError):
        closed = launcher.close_all_except([])
    assert closed == []
