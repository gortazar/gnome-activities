#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$REPO_ROOT"

# dpkg-buildpackage expects packaging metadata at ./debian/; create a symlink
# to packaging/debian/ so the standard tooling finds it.
if [ ! -e debian ]; then
    ln -sf packaging/debian debian
    CREATED_SYMLINK=1
else
    CREATED_SYMLINK=0
fi

echo "Building gnome-activities .deb package..."
dpkg-buildpackage -us -uc -b --build-dir="$SCRIPT_DIR/dist"

if [ "$CREATED_SYMLINK" -eq 1 ]; then
    rm -f debian
fi

echo "Build complete. Check $SCRIPT_DIR/dist/"
