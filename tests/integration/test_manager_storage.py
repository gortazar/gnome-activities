"""Integration tests for manager and storage working together."""

import pytest
from gnome_activities.core.manager import ActivityManager
from gnome_activities.core.activity import AppState


@pytest.fixture
def tmp_manager(tmp_path):
    return ActivityManager(config_dir=str(tmp_path))


def test_full_lifecycle(tmp_manager):
    act = tmp_manager.create("work", "Work task")
    assert act.name == "work"
    acts = tmp_manager.list_activities()
    assert len(acts) == 1
    tmp_manager.activate("work")
    assert tmp_manager.get_current().name == "work"
    tmp_manager.modify("work", description="Updated work task")
    act = tmp_manager.get("work")
    assert act.description == "Updated work task"
    tmp_manager.delete("work")
    assert len(tmp_manager.list_activities()) == 0


def test_multiple_activities_only_one_active(tmp_path):
    m = ActivityManager(config_dir=str(tmp_path))
    m.create("work")
    m.create("play")
    m.create("study")
    m.activate("work")
    m.activate("play")
    active = [a for a in m.list_activities() if a.is_active]
    assert len(active) == 1
    assert active[0].name == "play"


def test_app_state_persisted(tmp_path):
    m1 = ActivityManager(config_dir=str(tmp_path))
    m1.create("work")
    app = AppState(app_id="gedit", command="gedit", files=["/tmp/note.txt"])
    m1.update_app_state("work", [app])
    m2 = ActivityManager(config_dir=str(tmp_path))
    act = m2.get("work")
    assert len(act.apps) == 1
    assert act.apps[0].app_id == "gedit"
    assert "/tmp/note.txt" in act.apps[0].files


def test_always_available_persisted(tmp_path):
    m1 = ActivityManager(config_dir=str(tmp_path))
    m1.add_always_available_app("thunderbird")
    m2 = ActivityManager(config_dir=str(tmp_path))
    assert "thunderbird" in m2.get_always_available_apps()
