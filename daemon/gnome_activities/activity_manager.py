"""Core activity manager."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from .models import Activity, ActivityApp
from .storage import Storage
from . import app_launcher

logger = logging.getLogger(__name__)


class ActivityManager:
    def __init__(self, storage: Storage = None):
        self.storage = storage or Storage()

    def list_activities(self) -> list[Activity]:
        return self.storage.get_activities()

    def add_activity(self, name: str) -> Activity:
        """Add a new activity. Raises ValueError if name already exists."""
        activities = self.storage.get_activities()
        if any(a.name == name for a in activities):
            raise ValueError(f"Activity '{name}' already exists")
        activity = Activity(
            id=str(uuid.uuid4()),
            name=name,
            apps=[],
            is_active=False,
            created_at=datetime.now(timezone.utc).isoformat(),
            last_used=None,
        )
        activities.append(activity)
        self.storage.set_activities(activities)
        return activity

    def remove_activity(self, name: str) -> None:
        """Remove an activity by name. Raises ValueError if not found."""
        activities = self.storage.get_activities()
        for i, a in enumerate(activities):
            if a.name == name:
                activities.pop(i)
                self.storage.set_activities(activities)
                return
        raise ValueError(f"Activity '{name}' not found")

    def rename_activity(self, old_name: str, new_name: str) -> Activity:
        activities = self.storage.get_activities()
        if any(a.name == new_name for a in activities):
            raise ValueError(f"Activity '{new_name}' already exists")
        for a in activities:
            if a.name == old_name:
                a.name = new_name
                self.storage.set_activities(activities)
                return a
        raise ValueError(f"Activity '{old_name}' not found")

    def get_active_activity(self) -> Optional[Activity]:
        for a in self.storage.get_activities():
            if a.is_active:
                return a
        return None

    def activate_activity(self, name: str) -> Activity:
        """Activate an activity: close previous non-global apps, open new activity's apps."""
        activities = self.storage.get_activities()

        target = None
        previous = None
        for a in activities:
            if a.name == name:
                target = a
            if a.is_active:
                previous = a

        if target is None:
            raise ValueError(f"Activity '{name}' not found")

        if target.is_active:
            return target

        # Close previous activity's non-global apps
        if previous:
            for app in previous.apps:
                if not app.is_global:
                    app_launcher.close_app(app.app_id)
            previous.is_active = False

        # Launch new activity's apps
        for app in target.apps:
            app_launcher.launch_app(app.exec_cmd, app.files)

        target.is_active = True
        target.last_used = datetime.now(timezone.utc).isoformat()
        self.storage.set_activities(activities)
        return target

    def add_app_to_activity(
        self,
        activity_name: str,
        app_id: str,
        exec_cmd: str,
        files: list[str] = None,
        is_global: bool = False,
    ) -> ActivityApp:
        activities = self.storage.get_activities()
        for a in activities:
            if a.name == activity_name:
                # Update if exists
                for existing in a.apps:
                    if existing.app_id == app_id:
                        existing.exec_cmd = exec_cmd
                        existing.files = files or []
                        existing.is_global = is_global
                        self.storage.set_activities(activities)
                        return existing
                new_app = ActivityApp(
                    app_id=app_id,
                    exec_cmd=exec_cmd,
                    files=files or [],
                    is_global=is_global,
                )
                a.apps.append(new_app)
                self.storage.set_activities(activities)
                return new_app
        raise ValueError(f"Activity '{activity_name}' not found")

    def remove_app_from_activity(self, activity_name: str, app_id: str) -> None:
        activities = self.storage.get_activities()
        for a in activities:
            if a.name == activity_name:
                original_len = len(a.apps)
                a.apps = [app for app in a.apps if app.app_id != app_id]
                if len(a.apps) == original_len:
                    raise ValueError(f"App '{app_id}' not found in activity '{activity_name}'")
                self.storage.set_activities(activities)
                return
        raise ValueError(f"Activity '{activity_name}' not found")

    def set_app_global(self, activity_name: str, app_id: str, is_global: bool) -> ActivityApp:
        activities = self.storage.get_activities()
        for a in activities:
            if a.name == activity_name:
                for app in a.apps:
                    if app.app_id == app_id:
                        app.is_global = is_global
                        self.storage.set_activities(activities)
                        return app
                raise ValueError(f"App '{app_id}' not found in activity '{activity_name}'")
        raise ValueError(f"Activity '{activity_name}' not found")

    def track_app_opened(self, app_id: str, exec_cmd: str, files: list[str] = None) -> None:
        """Track that an app was opened; adds/updates it in the active activity."""
        active = self.get_active_activity()
        if not active:
            logger.debug("No active activity; ignoring track_app_opened")
            return
        self.add_app_to_activity(active.name, app_id, exec_cmd, files or [])

    def track_app_closed(self, app_id: str) -> None:
        """Track that an app was closed; removes it from the active activity."""
        active = self.get_active_activity()
        if not active:
            return
        try:
            self.remove_app_from_activity(active.name, app_id)
        except ValueError:
            pass  # App not tracked, ignore
