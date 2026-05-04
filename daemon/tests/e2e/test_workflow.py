"""End-to-end workflow tests for gnome-activities."""
import pytest
from unittest.mock import patch
from gnome_activities.activity_manager import ActivityManager
from gnome_activities.models import ActivityApp
from gnome_activities.storage import Storage


def _make_manager(tmp_path):
    path = tmp_path / "state.json"
    return ActivityManager(Storage(path)), path


def test_full_workflow_create_add_activate_persist(tmp_path):
    """Create activity, add apps, activate, verify state persisted to disk."""
    manager, state_path = _make_manager(tmp_path)

    activity = manager.add_activity("Work")
    assert activity.name == "Work"

    with patch("gnome_activities.activity_manager.app_launcher") as mock_launcher:
        mock_launcher.launch_app.return_value = True
        mock_launcher.close_app.return_value = True
        manager.add_app_to_activity("Work", "firefox", "firefox")
        manager.add_app_to_activity("Work", "gedit", "gedit")
        manager.activate_activity("Work")

    # Load a fresh manager from the same file
    manager2 = ActivityManager(Storage(state_path))
    activities = manager2.list_activities()
    assert len(activities) == 1
    assert activities[0].name == "Work"
    assert activities[0].is_active is True
    assert len(activities[0].apps) == 2
    app_ids = [a.app_id for a in activities[0].apps]
    assert "firefox" in app_ids
    assert "gedit" in app_ids


def test_switching_between_activities_updates_state(tmp_path):
    """Test that switching between activities updates is_active flags correctly."""
    manager, state_path = _make_manager(tmp_path)
    manager.add_activity("Work")
    manager.add_activity("Personal")

    with patch("gnome_activities.activity_manager.app_launcher") as mock_launcher:
        mock_launcher.launch_app.return_value = True
        mock_launcher.close_app.return_value = True
        manager.activate_activity("Work")

    # Reload and verify Work is active
    manager2 = ActivityManager(Storage(state_path))
    assert manager2.get_active_activity().name == "Work"

    with patch("gnome_activities.activity_manager.app_launcher") as mock_launcher:
        mock_launcher.launch_app.return_value = True
        mock_launcher.close_app.return_value = True
        manager2.activate_activity("Personal")

    # Reload again and verify Personal is now active
    manager3 = ActivityManager(Storage(state_path))
    active = manager3.get_active_activity()
    assert active.name == "Personal"
    # Work should no longer be active
    activities = manager3.list_activities()
    work = next(a for a in activities if a.name == "Work")
    assert work.is_active is False


def test_global_app_not_closed_when_switching(tmp_path):
    """Global apps should not be closed when switching activities."""
    manager, _ = _make_manager(tmp_path)
    manager.add_activity("Work")
    manager.add_activity("Personal")

    # Add a global app and a non-global app to Work
    manager.add_app_to_activity("Work", "spotify", "spotify", is_global=True)
    manager.add_app_to_activity("Work", "firefox", "firefox", is_global=False)

    with patch("gnome_activities.activity_manager.app_launcher") as mock_launcher:
        mock_launcher.launch_app.return_value = True
        mock_launcher.close_app.return_value = True
        manager.activate_activity("Work")

    with patch("gnome_activities.activity_manager.app_launcher") as mock_launcher:
        mock_launcher.launch_app.return_value = True
        mock_launcher.close_app.return_value = True
        manager.activate_activity("Personal")
        # Spotify (global) should not be closed, firefox should be
        close_calls = [c[0][0] for c in mock_launcher.close_app.call_args_list]
        assert "spotify" not in close_calls
        assert "firefox" in close_calls


def test_track_app_opened_then_closed(tmp_path):
    """Tracking opens/closes updates the active activity."""
    manager, _ = _make_manager(tmp_path)
    manager.add_activity("Work")

    with patch("gnome_activities.activity_manager.app_launcher") as mock_launcher:
        mock_launcher.launch_app.return_value = True
        mock_launcher.close_app.return_value = True
        manager.activate_activity("Work")

    manager.track_app_opened("code", "code .")
    active = manager.get_active_activity()
    assert active.get_app("code") is not None

    manager.track_app_closed("code")
    active = manager.get_active_activity()
    assert active.get_app("code") is None
