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

module "lambda_security_group" {
  source = "../../modules/security_groups"

  project_name = var.project_name
  environment  = var.environment
  sg_name      = "lambda_sg"
  vpc_id       = module.vpc.vpc_id
  egress_rules = [{ from_port = 5432 }, { from_port = 443 }]
}
module "rds_security_group" {
  source = "../../modules/security_groups"

  project_name  = var.project_name
  environment   = var.environment
  sg_name       = "rds_sg"
  vpc_id        = module.vpc.vpc_id
  ingress_rules = [{ from_port = 5432, security_groups = [module.lambda_security_group.security_group_id] }]
  egress_rules  = [{ from_port = 0, protocol = "-1" }]
}

module "rds" {
  source = "../../modules/rds"

  project_name      = var.project_name
  environment       = var.environment
  vpc_id            = module.vpc.vpc_id
  subnet_ids        = module.vpc.private_subnet_ids
  security_group_id = module.rds_security_group.security_group_id
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

module "lambda_backend" {
  source = "../../modules/lambda"

  project_name       = var.project_name
  environment        = var.environment
  function_name      = "request-handler"
  filename           = "../../placeholder_backend.zip"
  role               = aws_iam_role.lambda_exec.arn
  handler            = "main.handler"
  subnet_ids         = module.vpc.public_subnet_ids
  security_group_ids = [module.lambda_security_group.security_group_id]

  environment_variables = {
    DB_HOST     = module.rds.endpoint
    DB_NAME     = module.rds.db_name
    DB_USER     = jsondecode(aws_secretsmanager_secret_version.db_credentials_secret.secret_string)["username"]
    DB_PASSWORD = jsondecode(aws_secretsmanager_secret_version.db_credentials_secret.secret_string)["password"]
  }
}

module "api_gateway" {
  source = "../../modules/api_gateway"

  project_name      = var.project_name
  environment       = var.environment
  lambda_invoke_arn = module.lambda_backend.invoke_arn
  lambda_arn        = module.lambda_backend.arn
}

module "s3_frontend" {
  source = "../../modules/s3"

  project_name = var.project_name
  environment  = var.environment
  bucket_name  = "frontend"
}

module "cloudfront_frontend" {
  source = "../../modules/cloudfront"

  project_name      = var.project_name
  environment       = var.environment
  origins           = [{ domain_name = module.s3_frontend.bucket_regional_domain_name, origin_id = module.s3_frontend.bucket_id }]
  target_origin_id  = module.s3_frontend.bucket_id
  oac_name          = "frontend-OAC"
  distribution_name = "frontend_CFN"

  allow_methods  = ["GET", "HEAD"]
  cached_methods = ["GET", "HEAD"]
}

resource "aws_s3_bucket_policy" "s3-policy-frontend" {
  bucket = module.s3_frontend.bucket_id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "AllowCloudFrontOAC"
      Effect = "Allow"
      Principal = {
        Service = "cloudfront.amazonaws.com"
      }
      Action   = "s3:GetObject"
      Resource = "${module.s3_frontend.bucket_arn}/*"
      Condition = {
        StringEquals = {
          "AWS:SourceArn" = module.cloudfront_frontend.distribution_arn
        }
      }
    }]
  })
}

module "s3_data_exports" {
  source       = "../../modules/s3"
  project_name = var.project_name
  environment  = var.environment
  bucket_name  = "data-exports"
}

resource "aws_s3_bucket_versioning" "data_exports" {
  bucket = module.s3_data_exports.bucket_id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "data_exports" {
  bucket = module.s3_data_exports.bucket_id

  rule {
    id     = "expire-old-versions"
    status = "Enabled"
    filter {
      prefix = "tmp/"
    }

    noncurrent_version_expiration {
      newer_noncurrent_versions = 7
      noncurrent_days           = 30
    }
  }

  depends_on = [aws_s3_bucket_versioning.data_exports]
}

resource "aws_iam_policy" "lambda_s3" {
  name = "${var.project_name}-${var.environment}-lambda-s3-access"
  policy = templatefile("${path.root}/../../policies/lambda_s3_policy.json.tpl", {
    bucket_arn = module.s3_data_exports.bucket_arn
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-lambda-s3-policy"
  }
}

resource "aws_iam_role_policy_attachment" "lambda_s3_attach" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_s3.arn
}

module "lambda_loader" {
  source = "../../modules/lambda"

  project_name       = var.project_name
  environment        = var.environment
  function_name      = "data-loader"
  filename           = "../../loader.zip"
  role               = aws_iam_role.lambda_exec.arn
  handler            = "main.handler"
  timeout            = 300
  memory_size        = 512
  subnet_ids         = module.vpc.private_subnet_ids
  security_group_ids = [module.lambda_security_group.security_group_id]

  environment_variables = {
    DB_HOST          = module.rds.endpoint
    DB_NAME          = module.rds.db_name
    DB_USER          = jsondecode(aws_secretsmanager_secret_version.db_credentials_secret.secret_string)["username"]
    DB_PASSWORD      = jsondecode(aws_secretsmanager_secret_version.db_credentials_secret.secret_string)["password"]
    DATA_BUCKET_NAME = module.s3_data_exports.bucket_id
  }
}

