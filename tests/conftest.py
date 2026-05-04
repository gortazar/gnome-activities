"""Shared pytest fixtures."""
import pytest
import gnome_activities.core.storage as storage


@pytest.fixture(autouse=False)
def isolated_storage(tmp_path, monkeypatch):
    """Isolate storage to a temporary directory."""
    monkeypatch.setattr(storage, "CONFIG_DIR", tmp_path / "gnome-activities")
    monkeypatch.setattr(storage, "ACTIVITIES_FILE", storage.CONFIG_DIR / "activities.json")
    monkeypatch.setattr(storage, "CONFIG_FILE", storage.CONFIG_DIR / "config.json")
    return tmp_path
