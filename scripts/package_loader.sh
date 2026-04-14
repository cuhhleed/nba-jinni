#!/usr/bin/env bash
# Build loader.zip for the data-loader Lambda.
# Run from repo root: scripts/package_loader.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOADER_DIR="$REPO_ROOT/loader"
SHARED_DIR="$REPO_ROOT/shared"
DIST_DIR="$LOADER_DIR/dist"
ZIP_PATH="$REPO_ROOT/infra/loader.zip"

echo "Building loader Lambda package..."

rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"

# Install loader dependencies into dist/
pip install \
  sqlalchemy[asyncio] \
  asyncpg \
  boto3 \
  structlog \
  alembic \
  --target "$DIST_DIR" \
  --quiet

# Copy nbajinni_shared package (excluding __pycache__)
rsync -a --exclude='__pycache__' "$SHARED_DIR/nbajinni_shared/" "$DIST_DIR/nbajinni_shared/"

# Copy loader handler
cp "$LOADER_DIR/main.py" "$DIST_DIR/main.py"

# Copy Alembic config and migrations (excluding __pycache__)
cp "$SHARED_DIR/alembic.ini" "$DIST_DIR/alembic.ini"
rsync -a --exclude='__pycache__' "$SHARED_DIR/alembic/" "$DIST_DIR/alembic/"

# Zip the package
cd "$DIST_DIR"
zip -r "$ZIP_PATH" . --quiet

echo "Created $ZIP_PATH"
