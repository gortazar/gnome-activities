# Installation

## From Debian Package

Download the latest `.deb` from the [Releases page](https://github.com/gortazar/gnome-activities/releases):

```bash
sudo dpkg -i gnome-activities_0.1.0-1_all.deb
sudo apt-get install -f   # resolve dependencies
```

## From Source

### Prerequisites

- Python 3.9+
- `python3-dbus`
- `python3-gi`
- `python3-click`
- `wmctrl` (recommended, for window tracking)

```bash
sudo apt-get install python3-dbus python3-gi python3-click wmctrl
```

### Install

```bash
git clone https://github.com/gortazar/gnome-activities.git
cd gnome-activities
pip install -e .
```

## Enable the Systemd Service

```bash
systemctl --user enable gnome-activities
systemctl --user start gnome-activities
```

## Firefox Extension

See [Firefox Extension Setup](firefox-extension.md).
