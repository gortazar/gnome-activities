"""Unit tests for Activity and AppState models."""
import pytest
from gnome_activities.core.activity import Activity, AppState


def test_app_state_creation():
    state = AppState(app_id="gedit", command="gedit")
    assert state.app_id == "gedit"
    assert state.command == "gedit"
    assert state.files == []
    assert state.windows == 1


def test_app_state_with_files():
    state = AppState(app_id="gedit", command="gedit /tmp/foo.txt", files=["/tmp/foo.txt"])
    assert "/tmp/foo.txt" in state.files


def test_app_state_to_dict():
    state = AppState(app_id="gedit", command="gedit", files=["/tmp/f.txt"], windows=2)
    d = state.to_dict()
    assert d["app_id"] == "gedit"
    assert d["command"] == "gedit"
    assert d["files"] == ["/tmp/f.txt"]
    assert d["windows"] == 2


def test_app_state_from_dict():
    d = {"app_id": "gedit", "command": "gedit", "files": [], "windows": 1}
    state = AppState.from_dict(d)
    assert state.app_id == "gedit"


def test_app_state_roundtrip():
    state = AppState(app_id="firefox", command="firefox", files=["https://example.com"])
    assert AppState.from_dict(state.to_dict()) == state


def test_activity_creation():
    act = Activity(name="work")
    assert act.name == "work"
    assert act.description == ""
    assert act.apps == []
    assert act.is_active is False


def test_activity_to_dict():
    act = Activity(name="work", description="Work stuff", is_active=True)
    d = act.to_dict()
    assert d["name"] == "work"
    assert d["description"] == "Work stuff"
    assert d["is_active"] is True


def test_activity_from_dict():
    d = {
        "name": "play",
        "description": "Gaming",
        "apps": [],
        "created_at": "",
        "last_used": "",
        "is_active": False,
    }
    act = Activity.from_dict(d)
    assert act.name == "play"
    assert act.description == "Gaming"


def test_activity_roundtrip_with_apps():
    app = AppState(app_id="gedit", command="gedit")
    act = Activity(name="dev", apps=[app])
    restored = Activity.from_dict(act.to_dict())
    assert restored.name == "dev"
    assert len(restored.apps) == 1
    assert restored.apps[0].app_id == "gedit"
