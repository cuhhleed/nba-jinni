#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

if [ -z "$1" ]; then
    echo "Usage: $0 <job>" >&2
    echo "Jobs: nightly, roster, schedule, first-start" >&2
    exit 1
fi

[ -f .env ] && set -a && source .env && set +a

cd ingestion
poetry run python cli.py "$1"
