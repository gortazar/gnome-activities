# Architecture

## Overview

GNOME Activities consists of several components:

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│  ┌──────────────┐              ┌──────────────────────────┐ │
│  │  CLI (click)  │              │   Firefox Extension      │ │
│  └──────┬───────┘              └──────────┬───────────────┘ │
│         │                                 │ Native Messaging  │
│         ▼                                 ▼                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              D-Bus Service (daemon)                  │    │
│  │         org.gnome.Activities                         │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                         │                                    │
│  ┌──────────────────────▼──────────────────────────────┐    │
│  │                  Core Library                        │    │
│  │  ┌──────────┐  ┌─────────┐  ┌──────────┐           │    │
│  │  │ Manager  │  │ Tracker │  │ Launcher │           │    │
│  │  └────┬─────┘  └────┬────┘  └────┬─────┘           │    │
│  │       │             │            │                  │    │
│  │  ┌────▼─────────────▼────────────▼─────┐           │    │
│  │  │           Storage (JSON)             │           │    │
│  │  │   ~/.config/gnome-activities/        │           │    │
│  │  └──────────────────────────────────────┘           │    │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Components

### Core Library (`gnome_activities/core/`)

- **`activity.py`**: Data models (`Activity`, `AppState`) with serialization
- **`storage.py`**: Atomic JSON persistence with input validation
- **`manager.py`**: Business logic for CRUD operations on activities
- **`tracker.py`**: Reads open windows via `wmctrl` and open files via `/proc`
- **`launcher.py`**: Launches/closes apps using subprocess

### Daemon (`gnome_activities/daemon/`)

- **`service.py`**: D-Bus service exposing `org.gnome.Activities`
- **`monitor.py`**: Background thread polling window state every 5 seconds

### CLI (`gnome_activities/cli/`)

- **`main.py`**: Click-based CLI, communicates directly with the core library

### Firefox Extension (`firefox-extension/`)

- **`background.js`**: Monitors tab events, communicates via native messaging
- **`native/native_host.py`**: Bridges Firefox ↔ D-Bus daemon

## Data Flow

### Switching Activities

1. User runs `gnome-activities activate "Work"`
2. CLI calls `ActivityManager.activate("Work")`
3. Manager marks "Work" as active, updates `last_used`
4. Manager persists to `~/.config/gnome-activities/activities.json`
5. Launcher closes apps from previous activity (except always-available)
6. Launcher opens apps recorded in "Work" activity state
7. D-Bus signal `ActivityChanged` is emitted
8. Firefox extension receives signal, closes old tabs, opens Work tabs

### App State Tracking

1. `WindowMonitor` polls every 5 seconds
2. Calls `AppTracker.snapshot_current_state()`
3. Reads `wmctrl -lp` for PIDs and window titles
4. Reads `/proc/<pid>/comm` for app names
5. Reads `/proc/<pid>/fd` for open files
6. Updates current activity's `apps` list via `ActivityManager`
