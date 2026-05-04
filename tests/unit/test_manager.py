"""Unit tests for ActivityManager."""
import pytest
from gnome_activities.core.manager import ActivityManager, ActivityError


@pytest.fixture
def manager(tmp_path):
    return ActivityManager(config_dir=str(tmp_path))


def test_create_activity(manager):
    act = manager.create("work")
    assert act.name == "work"
    assert act.created_at != ""


def test_create_duplicate_raises(manager):
    manager.create("work")
    with pytest.raises(ActivityError):
        manager.create("work")


def test_create_invalid_name_raises(manager):
    with pytest.raises(ValueError):
        manager.create("../bad")


def test_delete_activity(manager):
    manager.create("work")
    manager.delete("work")
    assert not any(a.name == "work" for a in manager.list_activities())


def test_delete_nonexistent_raises(manager):
    with pytest.raises(ActivityError):
        manager.delete("nonexistent")


def test_list_activities(manager):
    manager.create("work")
    manager.create("play")
    acts = manager.list_activities()
    names = [a.name for a in acts]
    assert "work" in names
    assert "play" in names


def test_activate_activity(manager):
    manager.create("work")
    manager.create("play")
    manager.activate("work")
    assert manager.get_current().name == "work"
    manager.activate("play")
    assert manager.get_current().name == "play"
    work = manager.get("work")
    assert not work.is_active


def test_activate_nonexistent_raises(manager):
    with pytest.raises(ActivityError):
        manager.activate("nonexistent")


def test_get_current_none_initially(manager):
    assert manager.get_current() is None


def test_modify_description(manager):
    manager.create("work", "old desc")
    act = manager.modify("work", description="new desc")
    assert act.description == "new desc"


def test_modify_nonexistent_raises(manager):
    with pytest.raises(ActivityError):
        manager.modify("nonexistent", description="x")


def test_always_available_apps(manager):
    manager.add_always_available_app("thunderbird")
    assert "thunderbird" in manager.get_always_available_apps()
    manager.remove_always_available_app("thunderbird")
    assert "thunderbird" not in manager.get_always_available_apps()


def test_always_available_no_duplicates(manager):
    manager.add_always_available_app("thunderbird")
    manager.add_always_available_app("thunderbird")
    assert manager.get_always_available_apps().count("thunderbird") == 1


def test_persistence(tmp_path):
    m1 = ActivityManager(config_dir=str(tmp_path))
    m1.create("work", "Work stuff")
    m2 = ActivityManager(config_dir=str(tmp_path))
    acts = m2.list_activities()
    assert any(a.name == "work" for a in acts)


def test_activate_sets_last_used(manager):
    manager.create("work")
    manager.activate("work")
    act = manager.get("work")
    assert act.last_used != ""
