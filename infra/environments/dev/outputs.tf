output "rds_endpoint" {
  description = "RDS PostgreSQL instance endpoint"
  value       = module.rds.endpoint
}

output "api_gateway_url" {
  description = "API Gateway invoke URL."
  value       = module.api_gateway.api_endpoint
}

# output "cloudfront_domain" {
#   description = "CloudFront distribution domain for the frontend"
#   value       = module.frontend.cloudfront_domain
# }

output "db_secret_arn" {
  description = "ARN of the Secrets Manager secret containing DB credentials."
  value       = aws_secretsmanager_secret.db_credentials.arn
}
