"""JSON file storage for GNOME Activities state."""
import json
import logging
from pathlib import Path
from typing import Optional

from .models import Activity

logger = logging.getLogger(__name__)

DEFAULT_STATE_PATH = Path.home() / ".config" / "gnome-activities" / "state.json"


class Storage:
    """Persists activities to a JSON file."""

    def __init__(self, path: Optional[Path] = None):
        self.path = Path(path) if path else DEFAULT_STATE_PATH
        self._activities: Optional[list[Activity]] = None

    def load(self) -> list[Activity]:
        """Load activities from disk. Returns empty list if file doesn't exist or is corrupt."""
        if not self.path.exists():
            return []
        try:
            raw = self.path.read_text(encoding="utf-8")
            data = json.loads(raw)
            return [Activity.from_dict(d) for d in data]
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            logger.warning(f"Failed to parse state file {self.path}: {e}. Returning empty list.")
            return []

    def save(self, activities: list[Activity]) -> None:
        """Persist activities to disk, creating the directory if needed."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = [a.to_dict() for a in activities]
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get_activities(self) -> list[Activity]:
        """Return current activities, loading from disk if not cached."""
        if self._activities is None:
            self._activities = self.load()
        return self._activities

    def set_activities(self, activities: list[Activity]) -> None:
        """Update in-memory list and persist to disk."""
        self._activities = activities
        self.save(activities)
