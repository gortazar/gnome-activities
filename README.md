# GNOME Activities Manager

A KDE-activities-like tool for the GNOME desktop environment.

[![CI](https://github.com/gortazar/gnome-activities/actions/workflows/ci.yml/badge.svg)](https://github.com/gortazar/gnome-activities/actions/workflows/ci.yml)

## What is it?

GNOME Activities Manager lets you create named *activities* (like projects or contexts),
each remembering which applications and files were open. Switch between activities to
automatically close irrelevant apps and reopen the ones you need.

## Features

- 🗂️ **Activities** — Create named activities (Work, Personal, Gaming...)
- 🚀 **Auto-launch** — When you switch to an activity, all its apps reopen
- 🔒 **Auto-close** — Apps from the previous activity are closed automatically
- 📌 **Always-available apps** — Pin apps like Thunderbird to always stay open
- 🦊 **Firefox integration** — Browser tabs are tracked and restored per activity
- 🖥️ **D-Bus service** — Daemon runs in the background
- ⌨️ **CLI** — Full command-line interface

## Quick Start

```bash
# Install
sudo dpkg -i gnome-activities_0.1.0-1_all.deb

# Create activities
gnome-activities create "Work" --description "Daily work"
gnome-activities create "Personal" --description "Personal projects"

# Activate an activity
gnome-activities activate "Work"

# List activities
gnome-activities list

# Keep Thunderbird always available
gnome-activities always add thunderbird
```

## Installation

See [docs/user/installation.md](docs/user/installation.md).

## Usage

See [docs/user/usage.md](docs/user/usage.md).

## Firefox Extension

See [docs/user/firefox-extension.md](docs/user/firefox-extension.md).

## Development

See [docs/developer/building.md](docs/developer/building.md).

## Architecture

See [docs/developer/architecture.md](docs/developer/architecture.md).

## License

MIT License. See [LICENSE](LICENSE).
