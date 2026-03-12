#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$SCRIPT_DIR/../infra/environments/dev"
SECRET_ID=$(terraform output -raw db_credentials_secret_id)

echo "==> Switching to Terraform environment: $INFRA_DIR"
cd "$INFRA_DIR"

echo "==> Building targeted destroy list (excluding module.vpc)..."
TARGETS=$(terraform state list 2>/dev/null | grep -v "^module\.vpc" | sed 's/^/-target=/' | tr '\n' ' ')

if [ -z "$TARGETS" ]; then
  echo "No targets found in state. Nothing to destroy."
  exit 0
fi

echo ""
echo "Resources to be destroyed:"
terraform state list | grep -v "^module\.vpc"
echo ""
read -p "Proceed with destroy? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
  echo "Aborted."
  exit 0
fi

echo "==> Running targeted destroy..."
terraform destroy $TARGETS

aws secretsmanager delete-secret \
  --secret-id "$SECRET_ID" \
  --force-delete-without-recovery \
  --no-cli-pager 2>/dev/null && echo "Secret deleted." || echo "Secret not found or already deleted, continuing."

echo "==> Teardown complete."