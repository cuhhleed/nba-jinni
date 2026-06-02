#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

VALID_JOBS="nightly|roster|schedule|playoff-schedule"

if [ -z "${1:-}" ] || ! echo "$1" | grep -qE "^($VALID_JOBS)$"; then
    echo "Usage: $0 <job>" >&2
    echo "Jobs: nightly, roster, schedule, playoff-schedule" >&2
    echo "(first-start is excluded — run manually via run_ingestion.sh)" >&2
    exit 1
fi

JOB="$1"

cd "$PROJECT_ROOT"

[ -f .env ] && set -a && source .env && set +a

AWS_PROFILE="${AWS_PROFILE:-nbajinni-dev-cron}"
AWS_REGION="${AWS_REGION:-us-east-1}"
DATA_BUCKET_NAME="${DATA_BUCKET_NAME:-nbajinni-dev-data-exports}"
LOADER_FN="${LOADER_FN:-nbajinni-dev-data-loader}"
export AWS_PROFILE AWS_REGION DATA_BUCKET_NAME

# Step 1: Ingest — writes to local PostgreSQL
(cd ingestion && poetry run python cli.py "$JOB")

# Step 2: Export — reads local PostgreSQL and writes JSON to staging area
(cd scripts && poetry run python export_to_json.py)

# Step 3: Upload — syncs staging JSON to the S3 data-exports bucket
(cd scripts && poetry run python upload_to_s3.py)

# Step 4: Invoke Loader asynchronously — Lambda picks up the new S3 objects
aws lambda invoke \
    --function-name "$LOADER_FN" \
    --invocation-type Event \
    --region "$AWS_REGION" \
    /tmp/loader-invoke-${JOB}.json

# Step 5: Heartbeat — emitted last so it signals end-to-end success
aws cloudwatch put-metric-data \
    --namespace NBAJinni/Ingestion \
    --metric-name IngestionHeartbeat \
    --value 1 \
    --unit Count \
    --dimensions "JobName=$JOB" \
    --region "$AWS_REGION"
