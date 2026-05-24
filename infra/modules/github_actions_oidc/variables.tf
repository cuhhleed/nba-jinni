variable "project_name" {
  description = "Name of the project, used for resource naming and tagging"
  type        = string
}

variable "environment" {
  description = "Deployment environment (dev, prod)"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository in owner/name format (e.g. cuhhleed/nba-jinni)"
  type        = string
}

variable "aws_region" {
  description = "AWS region for ARN construction in the deploy policy"
  type        = string
}

variable "account_id" {
  description = "AWS account ID for ARN construction in the deploy policy"
  type        = string
}

variable "oidc_provider_arn" {
  description = "ARN of the GitHub Actions OIDC provider (created at the shared env root)"
  type        = string
}
