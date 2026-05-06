"""Unit tests for Activity and ActivityApp models."""

import pytest
from gnome_activities.models import Activity, ActivityApp


def test_create_activity_app_with_defaults():
    app = ActivityApp(app_id="firefox", exec_cmd="firefox")
    assert app.app_id == "firefox"
    assert app.exec_cmd == "firefox"
    assert app.files == []
    assert app.is_global is False


def test_activity_app_to_dict_and_from_dict():
    app = ActivityApp(app_id="firefox", exec_cmd="firefox", files=["/home/user/doc.txt"], is_global=True)
    d = app.to_dict()
    assert d["app_id"] == "firefox"
    assert d["exec_cmd"] == "firefox"
    assert d["files"] == ["/home/user/doc.txt"]
    assert d["is_global"] is True

    restored = ActivityApp.from_dict(d)
    assert restored.app_id == app.app_id
    assert restored.exec_cmd == app.exec_cmd
    assert restored.files == app.files
    assert restored.is_global == app.is_global


def test_activity_app_from_dict_defaults():
    app = ActivityApp.from_dict({"app_id": "gedit", "exec_cmd": "gedit"})
    assert app.files == []
    assert app.is_global is False


def test_activity_to_dict_and_from_dict():
    activity = Activity(
        id="abc-123",
        name="Work",
        apps=[ActivityApp(app_id="firefox", exec_cmd="firefox")],
        is_active=True,
        created_at="2024-01-01T00:00:00+00:00",
        last_used="2024-01-02T00:00:00+00:00",
    )
    d = activity.to_dict()
    assert d["id"] == "abc-123"
    assert d["name"] == "Work"
    assert len(d["apps"]) == 1
    assert d["is_active"] is True
    assert d["created_at"] == "2024-01-01T00:00:00+00:00"
    assert d["last_used"] == "2024-01-02T00:00:00+00:00"

    restored = Activity.from_dict(d)
    assert restored.id == activity.id
    assert restored.name == activity.name
    assert len(restored.apps) == 1
    assert restored.apps[0].app_id == "firefox"
    assert restored.is_active is True
    assert restored.last_used == "2024-01-02T00:00:00+00:00"


def test_activity_get_app_finds_correct_app():
    app1 = ActivityApp(app_id="firefox", exec_cmd="firefox")
    app2 = ActivityApp(app_id="gedit", exec_cmd="gedit")
    activity = Activity(id="x", name="Work", apps=[app1, app2])

    found = activity.get_app("gedit")
    assert found is app2


def test_activity_get_app_returns_none_when_not_found():
    activity = Activity(id="x", name="Work", apps=[])
    assert activity.get_app("nonexistent") is None


def test_activity_defaults():
    activity = Activity(id="y", name="Personal")
    assert activity.apps == []
    assert activity.is_active is False
    assert activity.last_used is None
    assert activity.created_at is not None
