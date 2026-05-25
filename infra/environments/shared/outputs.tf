output "dev_role_arn" {
  description = "ARN of the application-deploy IAM role for the dev environment"
  value       = module.oidc_dev.app_role_arn
}

output "prod_role_arn" {
  description = "ARN of the application-deploy IAM role for the prod environment"
  value       = module.oidc_prod.app_role_arn
}

output "dev_terraform_role_arn" {
  description = "ARN of the Terraform-CI IAM role for the dev environment"
  value       = module.oidc_dev.terraform_role_arn
}

output "prod_terraform_role_arn" {
  description = "ARN of the Terraform-CI IAM role for the prod environment"
  value       = module.oidc_prod.terraform_role_arn
}

output "oidc_provider_arn" {
  description = "ARN of the GitHub Actions OIDC identity provider"
  value       = aws_iam_openid_connect_provider.github.arn
}