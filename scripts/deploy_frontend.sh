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
CLOUDFRONT_DOMAIN="$(terraform -chdir="$TF_DIR" output -raw cloudfront_domain)"

cd "$FRONTEND_DIR"

VITE_API_BASE_URL="$API_URL" npm ci
VITE_API_BASE_URL="$API_URL" npm run build

aws s3 sync dist/ "s3://$BUCKET/" --delete

INV_ID="$(aws cloudfront create-invalidation \
  --distribution-id "$DIST_ID" \
  --paths "/*" \
  --query 'Invalidation.Id' \
  --output text)"

aws cloudfront wait invalidation-completed \
  --distribution-id "$DIST_ID" \
  --id "$INV_ID"

STATUS="$(curl -fsS -o /dev/null -w '%{http_code}' "https://$CLOUDFRONT_DOMAIN/")"
if [ "$STATUS" != "200" ]; then
  echo "Smoke test failed: expected 200, got $STATUS"
  exit 1
fi

echo "Synced frontend to s3://$BUCKET/, invalidation $INV_ID completed, smoke test passed (200)"
