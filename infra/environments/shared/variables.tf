variable "aws_region" {
  description = "AWS region for the OIDC provider and IAM resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name of the project, used for resource naming and tagging"
  type        = string
  default     = "nbajinni"
}

variable "github_repo" {
  description = "GitHub repository in owner/name format (e.g. cuhhleed/nba-jinni)"
  type        = string
  default     = "cuhhleed/nba-jinni"
}

variable "github_owner" {
  description = "GitHub username or org that owns the repository"
  type        = string
  default     = "cuhhleed"
}

variable "github_token" {
  description = "Fine-grained GitHub PAT with Administration, Secrets, and Environments write permissions. Pass via TF_VAR_github_token or GITHUB_TOKEN env var — never commit."
  type        = string
  sensitive   = true
}
