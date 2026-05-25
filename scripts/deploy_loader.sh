#!/usr/bin/env bash
# Package and deploy the data-loader Lambda code.
# Uploads the zip to S3, then (if the function already exists) refreshes Lambda from that key.
# Run from repo root: scripts/deploy_loader.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TF_DIR="$REPO_ROOT/infra/environments/dev"
ZIP_PATH="$REPO_ROOT/infra/loader.zip"
S3_KEY="loader.zip"

bash "$REPO_ROOT/scripts/package_loader.sh"

ARTIFACTS_BUCKET="$(terraform -chdir="$TF_DIR" output -raw lambda_artifacts_bucket_name)"

aws s3 cp "$ZIP_PATH" "s3://$ARTIFACTS_BUCKET/$S3_KEY"

FUNCTION_NAME="$(terraform -chdir="$TF_DIR" output -raw loader_lambda_function_name 2>/dev/null || echo "")"
if [[ -n "$FUNCTION_NAME" ]] && aws lambda get-function --function-name "$FUNCTION_NAME" >/dev/null 2>&1; then
  aws lambda update-function-code \
    --function-name "$FUNCTION_NAME" \
    --s3-bucket "$ARTIFACTS_BUCKET" \
    --s3-key "$S3_KEY" \
    --publish > /dev/null
  echo "Updated $FUNCTION_NAME from s3://$ARTIFACTS_BUCKET/$S3_KEY"
else
  echo "Function not yet deployed; uploaded zip to s3://$ARTIFACTS_BUCKET/$S3_KEY (run terraform apply to create)"
fi
