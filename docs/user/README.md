# GNOME Activities — User Guide

## What is GNOME Activities?

GNOME Activities brings KDE Activities-like task management to GNOME Shell. It lets you create
named *activities* (e.g., "Work", "Personal", "Gaming") and associates specific applications and
files with each one. When you switch activities, the previous activity's apps close and the new
activity's apps open automatically.

---

## Installation

### From .deb Package

```bash
sudo dpkg -i gnome-activities_0.1.0-1_all.deb
sudo apt-get install -f   # fix any missing dependencies
```

### From Source

```bash
cd daemon
pip install .
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

4. A panel indicator will appear in the top bar showing the current activity name.

---

## Starting the Daemon

The daemon provides a D-Bus service. Enable it as a systemd user service:

```bash
systemctl --user enable gnome-activities
systemctl --user start gnome-activities
```

Or run it manually:

```bash
gnome-activities daemon
```

---

## CLI Usage

### List activities

```bash
gnome-activities list
```

### Create a new activity

```bash
gnome-activities add Work
gnome-activities add Personal
```

### Switch to an activity

```bash
gnome-activities activate Work
```

This closes the current activity's non-global apps and opens all apps associated with "Work".

### Check the active activity

```bash
gnome-activities status
```

### Rename an activity

```bash
gnome-activities rename Work "Day Job"
```

### Remove an activity

```bash
gnome-activities remove Personal
```

---

## Managing Apps in Activities

### Add an app to an activity

```bash
gnome-activities app add Work firefox firefox
gnome-activities app add Work code "code /home/user/project"
gnome-activities app add Work notes "gedit" --file /home/user/notes.txt
```

### Mark an app as global (not closed when switching)

Global apps (e.g., Spotify, Slack) stay open regardless of which activity is active.

```bash
gnome-activities app add Work spotify spotify --global
```

### List apps in an activity

```bash
gnome-activities app list Work
```

### Remove an app from an activity

```bash
gnome-activities app remove Work firefox
```

---

## Firefox Extension Setup

1. Install the extension in Firefox:
   - Open Firefox → Extensions → Install from file → select `gnome-activities-firefox.zip`

2. Install the native messaging host:

   ```bash
   sudo install -D -m 755 firefox-extension/native-messaging/gnome_activities_host.py \
       /usr/lib/gnome-activities/gnome_activities_host.py
   sudo install -D -m 644 firefox-extension/native-messaging/org.gnome.activities.json \
       /usr/lib/mozilla/native-messaging-hosts/org.gnome.activities.json
   ```

3. The extension will automatically track which tabs are open and notify the daemon.

---

## Marking Apps as Global

Global apps are not closed when you switch activities. Examples:

- Music player (Spotify, Rhythmbox)
- Communication tools (Slack, Telegram)
- System monitor

```bash
gnome-activities app add Personal spotify spotify --global
```

---

## Troubleshooting

**The daemon won't start:**
- Check that `gnome-activities` is in your PATH: `which gnome-activities`
- Check D-Bus is running: `echo $DBUS_SESSION_BUS_ADDRESS`
- Check logs: `journalctl --user -u gnome-activities`

**Apps don't launch when switching activities:**
- Verify the `exec_cmd` is correct: `gnome-activities app list <activity>`
- Test the command manually in a terminal

**The GNOME Shell extension shows "No Activity":**
- Ensure the daemon is running: `gnome-activities status`
- Check that D-Bus service name `org.gnome.Activities` is registered:
  `gdbus introspect --session --dest org.gnome.Activities --object-path /org/gnome/Activities`
