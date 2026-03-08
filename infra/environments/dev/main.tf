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

resource "aws_iam_role" "lambda_exec" {
  name               = "${var.project_name}-${var.environment}-lambda-exec-role"
  assume_role_policy = file("${path.root}/../../policies/lambda_trust_policy.json")

  tags = {
    Name = "${var.project_name}-${var.environment}-lambda-exec-role"
  }
}

resource "aws_iam_policy" "lambda_secrets" {
  name = "${var.project_name}-${var.environment}-lambda-secrets-access"
  policy = templatefile("${path.root}/../../policies/lambda_secrets_policy.json.tpl", {
    secret_arn = aws_secretsmanager_secret.db_credentials.arn
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-lambda-secrets-policy"
  }
}


resource "aws_iam_role_policy_attachment" "lambda_secrets_attach" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_secrets.arn
}

resource "aws_iam_role_policy_attachment" "lambda_vpc_attach" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

module "lambda_ingestion" {
  source = "../../modules/lambda"

  project_name       = var.project_name
  environment        = var.environment
  function_name      = "daily-ingestion"
  filename           = "../../placeholder_ingestion.zip"
  role               = aws_iam_role.lambda_exec.arn
  handler            = "main.handler"
  timeout            = 300
  subnet_ids         = module.vpc.public_subnet_ids
  security_group_ids = [module.vpc.lambda_sg_id]

  environment_variables = {
    DB_HOST       = module.rds.endpoint
    DB_NAME       = module.rds.db_name
    DB_PORT       = module.rds.port
    DB_SECRET_ARN = aws_secretsmanager_secret.db_credentials.arn
  }
}

module "lambda_backend" {
  source = "../../modules/lambda"

  project_name       = var.project_name
  environment        = var.environment
  function_name      = "request-handler"
  filename           = "../../placeholder_backend.zip"
  role               = aws_iam_role.lambda_exec.arn
  handler            = "main.handler"
  subnet_ids         = module.vpc.public_subnet_ids
  security_group_ids = [module.vpc.lambda_sg_id]

  environment_variables = {
    DB_HOST       = module.rds.endpoint
    DB_NAME       = module.rds.db_name
    DB_PORT       = module.rds.port
    DB_SECRET_ARN = aws_secretsmanager_secret.db_credentials.arn
  }
}

module "api_gateway" {
  source = "../../modules/api_gateway"

  project_name      = var.project_name
  environment       = var.environment
  lambda_invoke_arn = module.lambda_backend.invoke_arn
  lambda_arn        = module.lambda_backend.arn
}

module "event_bridge" {
  source = "../../modules/event_bridge"

  project_name        = var.project_name
  environment         = var.environment
  lambda_arn          = module.lambda_ingestion.arn
  rule_name           = "daily-ingestion-rule"
  schedule_expression = "cron(0 9 * * ? *)"
}
