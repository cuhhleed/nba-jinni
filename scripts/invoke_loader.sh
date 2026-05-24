#!/usr/bin/env bash
# Invoke the data-loader Lambda with either "migrate" or "load".
#   migrate → runs Alembic upgrade head, then truncates + loads from S3
#   load    → truncates + loads from S3 (no migration)
# Run from repo root: scripts/invoke_loader.sh <migrate|load>
set -euo pipefail

if [[ $# -ne 1 || ( "$1" != "migrate" && "$1" != "load" ) ]]; then
  echo "Usage: $0 <migrate|load>" >&2
  exit 2
fi

ACTION="$1"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TF_DIR="$REPO_ROOT/infra/environments/dev"
RESPONSE_FILE="$(mktemp)"
META_FILE="$(mktemp)"

FUNCTION_NAME="$(terraform -chdir="$TF_DIR" output -raw loader_lambda_function_name)"

echo "Invoking $FUNCTION_NAME with action=$ACTION (timeout 5 min)..."

aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --payload "{\"action\":\"$ACTION\"}" \
  --cli-binary-format raw-in-base64-out \
  --cli-read-timeout 360 \
  "$RESPONSE_FILE" \
  > "$META_FILE"

echo "--- Lambda response ---"
cat "$RESPONSE_FILE"
echo
echo "--- Invoke metadata ---"
cat "$META_FILE"
echo

FAILED=0
if grep -q '"FunctionError"' "$META_FILE"; then
  FAILED=1
fi

rm -f "$RESPONSE_FILE" "$META_FILE"

if [[ $FAILED -eq 1 ]]; then
  echo "Loader invocation failed — function raised an exception" >&2
  exit 1
fi

echo "Loader $ACTION complete."
