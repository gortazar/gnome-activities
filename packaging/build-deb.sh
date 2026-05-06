#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$REPO_ROOT"

echo "Building gnome-activities .deb package..."
dpkg-buildpackage -us -uc -b --build-dir="$SCRIPT_DIR/dist"
echo "Build complete. Check $SCRIPT_DIR/dist/"
