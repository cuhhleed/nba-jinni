output "dev_role_arn" {
  description = "ARN of the GitHub Actions IAM role for the dev environment"
  value       = module.oidc_dev.role_arn
}

output "prod_role_arn" {
  description = "ARN of the GitHub Actions IAM role for the prod environment"
  value       = module.oidc_prod.role_arn
}

output "oidc_provider_arn" {
  description = "ARN of the GitHub Actions OIDC identity provider"
  value       = aws_iam_openid_connect_provider.github.arn
}