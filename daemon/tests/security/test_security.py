"""Security tests for input sanitization and injection prevention."""
import pytest
from unittest.mock import patch, MagicMock
from gnome_activities.app_launcher import _sanitize_path, _sanitize_app_id, launch_app, close_app


# --- _sanitize_path tests ---

def test_sanitize_path_blocks_semicolon():
    assert _sanitize_path("/home/user/file; rm -rf /") == ""


def test_sanitize_path_blocks_pipe():
    assert _sanitize_path("/home/user/file | cat /etc/passwd") == ""


def test_sanitize_path_blocks_ampersand():
    assert _sanitize_path("/home/user/file & evil") == ""


def test_sanitize_path_blocks_dollar():
    assert _sanitize_path("$HOME/.ssh/id_rsa") == ""


def test_sanitize_path_blocks_backtick():
    assert _sanitize_path("`id`") == ""


def test_sanitize_path_blocks_path_traversal():
    assert _sanitize_path("../../../etc/passwd") == ""


def test_sanitize_path_allows_valid_path():
    assert _sanitize_path("/home/user/documents/myfile.txt") == "/home/user/documents/myfile.txt"


def test_sanitize_path_allows_tilde_path():
    assert _sanitize_path("~/documents/file.md") == "~/documents/file.md"


def test_sanitize_path_allows_alphanumeric_with_spaces():
    assert _sanitize_path("/home/user/my file.txt") == "/home/user/my file.txt"


# --- _sanitize_app_id tests ---

def test_sanitize_app_id_blocks_semicolon():
    assert _sanitize_app_id("firefox;rm -rf /") == ""


def test_sanitize_app_id_blocks_pipe():
    assert _sanitize_app_id("firefox|cat") == ""


def test_sanitize_app_id_blocks_ampersand():
    assert _sanitize_app_id("firefox&evil") == ""


def test_sanitize_app_id_blocks_space():
    assert _sanitize_app_id("fire fox") == ""


def test_sanitize_app_id_allows_valid_app_id():
    assert _sanitize_app_id("org.gnome.gedit") == "org.gnome.gedit"


def test_sanitize_app_id_allows_dash_underscore():
    assert _sanitize_app_id("my-app_v2") == "my-app_v2"


# --- launch_app security tests ---

def test_launch_app_empty_exec_cmd_returns_false():
    assert launch_app("") is False
    assert launch_app("   ") is False


def test_launch_app_malicious_file_path_is_blocked():
    """Malicious file paths should be stripped out (sanitized to empty)."""
    with patch("gnome_activities.app_launcher.subprocess.Popen") as mock_popen:
        mock_popen.return_value = MagicMock()
        result = launch_app("gedit", files=["/safe/file.txt", "/etc/passwd; rm -rf /"])
        # The app should still launch but with only the safe file
        assert result is True
        call_args = mock_popen.call_args[0][0]
        assert "/safe/file.txt" in call_args
        assert "/etc/passwd; rm -rf /" not in call_args


def test_launch_app_file_not_found_returns_false():
    with patch("gnome_activities.app_launcher.subprocess.Popen", side_effect=FileNotFoundError("not found")):
        result = launch_app("nonexistent_binary_xyz")
        assert result is False


# --- close_app security tests ---

def test_close_app_empty_app_id_returns_false():
    assert close_app("") is False
    assert close_app("   ") is False


def test_close_app_malicious_app_id_returns_false():
    assert close_app("firefox; rm -rf /") is False


def test_close_app_with_pipe_returns_false():
    assert close_app("firefox | evil") is False


# --- Storage path traversal test ---

def test_storage_handles_special_chars_in_activity_name(tmp_path):
    """Activity names with special chars should be stored safely (no path traversal)."""
    from gnome_activities.storage import Storage
    from gnome_activities.models import Activity

    path = tmp_path / "state.json"
    storage = Storage(path)
    # Activity name with special chars - stored as JSON value, not used as filename
    activity = Activity(
        id="test",
        name="../../../etc/cron.d/evil",
        apps=[],
        is_active=False,
        created_at="2024-01-01T00:00:00+00:00",
    )
    storage.save([activity])
    # File should be written to the expected path, not a traversal path
    assert path.exists()
    evil_path = tmp_path.parent.parent.parent / "etc" / "cron.d" / "evil"
    assert not evil_path.exists()

    # Should load back correctly
    loaded = storage.load()
    assert loaded[0].name == "../../../etc/cron.d/evil"


def test_sanitize_path_blocks_path_traversal_variant():
    """Ensure ../../etc/passwd style paths are blocked."""
    assert _sanitize_path("../../etc/passwd") == ""
