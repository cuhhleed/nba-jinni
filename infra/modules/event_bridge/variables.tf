variable "project_name" {
  description = "Name of the project, used for resource naming and tagging."
  type        = string
}

variable "environment" {
  description = "Deployment environment (dev, prod)."
  type        = string
}

variable "rule_name" {
  description = "Name of the rule, identify what it does relative to the project."
  type        = string
}

variable "schedule_expression" {
  description = "The scheduling CRON expression."
  type        = string
}

# Event Bridge Lambda permission resource

variable "lambda_arn" {
  description = "ARN for Lambda function to give permission on."
  type        = string
}


