#!/bin/bash
set -e

# IMPORTANT: This script uses an explicit target list, not a catch-all.
# It destroys only resources with a real monthly cost (RDS, NAT Gateway, EIP,
# Secrets Manager, CloudWatch Alarms, CloudWatch Dashboard).
# Free/idle resources (Lambda, API Gateway, CloudFront, IAM, VPC primitives,
# S3 buckets, security groups, SNS topic) are intentionally preserved to speed
# up re-spinup.
#
# If a new expensive AWS resource is added to the stack (e.g. ElastiCache,
# another RDS instance), its Terraform address MUST be added to the TARGETS
# variable below — it will NOT be torn down automatically.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$SCRIPT_DIR/../infra/environments/dev"

echo "==> Switching to Terraform environment: $INFRA_DIR"
cd "$INFRA_DIR"

SECRET_ID=$(terraform output -raw db_secret_arn)

TARGETS="\
  -target=module.rds \
  -target=module.vpc.aws_nat_gateway.main \
  -target=module.vpc.aws_eip.nat \
  -target=module.vpc.aws_route.private_internet \
  -target=aws_secretsmanager_secret.db_credentials \
  -target=aws_secretsmanager_secret_version.db_credentials_secret \
  -target=module.observability.aws_cloudwatch_dashboard.overview \
  -target=module.observability.aws_cloudwatch_metric_alarm.backend_error_rate \
  -target=module.observability.aws_cloudwatch_metric_alarm.backend_duration_p99 \
  -target=module.observability.aws_cloudwatch_metric_alarm.loader_failure \
  -target=module.observability.aws_cloudwatch_metric_alarm.rds_connection_saturation"

echo ""
echo "Resources to be destroyed:"
echo "  module.rds"
echo "  module.vpc.aws_nat_gateway.main"
echo "  module.vpc.aws_eip.nat"
echo "  module.vpc.aws_route.private_internet"
echo "  aws_secretsmanager_secret.db_credentials"
echo "  aws_secretsmanager_secret_version.db_credentials_secret"
echo "  module.observability.aws_cloudwatch_dashboard.overview"
echo "  module.observability.aws_cloudwatch_metric_alarm.backend_error_rate"
echo "  module.observability.aws_cloudwatch_metric_alarm.backend_duration_p99"
echo "  module.observability.aws_cloudwatch_metric_alarm.loader_failure"
echo "  module.observability.aws_cloudwatch_metric_alarm.rds_connection_saturation"
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
