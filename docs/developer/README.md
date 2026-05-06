# GNOME Activities — Developer Guide

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     User Interfaces                     │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  GNOME Shell │  │  Firefox Ext │  │    CLI       │  │
│  │  Extension   │  │  (WebExt)    │  │ (click-based)│  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │ D-Bus            │ Native Msg       │ Direct   │
└─────────┼──────────────────┼──────────────────┼─────────┘
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼─────────┐
│                    Python Daemon                         │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  dbus_service│  │activity_mgr  │  │ app_launcher │  │
│  │  (D-Bus API) │  │  (core logic)│  │ (subprocess) │  │
│  └──────────────┘  └──────┬───────┘  └──────────────┘  │
│                            │                            │
│                    ┌───────▼───────┐                    │
│                    │   storage.py  │                    │
│                    │  (JSON file)  │                    │
│                    └───────────────┘                    │
└─────────────────────────────────────────────────────────┘
```

**Components:**

| Component | Path | Purpose |
|-----------|------|---------|
| Core daemon | `daemon/gnome_activities/` | Python package |
| CLI | `daemon/gnome_activities/cli.py` | Click-based CLI |
| Activity Manager | `daemon/gnome_activities/activity_manager.py` | Core logic |
| Storage | `daemon/gnome_activities/storage.py` | JSON persistence |
| App Launcher | `daemon/gnome_activities/app_launcher.py` | Launch/close apps |
| D-Bus Service | `daemon/gnome_activities/dbus_service.py` | IPC interface |
| Models | `daemon/gnome_activities/models.py` | Data classes |
| GNOME Extension | `gnome-extension/` | Shell panel indicator |
| Firefox Extension | `firefox-extension/` | Tab tracking |
| Native Messaging | `firefox-extension/native-messaging/` | Browser bridge |

---

## Prerequisites

- Python 3.10+
- `python3-dbus` (for D-Bus service)
- `wmctrl` or `pkill` (for closing apps)
- GNOME Shell 45+ (for the extension)
- Firefox 109+ (for the browser extension)

---

## Development Setup

```bash
# Clone the repo
git clone https://github.com/gortazar/gnome-activities.git
cd gnome-activities

# Install in editable mode with dev dependencies
make install
# or manually:
cd daemon && pip install -e ".[dev]"
```

---

## Running Tests

```bash
make test
# or
cd daemon && pytest tests/ -v
```

Run a specific test file:

```bash
cd daemon && pytest tests/unit/test_models.py -v
```

Run with coverage:

```bash
cd daemon && pytest tests/ --cov=gnome_activities --cov-report=html
```

---

## Linting

```bash
make lint
# or
cd daemon && flake8 gnome_activities/ --max-line-length=120
```

---

## Security Scanning

```bash
make security
# or
cd daemon && bandit -r gnome_activities/ -ll
```

---

## Building the .deb Package

```bash
make build-deb
# or
bash packaging/build-deb.sh
```

Requires `debhelper` to be installed:

```bash
sudo apt-get install debhelper
```

---

## Key Files and Purpose

### `daemon/gnome_activities/models.py`

Defines `Activity` and `ActivityApp` dataclasses with `to_dict()` / `from_dict()` for JSON
serialization.

### `daemon/gnome_activities/storage.py`

Reads and writes `~/.config/gnome-activities/state.json`. Uses an in-memory cache after first
load. Handles corrupt JSON gracefully by returning an empty list.

### `daemon/gnome_activities/activity_manager.py`

Core business logic:
- `add_activity(name)` — create new activity (raises `ValueError` on duplicates)
- `activate_activity(name)` — switch to activity (closes non-global apps of previous, opens apps of target)
- `add_app_to_activity(...)` — upsert an app into an activity
- `track_app_opened/closed(...)` — auto-track apps in the current activity

### `daemon/gnome_activities/app_launcher.py`

Wraps `subprocess.Popen` (for launching) and `wmctrl`/`pkill` (for closing). All inputs are
sanitized with `_sanitize_path` and `_sanitize_app_id` to prevent injection.

### `daemon/gnome_activities/dbus_service.py`

Exposes `ActivityManager` over D-Bus at `org.gnome.Activities`. Requires `dbus-python` and
`python-gi`. Emits `ActivityChanged(name)` signal.

---

## D-Bus Interface

**Bus name:** `org.gnome.Activities`  
**Object path:** `/org/gnome/Activities`  
**Interface:** `org.gnome.Activities`

| Method | Signature | Description |
|--------|-----------|-------------|
| `ListActivities` | `() → s` | Returns JSON array of activity dicts |
| `AddActivity` | `(s) → s` | Add activity by name, returns JSON dict |
| `RemoveActivity` | `(s) → ` | Remove activity by name |
| `RenameActivity` | `(ss) → s` | Rename activity, returns updated dict |
| `ActivateActivity` | `(s) → s` | Activate activity, returns dict |
| `GetActiveActivity` | `() → s` | Returns active activity JSON or `"null"` |
| `AddAppToActivity` | `(sssasb) → s` | Add/update app, returns app dict |
| `RemoveAppFromActivity` | `(ss) → ` | Remove app from activity |
| `SetAppGlobal` | `(ssb) → s` | Set is_global flag on app |
| `TrackAppOpened` | `(ssas) → ` | Track app opened in active activity |
| `TrackAppClosed` | `(s) → ` | Track app closed in active activity |

**Signal:**

| Signal | Signature | Description |
|--------|-----------|-------------|
| `ActivityChanged` | `(s)` | Emitted when active activity changes |

---

## How to Contribute

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes with tests
4. Ensure tests pass: `make test`
5. Ensure linting passes: `make lint`
6. Open a pull request

### Commit message format

```
type: short description

Longer explanation if needed.

Co-authored-by: Name <email>
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`
