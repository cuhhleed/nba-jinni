terraform {
  required_version = ">= 1.8.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

resource "aws_secretsmanager_secret" "db_credentials" {
  name = "${var.project_name}/${var.environment}/db-credentials"

  tags = {
    Name = "${var.project_name}-DB-credentials"
  }
}


resource "aws_secretsmanager_secret_version" "db_credentials_secret" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = var.db_username
    password = var.db_password
  })
}

module "vpc" {
  source = "../../modules/vpc"

  aws_region   = var.aws_region
  project_name = var.project_name
  environment  = var.environment
}

module "rds" {
  source = "../../modules/rds"

  project_name      = var.project_name
  environment       = var.environment
  vpc_id            = module.vpc.vpc_id
  subnet_ids        = module.vpc.private_subnet_ids
  security_group_id = module.vpc.rds_sg_id
  username          = var.db_username
  password          = var.db_password
}