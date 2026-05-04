"""Unit tests for ActivityManager."""
import pytest
from unittest.mock import MagicMock, patch, call
from gnome_activities.models import Activity, ActivityApp
from gnome_activities.storage import Storage
from gnome_activities.activity_manager import ActivityManager


def _make_storage(activities=None):
    storage = MagicMock(spec=Storage)
    storage.get_activities.return_value = activities if activities is not None else []
    storage.set_activities.return_value = None
    return storage


def _make_activity(name="Work", is_active=False, apps=None):
    return Activity(
        id=f"id-{name}",
        name=name,
        apps=apps or [],
        is_active=is_active,
        created_at="2024-01-01T00:00:00+00:00",
        last_used=None,
    )


def test_add_activity_creates_with_correct_name():
    storage = _make_storage([])
    manager = ActivityManager(storage)
    activity = manager.add_activity("Work")
    assert activity.name == "Work"
    storage.set_activities.assert_called_once()


def test_add_activity_raises_on_duplicate():
    storage = _make_storage([_make_activity("Work")])
    manager = ActivityManager(storage)
    with pytest.raises(ValueError, match="already exists"):
        manager.add_activity("Work")


def test_remove_activity_removes_correctly():
    storage = _make_storage([_make_activity("Work"), _make_activity("Personal")])
    manager = ActivityManager(storage)
    manager.remove_activity("Work")
    saved = storage.set_activities.call_args[0][0]
    assert len(saved) == 1
    assert saved[0].name == "Personal"


def test_remove_activity_raises_on_missing():
    storage = _make_storage([])
    manager = ActivityManager(storage)
    with pytest.raises(ValueError, match="not found"):
        manager.remove_activity("Nonexistent")


def test_rename_activity_works():
    storage = _make_storage([_make_activity("Work")])
    manager = ActivityManager(storage)
    activity = manager.rename_activity("Work", "NewWork")
    assert activity.name == "NewWork"


def test_rename_activity_raises_if_new_name_exists():
    storage = _make_storage([_make_activity("Work"), _make_activity("Personal")])
    manager = ActivityManager(storage)
    with pytest.raises(ValueError, match="already exists"):
        manager.rename_activity("Work", "Personal")


def test_get_active_activity_returns_none_when_none_active():
    storage = _make_storage([_make_activity("Work", is_active=False)])
    manager = ActivityManager(storage)
    assert manager.get_active_activity() is None


def test_get_active_activity_returns_active_activity():
    storage = _make_storage([_make_activity("Work", is_active=True)])
    manager = ActivityManager(storage)
    active = manager.get_active_activity()
    assert active is not None
    assert active.name == "Work"


def test_activate_activity_activates_target_and_deactivates_previous():
    previous = _make_activity("Work", is_active=True)
    target = _make_activity("Personal", is_active=False)
    storage = _make_storage([previous, target])

    with patch("gnome_activities.activity_manager.app_launcher") as mock_launcher:
        mock_launcher.close_app.return_value = True
        mock_launcher.launch_app.return_value = True
        manager = ActivityManager(storage)
        result = manager.activate_activity("Personal")

    assert result.name == "Personal"
    assert result.is_active is True
    assert previous.is_active is False


def test_activate_activity_closes_previous_non_global_apps():
    app1 = ActivityApp(app_id="firefox", exec_cmd="firefox", is_global=False)
    app2 = ActivityApp(app_id="gedit", exec_cmd="gedit", is_global=True)
    previous = _make_activity("Work", is_active=True, apps=[app1, app2])
    target = _make_activity("Personal")
    storage = _make_storage([previous, target])

    with patch("gnome_activities.activity_manager.app_launcher") as mock_launcher:
        mock_launcher.close_app.return_value = True
        mock_launcher.launch_app.return_value = True
        manager = ActivityManager(storage)
        manager.activate_activity("Personal")

    # Only non-global app should be closed
    mock_launcher.close_app.assert_called_once_with("firefox")


def test_activate_activity_does_not_close_global_apps():
    app = ActivityApp(app_id="spotify", exec_cmd="spotify", is_global=True)
    previous = _make_activity("Work", is_active=True, apps=[app])
    target = _make_activity("Personal")
    storage = _make_storage([previous, target])

    with patch("gnome_activities.activity_manager.app_launcher") as mock_launcher:
        mock_launcher.close_app.return_value = True
        mock_launcher.launch_app.return_value = True
        manager = ActivityManager(storage)
        manager.activate_activity("Personal")

    mock_launcher.close_app.assert_not_called()


def test_activate_activity_launches_new_activity_apps():
    app = ActivityApp(app_id="code", exec_cmd="code /home/user/project", files=[])
    previous = _make_activity("Work", is_active=True)
    target = _make_activity("Dev", apps=[app])
    storage = _make_storage([previous, target])

    with patch("gnome_activities.activity_manager.app_launcher") as mock_launcher:
        mock_launcher.close_app.return_value = True
        mock_launcher.launch_app.return_value = True
        manager = ActivityManager(storage)
        manager.activate_activity("Dev")

    mock_launcher.launch_app.assert_called_once_with("code /home/user/project", [])


def test_add_app_to_activity_adds_new_app():
    activity = _make_activity("Work")
    storage = _make_storage([activity])
    manager = ActivityManager(storage)
    app = manager.add_app_to_activity("Work", "firefox", "firefox")
    assert app.app_id == "firefox"
    assert app.exec_cmd == "firefox"


def test_add_app_to_activity_updates_existing_app():
    existing = ActivityApp(app_id="firefox", exec_cmd="firefox")
    activity = _make_activity("Work", apps=[existing])
    storage = _make_storage([activity])
    manager = ActivityManager(storage)

    updated = manager.add_app_to_activity("Work", "firefox", "firefox --private-window")
    assert updated.exec_cmd == "firefox --private-window"


def test_remove_app_from_activity_removes_correctly():
    app = ActivityApp(app_id="firefox", exec_cmd="firefox")
    activity = _make_activity("Work", apps=[app])
    storage = _make_storage([activity])
    manager = ActivityManager(storage)
    manager.remove_app_from_activity("Work", "firefox")
    saved = storage.set_activities.call_args[0][0]
    assert len(saved[0].apps) == 0


def test_set_app_global_changes_flag():
    app = ActivityApp(app_id="spotify", exec_cmd="spotify", is_global=False)
    activity = _make_activity("Work", apps=[app])
    storage = _make_storage([activity])
    manager = ActivityManager(storage)
    updated = manager.set_app_global("Work", "spotify", True)
    assert updated.is_global is True


def test_track_app_opened_adds_to_active_activity():
    active = _make_activity("Work", is_active=True)
    storage = _make_storage([active])
    manager = ActivityManager(storage)
    manager.track_app_opened("firefox", "firefox")
    saved = storage.set_activities.call_args[0][0]
    assert any(app.app_id == "firefox" for app in saved[0].apps)


def test_track_app_opened_does_nothing_when_no_active_activity():
    storage = _make_storage([_make_activity("Work", is_active=False)])
    manager = ActivityManager(storage)
    manager.track_app_opened("firefox", "firefox")
    storage.set_activities.assert_not_called()


def test_track_app_closed_removes_from_active_activity():
    app = ActivityApp(app_id="firefox", exec_cmd="firefox")
    active = _make_activity("Work", is_active=True, apps=[app])
    storage = _make_storage([active])
    manager = ActivityManager(storage)
    manager.track_app_closed("firefox")
    saved = storage.set_activities.call_args[0][0]
    assert len(saved[0].apps) == 0
