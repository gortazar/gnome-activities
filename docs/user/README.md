# GNOME Activities — User Guide

## What is GNOME Activities?

GNOME Activities brings KDE Activities-like task management to GNOME Shell. It lets you create
named *activities* (e.g., "Work", "Personal", "Gaming") and associate them with a specific set
of open applications. When you switch activities, the previous activity's apps close and the new
activity's apps reopen automatically.

**No manual configuration is needed for apps.** GNOME Activities automatically tracks which
applications are open while an activity is active — open an app and it is added to the activity;
close it and it is removed.

---

## Installation

### From .deb Package

```bash
sudo dpkg -i gnome-activities_0.1.0-1_all.deb
sudo apt-get install -f   # install any missing dependencies
```

### From Source

```bash
cd daemon
pip install .
```

---

## Quick Start

1. Install and start the daemon (see below).
2. Enable the GNOME Shell extension (see below).
3. Click the **Activities** button in the top-right panel.
4. Click **＋ New Activity** and type a name (e.g., "Work") → press **Enter**.
5. Switch to that activity — it becomes active.
6. Open your work apps (browser, editor, terminal…).  They are tracked automatically.
7. When you later switch back, those apps reopen where you left them.

---

## Starting the Daemon

The daemon provides a D-Bus service that the GNOME Shell extension talks to.
Enable it as a systemd user service so it starts automatically at login:

```bash
systemctl --user enable gnome-activities
systemctl --user start gnome-activities
```

Or run it manually in a terminal for testing:

```bash
gnome-activities daemon
```

---

## Enabling the GNOME Shell Extension

1. Copy the extension to your extensions directory:

   ```bash
   cp -r gnome-extension ~/.local/share/gnome-shell/extensions/gnome-activities@gortazar.github.com
   ```

2. Restart GNOME Shell (press `Alt+F2`, type `r`, press Enter) or log out and back in.

3. Enable the extension:

   ```bash
   gnome-extensions enable gnome-activities@gortazar.github.com
   ```

4. An **Activities** indicator appears in the top-right of the panel.

---

## Using the Activities Panel

Click the **Activities** indicator in the top bar to open the panel menu.

### Switch to an activity

Click an activity name in the list.  The previous activity's apps close and
this activity's apps reopen.

### Create a new activity

Click **＋ New Activity** at the bottom of the menu, type the name, and press
**Enter** (or click **✔**).  Press **Escape** or click **✖** to cancel.

### Rename an activity

Click the **✏** pencil icon next to the activity name, type the new name, and
press **Enter**.

---

## Automatic App Tracking

While an activity is active, GNOME Activities automatically:

- **Adds** an app to the activity as soon as you launch it.
- **Removes** an app from the activity as soon as you close it.

This means the activity always reflects what was open the last time you used it.
No manual management of apps is required.

---

## Global Apps

Some apps (e.g., a music player, a communication tool) should stay open
regardless of which activity is active.  Mark them as *global* using the CLI:

```bash
gnome-activities always add thunderbird
```

Global apps are never closed when you switch activities.

---

## Firefox Extension Setup

The optional Firefox extension tracks which browser tabs are open per activity
so they are restored when you switch back.

1. Install the extension in Firefox:
   - Open Firefox → Extensions → Install from file → select `gnome-activities-firefox.zip`

2. Install the native messaging host:

   ```bash
   sudo install -D -m 755 firefox-extension/native/native_host.py \
       /usr/lib/gnome-activities/native_host.py
   sudo install -D -m 644 firefox-extension/native/manifest.json \
       /usr/lib/mozilla/native-messaging-hosts/gnome.activities.json
   ```

3. The extension will automatically track which tabs are open and notify the daemon.

---

## Advanced: CLI Reference

The CLI is intended for scripting and advanced configuration; day-to-day use
goes through the panel.

| Command | Description |
|---------|-------------|
| `gnome-activities list` | List all activities |
| `gnome-activities create <name>` | Create an activity |
| `gnome-activities delete <name>` | Delete an activity |
| `gnome-activities activate <name>` | Switch to an activity |
| `gnome-activities modify <name> -d <desc>` | Update an activity's description |
| `gnome-activities current` | Show the currently active activity |
| `gnome-activities status` | Show overall status and always-available apps |
| `gnome-activities always add <app_id>` | Mark an app as always available |
| `gnome-activities always remove <app_id>` | Unmark an app as always available |
| `gnome-activities always list` | List always-available apps |

---

## Troubleshooting

**The daemon won't start:**
- Check that `gnome-activities` is in your PATH: `which gnome-activities`
- Check D-Bus is running: `echo $DBUS_SESSION_BUS_ADDRESS`
- Check logs: `journalctl --user -u gnome-activities`

**Apps don't reopen when switching activities:**
- Ensure the daemon is running: `gnome-activities status`
- Check that the app was open while the activity was active (auto-tracking only works when the daemon is running)

**The GNOME Shell extension shows "No Activity":**
- Ensure the daemon is running: `systemctl --user status gnome-activities`
- Check that the D-Bus service is registered:
  `gdbus introspect --session --dest org.gnome.Activities --object-path /org/gnome/Activities`

