variable "project_name" {
  description = "Name of the project, used for resource naming and tagging."
  type        = string
}

variable "environment" {
  description = "Deployment environment (dev, prod)."
  type        = string
}

variable "aws_region" {
  description = "AWS region; CloudFront 5xx metric must query us-east-1."
  type        = string
}

variable "backend_lambda_name" {
  description = "Full name of the backend request-handler Lambda (alarm dimension)."
  type        = string
}

variable "loader_lambda_name" {
  description = "Full name of the data-loader Lambda (alarm dimension + log filter source)."
  type        = string
}

variable "loader_log_group_name" {
  description = "Name of the Loader Lambda's CloudWatch log group. Used by aws_cloudwatch_log_metric_filter."
  type        = string
}

variable "rds_instance_identifier" {
  description = "RDS instance identifier (DBInstanceIdentifier dimension for the DatabaseConnections metric)."
  type        = string
}

variable "cloudfront_distribution_id" {
  description = "CloudFront distribution ID for the 5xx error rate dashboard widget."
  type        = string
}

variable "alert_email" {
  description = "Email address to receive SNS alarm notifications. Confirmation is manual (operator clicks AWS-sent confirmation link)."
  type        = string
  sensitive   = true
}

variable "backend_error_rate_threshold_pct" {
  description = "Backend Lambda error rate (%) above which the alarm fires."
  type        = number
  default     = 5
}

variable "backend_duration_p99_threshold_ms" {
  description = "Backend Lambda Duration p99 (ms) above which the alarm fires."
  type        = number
  default     = 10000
}

variable "rds_connections_threshold" {
  description = "RDS DatabaseConnections count above which the alarm fires (~70% of db.t3.micro max)."
  type        = number
  default     = 60
}
