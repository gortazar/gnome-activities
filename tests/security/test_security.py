"""Security tests for GNOME Activities Manager."""

import pytest
import gnome_activities.core.storage as storage
from gnome_activities.core.activity import Activity
from gnome_activities.core.manager import ActivityManager


def test_path_traversal_in_activity_name():
    with pytest.raises(ValueError):
        storage.validate_name("../../../etc/passwd")
    with pytest.raises(ValueError):
        storage.validate_name("../../root/.ssh/authorized_keys")


def test_shell_injection_in_activity_name():
    with pytest.raises(ValueError):
        storage.validate_name("work; rm -rf /")
    with pytest.raises(ValueError):
        storage.validate_name("work$(evil)")
    with pytest.raises(ValueError):
        storage.validate_name("work`evil`")


def test_config_dir_permissions(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "CONFIG_DIR", tmp_path / "gnome-activities")
    monkeypatch.setattr(storage, "ACTIVITIES_FILE", storage.CONFIG_DIR / "activities.json")
    monkeypatch.setattr(storage, "CONFIG_FILE", storage.CONFIG_DIR / "config.json")
    storage._ensure_config_dir()
    mode = oct(storage.CONFIG_DIR.stat().st_mode)[-3:]
    assert mode == "700", f"Expected 700, got {mode}"


def test_no_code_injection_in_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "CONFIG_DIR", tmp_path / "gnome-activities")
    monkeypatch.setattr(storage, "ACTIVITIES_FILE", storage.CONFIG_DIR / "activities.json")
    monkeypatch.setattr(storage, "CONFIG_FILE", storage.CONFIG_DIR / "config.json")
    act = Activity(name="test", description='"; import os; os.system("rm -rf /"); "')
    storage.save_activities({"test": act})
    loaded = storage.load_activities()
    assert loaded["test"].description == '"; import os; os.system("rm -rf /"); "'


def test_activity_name_max_length():
    with pytest.raises(ValueError):
        storage.validate_name("a" * 65)
    storage.validate_name("a" * 64)


def test_manager_rejects_path_traversal(tmp_path):
    m = ActivityManager(config_dir=str(tmp_path))
    with pytest.raises(ValueError):
        m.create("../../evil")
    with pytest.raises(ValueError):
        m.delete("../../evil")
    with pytest.raises(ValueError):
        m.activate("../../evil")
    with pytest.raises(ValueError):
        m.modify("../../evil")


def test_atomic_write_no_partial_files(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "CONFIG_DIR", tmp_path / "gnome-activities")
    monkeypatch.setattr(storage, "ACTIVITIES_FILE", storage.CONFIG_DIR / "activities.json")
    storage._ensure_config_dir()
    storage._atomic_write(storage.ACTIVITIES_FILE, {"test": "value"})
    temp_files = list(storage.CONFIG_DIR.glob(".tmp_*"))
    assert len(temp_files) == 0
