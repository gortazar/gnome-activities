"""Activity data models for GNOME Activities Manager."""
from __future__ import annotations
import dataclasses
from typing import List


@dataclasses.dataclass
class AppState:
    """State of an application within an activity."""
    app_id: str
    command: str
    files: List[str] = dataclasses.field(default_factory=list)
    windows: int = 1

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AppState":
        return cls(
            app_id=data["app_id"],
            command=data["command"],
            files=data.get("files", []),
            windows=data.get("windows", 1),
        )


@dataclasses.dataclass
class Activity:
    """An activity/task with associated application states."""
    name: str
    description: str = ""
    apps: List[AppState] = dataclasses.field(default_factory=list)
    tabs: List[str] = dataclasses.field(default_factory=list)
    created_at: str = ""
    last_used: str = ""
    is_active: bool = False

    def to_dict(self) -> dict:
        d = dataclasses.asdict(self)
        d["apps"] = [app.to_dict() for app in self.apps]
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Activity":
        apps = [AppState.from_dict(a) for a in data.get("apps", [])]
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            apps=apps,
            tabs=data.get("tabs", []),
            created_at=data.get("created_at", ""),
            last_used=data.get("last_used", ""),
            is_active=data.get("is_active", False),
        )
