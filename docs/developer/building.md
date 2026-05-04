# Building

## Prerequisites

```bash
sudo apt-get install python3 python3-pip python3-venv python3-dbus python3-gi \
  python3-click wmctrl debhelper dh-python
```

## Development Setup

```bash
git clone https://github.com/gortazar/gnome-activities.git
cd gnome-activities
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

## Running Tests

```bash
# All tests
pytest tests/

# Unit tests only
pytest tests/unit/ -v

# With coverage
pytest tests/ --cov=gnome_activities --cov-report=html
open htmlcov/index.html
```

## Linting

```bash
flake8 gnome_activities/ tests/ --max-line-length=120
black gnome_activities/ tests/ --line-length=120
```

## Security Scan

```bash
bandit -r gnome_activities/ -ll
```

## Building the Debian Package

```bash
dpkg-buildpackage -us -uc -b
ls ../*.deb
```

## Building the Firefox Extension

```bash
cd firefox-extension
zip -r ../gnome-activities-firefox.zip . -x "native/*"
```
