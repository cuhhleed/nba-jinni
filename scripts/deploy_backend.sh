#!/usr/bin/env bash
# Package and deploy the backend (request-handler) Lambda code.
# Uploads the zip to S3, then tells Lambda to refresh from that key.
# Run from repo root: scripts/deploy_backend.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TF_DIR="$REPO_ROOT/infra/environments/dev"
ZIP_PATH="$REPO_ROOT/infra/backend.zip"
S3_KEY="backend.zip"

bash "$REPO_ROOT/scripts/package_backend.sh"

FUNCTION_NAME="$(terraform -chdir="$TF_DIR" output -raw backend_lambda_function_name)"
ARTIFACTS_BUCKET="$(terraform -chdir="$TF_DIR" output -raw lambda_artifacts_bucket_name)"

aws s3 cp "$ZIP_PATH" "s3://$ARTIFACTS_BUCKET/$S3_KEY"

aws lambda update-function-code \
  --function-name "$FUNCTION_NAME" \
  --s3-bucket "$ARTIFACTS_BUCKET" \
  --s3-key "$S3_KEY" \
  --publish > /dev/null

echo "Deployed $FUNCTION_NAME from s3://$ARTIFACTS_BUCKET/$S3_KEY"
