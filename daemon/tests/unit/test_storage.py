"""Unit tests for Storage."""

import json
import pytest
from gnome_activities.models import Activity, ActivityApp
from gnome_activities.storage import Storage


def _make_activity(name="Work") -> Activity:
    return Activity(
        id="test-id-1",
        name=name,
        apps=[],
        is_active=False,
        created_at="2024-01-01T00:00:00+00:00",
        last_used=None,
    )


def test_save_and_load_round_trip(tmp_path):
    path = tmp_path / "state.json"
    storage = Storage(path)
    activity = _make_activity("Work")
    storage.save([activity])

    storage2 = Storage(path)
    activities = storage2.load()
    assert len(activities) == 1
    assert activities[0].name == "Work"
    assert activities[0].id == "test-id-1"


def test_load_returns_empty_list_when_file_not_exists(tmp_path):
    path = tmp_path / "nonexistent.json"
    storage = Storage(path)
    assert storage.load() == []


def test_load_handles_corrupt_json(tmp_path):
    path = tmp_path / "state.json"
    path.write_text("this is not valid json{{{{", encoding="utf-8")
    storage = Storage(path)
    result = storage.load()
    assert result == []


def test_directory_created_if_missing(tmp_path):
    path = tmp_path / "deep" / "nested" / "state.json"
    storage = Storage(path)
    storage.save([_make_activity()])
    assert path.exists()


def test_set_activities_and_get_activities_consistency(tmp_path):
    path = tmp_path / "state.json"
    storage = Storage(path)
    a1 = _make_activity("Work")
    a2 = _make_activity("Personal")
    a2.id = "test-id-2"
    storage.set_activities([a1, a2])

    activities = storage.get_activities()
    assert len(activities) == 2
    names = [a.name for a in activities]
    assert "Work" in names
    assert "Personal" in names


def test_get_activities_caches_after_first_load(tmp_path):
    path = tmp_path / "state.json"
    storage = Storage(path)
    activity = _make_activity()
    storage.save([activity])

    # First call loads from disk
    acts1 = storage.get_activities()
    # Second call should return the same cached list
    acts2 = storage.get_activities()
    assert acts1 is acts2


def test_save_persists_apps(tmp_path):
    path = tmp_path / "state.json"
    storage = Storage(path)
    activity = _make_activity()
    activity.apps = [ActivityApp(app_id="firefox", exec_cmd="firefox", files=[], is_global=False)]
    storage.save([activity])

    storage2 = Storage(path)
    acts = storage2.load()
    assert len(acts[0].apps) == 1
    assert acts[0].apps[0].app_id == "firefox"
