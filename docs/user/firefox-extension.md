# Firefox Extension Setup

The GNOME Activities Firefox extension tracks your open tabs per activity.
When you switch activities, it can close old tabs and restore previously open tabs.

## Installation

### Step 1: Install the Native Messaging Host

The native messaging host bridges Firefox and the gnome-activities daemon.

```bash
# If installed via deb package, the host is already at:
# /usr/lib/gnome-activities/native-host.py

# Install the native messaging manifest for Firefox:
mkdir -p ~/.mozilla/native-messaging-hosts/
cp /usr/lib/mozilla/native-messaging-hosts/gnome.activities.json \
   ~/.mozilla/native-messaging-hosts/
```

For snap Firefox:
```bash
mkdir -p ~/snap/firefox/common/.mozilla/native-messaging-hosts/
cp /usr/lib/mozilla/native-messaging-hosts/gnome.activities.json \
   ~/snap/firefox/common/.mozilla/native-messaging-hosts/
```

### Step 2: Install the Firefox Extension

1. Open Firefox
2. Go to `about:debugging#/runtime/this-firefox`
3. Click **Load Temporary Add-on**
4. Navigate to `firefox-extension/manifest.json`

For permanent installation, install from the Firefox Add-ons store (when published).

## How It Works

- The extension monitors tab open/close/update events
- Events are sent to the native messaging host via the Firefox Native Messaging API
- The native host communicates with the gnome-activities daemon via D-Bus
- When you switch activities, the daemon notifies the extension to close old tabs and open new ones
