#!/usr/bin/env bash
# Build the React frontend with the dev API URL baked in, sync to S3,
# and invalidate CloudFront.
# Run from repo root: scripts/deploy_frontend.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TF_DIR="$REPO_ROOT/infra/environments/dev"
FRONTEND_DIR="$REPO_ROOT/frontend"

API_URL="$(terraform -chdir="$TF_DIR" output -raw api_gateway_url)"
BUCKET="$(terraform -chdir="$TF_DIR" output -raw frontend_bucket_name)"
DIST_ID="$(terraform -chdir="$TF_DIR" output -raw cloudfront_distribution_id)"

cd "$FRONTEND_DIR"

VITE_API_BASE_URL="$API_URL" npm ci
VITE_API_BASE_URL="$API_URL" npm run build

aws s3 sync dist/ "s3://$BUCKET/" --delete

aws cloudfront create-invalidation \
  --distribution-id "$DIST_ID" \
  --paths "/*" > /dev/null

echo "Synced frontend to s3://$BUCKET/ and invalidated CloudFront $DIST_ID"
