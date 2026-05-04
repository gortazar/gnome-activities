"""Unit tests for storage module."""
import json
import pytest
from gnome_activities.core.activity import Activity, AppState
from gnome_activities.core import storage


@pytest.fixture
def tmp_config(tmp_path, monkeypatch):
    """Override storage paths to use tmp_path."""
    monkeypatch.setattr(storage, "CONFIG_DIR", tmp_path / "gnome-activities")
    monkeypatch.setattr(storage, "ACTIVITIES_FILE", storage.CONFIG_DIR / "activities.json")
    monkeypatch.setattr(storage, "CONFIG_FILE", storage.CONFIG_DIR / "config.json")
    return tmp_path


def test_load_activities_empty(tmp_config):
    acts = storage.load_activities()
    assert acts == {}


def test_save_and_load_activities(tmp_config):
    acts = {"work": Activity(name="work", description="Work")}
    storage.save_activities(acts)
    loaded = storage.load_activities()
    assert "work" in loaded
    assert loaded["work"].name == "work"
    assert loaded["work"].description == "Work"


def test_activities_file_created(tmp_config):
    acts = {"test": Activity(name="test")}
    storage.save_activities(acts)
    assert storage.ACTIVITIES_FILE.exists()


def test_config_dir_permissions(tmp_config):
    storage._ensure_config_dir()
    stat = storage.CONFIG_DIR.stat()
    assert oct(stat.st_mode)[-3:] == "700"


def test_load_config_default(tmp_config):
    cfg = storage.load_config()
    assert "always_available_apps" in cfg
    assert isinstance(cfg["always_available_apps"], list)


def test_save_and_load_config(tmp_config):
    cfg = {"always_available_apps": ["thunderbird"], "version": "1"}
    storage.save_config(cfg)
    loaded = storage.load_config()
    assert loaded["always_available_apps"] == ["thunderbird"]


def test_atomic_write(tmp_config):
    storage._ensure_config_dir()
    path = storage.CONFIG_DIR / "test.json"
    storage._atomic_write(path, {"key": "value"})
    assert path.exists()
    with open(path) as f:
        data = json.load(f)
    assert data["key"] == "value"


def test_load_activities_corrupted_json(tmp_config):
    storage._ensure_config_dir()
    storage.ACTIVITIES_FILE.write_text("not valid json {{{")
    acts = storage.load_activities()
    assert acts == {}


def test_validate_name_valid():
    assert storage.validate_name("work") == "work"
    assert storage.validate_name("My Work 2024") == "My Work 2024"
    assert storage.validate_name("dev-project_1") == "dev-project_1"


def test_validate_name_invalid():
    with pytest.raises(ValueError):
        storage.validate_name("")
    with pytest.raises(ValueError):
        storage.validate_name("a" * 65)
    with pytest.raises(ValueError):
        storage.validate_name("../etc/passwd")
    with pytest.raises(ValueError):
        storage.validate_name("hack;rm -rf /")


def test_roundtrip_with_apps(tmp_config):
    app = AppState(app_id="gedit", command="gedit", files=["/tmp/f.txt"])
    acts = {"dev": Activity(name="dev", apps=[app])}
    storage.save_activities(acts)
    loaded = storage.load_activities()
    assert loaded["dev"].apps[0].app_id == "gedit"
    assert loaded["dev"].apps[0].files == ["/tmp/f.txt"]
