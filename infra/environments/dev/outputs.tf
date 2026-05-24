output "rds_endpoint" {
  description = "RDS PostgreSQL instance endpoint"
  value       = module.rds.endpoint
}

output "api_gateway_url" {
  description = "API Gateway invoke URL."
  value       = module.api_gateway.api_endpoint
}

output "db_secret_arn" {
  description = "ARN of the Secrets Manager secret containing DB credentials."
  value       = aws_secretsmanager_secret.db_credentials.arn
}

output "backend_lambda_function_name" {
  description = "Name of the backend request-handler Lambda function."
  value       = module.lambda_backend.function_name
}

output "loader_lambda_function_name" {
  description = "Name of the data-loader Lambda function."
  value       = module.lambda_loader.function_name
}

output "lambda_artifacts_bucket_name" {
  description = "S3 bucket holding Lambda deployment artifacts."
  value       = module.s3_lambda_artifacts.bucket_id
}

output "frontend_bucket_name" {
  description = "S3 bucket hosting the built React frontend."
  value       = module.s3_frontend.bucket_id
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID for the frontend."
  value       = module.cloudfront_frontend.distribution_id
}

output "cloudfront_domain" {
  description = "CloudFront domain for the deployed frontend."
  value       = module.cloudfront_frontend.domain_name
}
