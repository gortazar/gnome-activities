# Usage

## Basic Commands

### List activities
```bash
gnome-activities list
```

### Create an activity
```bash
gnome-activities create "Work" --description "Daily work tasks"
gnome-activities create "Personal"
```

### Activate an activity
```bash
gnome-activities activate "Work"
```
This will:
1. Close all apps from the previous activity (except always-available apps)
2. Launch all apps that were open last time in the "Work" activity

### Show current activity
```bash
gnome-activities current
```

### Delete an activity
```bash
gnome-activities delete "Work"
```

### Modify an activity
```bash
gnome-activities modify "Work" --description "Updated description"
```

## Always-Available Apps

Some apps (like email clients) should always be available regardless of which activity is active.

```bash
# Add an always-available app
gnome-activities always add thunderbird
gnome-activities always add slack

# List always-available apps
gnome-activities always list

# Remove from always-available
gnome-activities always remove slack
```

## Status

```bash
gnome-activities status
```

## Daemon Management

```bash
# Start the background daemon
gnome-activities daemon --start

# Or via systemd
systemctl --user start gnome-activities
systemctl --user status gnome-activities
```
