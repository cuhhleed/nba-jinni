#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Point the backend at the local dummy-game fixtures so /games/live/{game_id}
# serves PLAYOFF001.json instead of hitting the real NBA API. Exporting here
# (rather than relying on the caller's shell) guarantees the uvicorn child
# process inherits it. See docs/LOCAL_OPERATIONS.md.
export NBAJINNI_LIVE_FIXTURE_DIR="$SCRIPT_DIR/dev/fixtures"

cleanup() {
  echo ""
  echo "Shutting down..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}

trap cleanup INT TERM

echo "Starting backend..."
(cd "$SCRIPT_DIR/../backend" && poetry run uvicorn app.main:app --reload) &
BACKEND_PID=$!

echo "Starting frontend..."
(cd "$SCRIPT_DIR/../frontend" && npm run dev) &
FRONTEND_PID=$!

echo "Backend PID: $BACKEND_PID | Frontend PID: $FRONTEND_PID"
echo "Press Ctrl+C to stop both."

wait "$BACKEND_PID" "$FRONTEND_PID"
