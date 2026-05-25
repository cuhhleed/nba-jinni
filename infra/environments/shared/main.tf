terraform {
  required_version = ">= 1.8.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = "shared"
      ManagedBy   = "terraform"
    }
  }
}

provider "github" {
  owner = var.github_owner
  token = var.github_token
}

data "aws_caller_identity" "current" {}

data "tls_certificate" "github_oidc" {
  url = "https://token.actions.githubusercontent.com"
}

data "github_user" "prod_reviewer" {
  username = var.github_owner
}

resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [for c in data.tls_certificate.github_oidc.certificates : c.sha1_fingerprint]
}

module "oidc_dev" {
  source = "../../modules/github_actions_oidc"

  project_name      = var.project_name
  environment       = "dev"
  github_repo       = var.github_repo
  aws_region        = var.aws_region
  account_id        = data.aws_caller_identity.current.account_id
  oidc_provider_arn = aws_iam_openid_connect_provider.github.arn
  state_bucket      = "nbajinni-terraform-state"
  lock_table        = "nbajinni-terraform-locks"
}

module "oidc_prod" {
  source = "../../modules/github_actions_oidc"

  project_name      = var.project_name
  environment       = "prod"
  github_repo       = var.github_repo
  aws_region        = var.aws_region
  account_id        = data.aws_caller_identity.current.account_id
  oidc_provider_arn = aws_iam_openid_connect_provider.github.arn
  state_bucket      = "nbajinni-terraform-state"
  lock_table        = "nbajinni-terraform-locks"
}

resource "github_repository_environment" "dev" {
  repository  = "nba-jinni"
  environment = "dev"
}

resource "github_repository_environment" "prod" {
  repository  = "nba-jinni"
  environment = "prod"

  reviewers {
    users = [data.github_user.prod_reviewer.id]
  }

  deployment_branch_policy {
    protected_branches     = true
    custom_branch_policies = false
  }
}

resource "github_actions_environment_secret" "dev_role_arn" {
  repository  = "nba-jinni"
  environment = github_repository_environment.dev.environment
  secret_name = "AWS_ROLE_ARN"
  value       = module.oidc_dev.app_role_arn
}

resource "github_actions_environment_secret" "prod_role_arn" {
  repository  = "nba-jinni"
  environment = github_repository_environment.prod.environment
  secret_name = "AWS_ROLE_ARN"
  value       = module.oidc_prod.app_role_arn
}

resource "github_actions_environment_secret" "dev_region" {
  repository  = "nba-jinni"
  environment = github_repository_environment.dev.environment
  secret_name = "AWS_REGION"
  value       = var.aws_region
}

resource "github_actions_environment_secret" "prod_region" {
  repository  = "nba-jinni"
  environment = github_repository_environment.prod.environment
  secret_name = "AWS_REGION"
  value       = var.aws_region
}

resource "github_actions_environment_secret" "tf_role_arn_dev" {
  repository  = "nba-jinni"
  environment = github_repository_environment.dev.environment
  secret_name = "TF_ROLE_ARN"
  value       = module.oidc_dev.terraform_role_arn
}

resource "github_actions_environment_secret" "tf_role_arn_prod" {
  repository  = "nba-jinni"
  environment = github_repository_environment.prod.environment
  secret_name = "TF_ROLE_ARN"
  value       = module.oidc_prod.terraform_role_arn
}