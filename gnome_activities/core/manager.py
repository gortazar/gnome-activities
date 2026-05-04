"""Activity manager - core business logic."""
from __future__ import annotations
import datetime
from typing import Dict, List, Optional

from gnome_activities.core.activity import Activity, AppState
from gnome_activities.core import storage


class ActivityError(Exception):
    pass


class ActivityManager:
    def __init__(self, config_dir: Optional[str] = None):
        if config_dir:
            import pathlib
            storage.CONFIG_DIR = pathlib.Path(config_dir)
            storage.ACTIVITIES_FILE = storage.CONFIG_DIR / "activities.json"
            storage.CONFIG_FILE = storage.CONFIG_DIR / "config.json"
        self._activities: Dict[str, Activity] = storage.load_activities()
        self._config = storage.load_config()

    def _save(self) -> None:
        storage.save_activities(self._activities)

    def _save_config(self) -> None:
        storage.save_config(self._config)

    def list_activities(self) -> List[Activity]:
        return list(self._activities.values())

    def get(self, name: str) -> Activity:
        storage.validate_name(name)
        if name not in self._activities:
            raise ActivityError(f"Activity '{name}' not found.")
        return self._activities[name]

    def create(self, name: str, description: str = "") -> Activity:
        storage.validate_name(name)
        if name in self._activities:
            raise ActivityError(f"Activity '{name}' already exists.")
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        activity = Activity(name=name, description=description, created_at=now)
        self._activities[name] = activity
        self._save()
        return activity

    def delete(self, name: str) -> None:
        storage.validate_name(name)
        if name not in self._activities:
            raise ActivityError(f"Activity '{name}' not found.")
        del self._activities[name]
        self._save()

    def modify(self, name: str, description: Optional[str] = None) -> Activity:
        storage.validate_name(name)
        if name not in self._activities:
            raise ActivityError(f"Activity '{name}' not found.")
        activity = self._activities[name]
        if description is not None:
            activity.description = description
        self._save()
        return activity

    def activate(self, name: str) -> Activity:
        storage.validate_name(name)
        if name not in self._activities:
            raise ActivityError(f"Activity '{name}' not found.")
        for act in self._activities.values():
            act.is_active = False
        activity = self._activities[name]
        activity.is_active = True
        activity.last_used = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self._save()
        return activity

    def get_current(self) -> Optional[Activity]:
        for act in self._activities.values():
            if act.is_active:
                return act
        return None

    def update_app_state(self, name: str, apps: List[AppState]) -> None:
        storage.validate_name(name)
        if name not in self._activities:
            raise ActivityError(f"Activity '{name}' not found.")
        self._activities[name].apps = apps
        self._save()

    def add_always_available_app(self, app_id: str) -> None:
        apps = self._config.setdefault("always_available_apps", [])
        if app_id not in apps:
            apps.append(app_id)
            self._save_config()

    def remove_always_available_app(self, app_id: str) -> None:
        apps = self._config.get("always_available_apps", [])
        if app_id in apps:
            apps.remove(app_id)
            self._save_config()

    def get_always_available_apps(self) -> List[str]:
        return list(self._config.get("always_available_apps", []))
