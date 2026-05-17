#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$SCRIPT_DIR/../infra/environments/dev"

echo "==> Switching to Terraform environment: $INFRA_DIR"
cd "$INFRA_DIR"

SECRET_ID=$(terraform output -raw db_secret_arn)

echo "==> Building targeted destroy list (excluding module.vpc core and module.s3*, preserving S3 bucket config)..."
TARGETS=$(terraform state list 2>/dev/null \
  | grep -v "^module\.vpc" \
  | grep -v "^module\.s3" \
  | grep -v "^module\..*security_group" \
  | grep -v "^aws_s3_bucket_versioning\." \
  | grep -v "^aws_s3_bucket_lifecycle_configuration\." \
  | sed 's/^/-target=/' | tr '\n' ' ')

# NAT Gateway components live inside module.vpc but are not foundational —
# explicitly re-add them so they are torn down even though the rest of vpc is preserved.
NAT_TARGETS="-target=module.vpc.aws_nat_gateway.main -target=module.vpc.aws_eip.nat -target=module.vpc.aws_route.private_internet"

if [ -z "$TARGETS" ]; then
  echo "No targets found in state. Nothing to destroy."
  exit 0
fi

echo ""
echo "Resources to be destroyed:"
terraform state list \
  | grep -v "^module\.vpc" \
  | grep -v "^module\.s3" \
  | grep -v "^module\..*security_group" \
  | grep -v "^aws_s3_bucket_versioning\." \
  | grep -v "^aws_s3_bucket_lifecycle_configuration\."
echo "  module.vpc.aws_nat_gateway.main"
echo "  module.vpc.aws_eip.nat"
echo "  module.vpc.aws_route.private_internet"
echo ""
read -p "Proceed with destroy? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
  echo "Aborted."
  exit 0
fi

echo "==> Running targeted destroy..."
terraform destroy $TARGETS $NAT_TARGETS

aws secretsmanager delete-secret \
  --secret-id "$SECRET_ID" \
  --force-delete-without-recovery \
  --no-cli-pager 2>/dev/null && echo "Secret deleted." || echo "Secret not found or already deleted, continuing."

echo "==> Teardown complete."