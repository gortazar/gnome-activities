"""Data models for GNOME Activities."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ActivityApp:
    """Represents an application associated with an activity."""
    app_id: str
    exec_cmd: str
    files: list[str] = field(default_factory=list)
    is_global: bool = False

    def to_dict(self) -> dict:
        return {
            "app_id": self.app_id,
            "exec_cmd": self.exec_cmd,
            "files": list(self.files),
            "is_global": self.is_global,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ActivityApp":
        return cls(
            app_id=data["app_id"],
            exec_cmd=data["exec_cmd"],
            files=list(data.get("files", [])),
            is_global=bool(data.get("is_global", False)),
        )


@dataclass
class Activity:
    """Represents a named activity context."""
    id: str
    name: str
    apps: list[ActivityApp] = field(default_factory=list)
    is_active: bool = False
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    last_used: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "apps": [app.to_dict() for app in self.apps],
            "is_active": self.is_active,
            "created_at": self.created_at,
            "last_used": self.last_used,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Activity":
        return cls(
            id=data["id"],
            name=data["name"],
            apps=[ActivityApp.from_dict(a) for a in data.get("apps", [])],
            is_active=bool(data.get("is_active", False)),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            last_used=data.get("last_used"),
        )

    def get_app(self, app_id: str) -> Optional[ActivityApp]:
        """Return the ActivityApp with the given app_id, or None if not found."""
        for app in self.apps:
            if app.app_id == app_id:
                return app
        return None
