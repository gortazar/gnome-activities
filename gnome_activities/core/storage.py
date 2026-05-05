"""Persistent storage for GNOME Activities Manager."""

from __future__ import annotations
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Dict, Any

from gnome_activities.core.activity import Activity

CONFIG_DIR = Path.home() / ".config" / "gnome-activities"
ACTIVITIES_FILE = CONFIG_DIR / "activities.json"
CONFIG_FILE = CONFIG_DIR / "config.json"

_VALID_NAME = re.compile(r"^[a-zA-Z0-9_\- ]{1,64}$")


def _ensure_config_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.chmod(0o700)


def validate_name(name: str) -> str:
    """Validate and return name, raising ValueError if invalid."""
    if not _VALID_NAME.match(name):
        raise ValueError(
            f"Invalid activity name '{name}'. "
            "Names must be 1-64 chars: letters, digits, spaces, hyphens, underscores."
        )
    return name


def _atomic_write(path: Path, data: Any) -> None:
    """Write JSON data atomically using a temp file and rename."""
    _ensure_config_dir()
    tmp_fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp_")
    try:
        with os.fdopen(tmp_fd, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, str(path))
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def load_activities() -> Dict[str, Activity]:
    """Load all activities from disk."""
    if not ACTIVITIES_FILE.exists():
        return {}
    try:
        with open(ACTIVITIES_FILE, "r") as f:
            raw = json.load(f)
        return {name: Activity.from_dict(data) for name, data in raw.items()}
    except (json.JSONDecodeError, KeyError, TypeError):
        return {}


def save_activities(activities: Dict[str, Activity]) -> None:
    """Save all activities to disk."""
    data = {name: act.to_dict() for name, act in activities.items()}
    _atomic_write(ACTIVITIES_FILE, data)


def load_config() -> Dict[str, Any]:
    """Load global configuration."""
    if not CONFIG_FILE.exists():
        return {"always_available_apps": [], "version": "1"}
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, TypeError):
        return {"always_available_apps": [], "version": "1"}


def save_config(config: Dict[str, Any]) -> None:
    """Save global configuration."""
    _atomic_write(CONFIG_FILE, config)
