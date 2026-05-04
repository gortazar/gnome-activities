.PHONY: all install test lint security build-deb clean help

PYTHON ?= python3
PIP ?= pip3
DAEMON_DIR = daemon

all: test

help:
	@echo "Available targets:"
	@echo "  install     - Install daemon in development mode"
	@echo "  test        - Run all tests"
	@echo "  lint        - Run flake8 linter"
	@echo "  security    - Run bandit security scanner"
	@echo "  build-deb   - Build .deb package"
	@echo "  clean       - Clean build artifacts"

install:
	cd $(DAEMON_DIR) && $(PIP) install -e ".[dev]"

test:
	cd $(DAEMON_DIR) && pytest tests/ --tb=short -v

lint:
	cd $(DAEMON_DIR) && flake8 gnome_activities/ --max-line-length=120

security:
	cd $(DAEMON_DIR) && bandit -r gnome_activities/ -ll

build-deb:
	bash packaging/build-deb.sh

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf $(DAEMON_DIR)/.coverage $(DAEMON_DIR)/coverage.xml $(DAEMON_DIR)/htmlcov
	rm -rf packaging/dist
