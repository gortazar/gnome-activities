# GNOME Activities

KDE-like activities manager for GNOME Shell.

## Features

- Named activity contexts (Work, Personal, Gaming, …)
- Each activity remembers which apps and files are open
- Automatically closes/opens apps when switching activities
- Global apps (e.g., Spotify) stay open across all activities
- GNOME Shell panel indicator for quick switching
- Firefox extension for per-activity tab tracking
- D-Bus IPC service for integration with other tools
- Full CLI for scripting and automation

## Quick Start

```bash
# Install
sudo dpkg -i gnome-activities_0.1.0-1_all.deb

# Start the daemon
systemctl --user start gnome-activities

# Create activities
gnome-activities add Work
gnome-activities add Personal

# Add apps to an activity
gnome-activities app add Work firefox firefox
gnome-activities app add Work code "code /home/user/project"
gnome-activities app add Personal spotify spotify --global

# Switch activities
gnome-activities activate Work

# Check status
gnome-activities status
```

## Architecture

```
GNOME Shell Extension  ←→  D-Bus  ←→  Python Daemon
Firefox Extension      ←→  Native Messaging Host  ←→  CLI
```

The Python daemon manages activity state in `~/.config/gnome-activities/state.json`
and exposes a D-Bus service at `org.gnome.Activities`.

## Documentation

- [User Guide](docs/user/README.md)
- [Developer Guide](docs/developer/README.md)

## Development

```bash
make install   # install in editable mode with dev deps
make test      # run all tests
make lint      # run flake8
make security  # run bandit
```

## License

See [LICENSE](LICENSE).
