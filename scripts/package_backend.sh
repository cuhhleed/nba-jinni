#!/usr/bin/env bash
# Build backend.zip for the request-handler (FastAPI + Mangum) Lambda.
# Run from repo root: scripts/package_backend.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$REPO_ROOT/backend"
SHARED_DIR="$REPO_ROOT/shared"
DIST_DIR="$BACKEND_DIR/dist"
ZIP_PATH="$REPO_ROOT/infra/backend.zip"

echo "Building backend Lambda package..."

rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"

# Install backend runtime dependencies into dist/
pip install \
  fastapi \
  mangum \
  "sqlalchemy[asyncio]" \
  asyncpg \
  pydantic \
  pydantic-settings \
  python-dotenv \
  boto3 \
  structlog \
  nba-api \
  --target "$DIST_DIR" \
  --quiet

# Copy nbajinni_shared package (excluding __pycache__)
rsync -a --exclude='__pycache__' "$SHARED_DIR/nbajinni_shared/" "$DIST_DIR/nbajinni_shared/"

# Copy backend app package so app.main.handler resolves at the zip root
rsync -a --exclude='__pycache__' "$BACKEND_DIR/app/" "$DIST_DIR/app/"

# Zip the package
cd "$DIST_DIR"
rm -f "$ZIP_PATH"
zip -r "$ZIP_PATH" . --quiet

echo "Created $ZIP_PATH"
