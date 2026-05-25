output "app_role_arn" {
  description = "ARN of the application-deploy role for this environment"
  value       = aws_iam_role.github_actions.arn
}

output "app_role_name" {
  description = "Name of the application-deploy role for this environment"
  value       = aws_iam_role.github_actions.name
}

output "terraform_role_arn" {
  description = "ARN of the Terraform-CI role for this environment"
  value       = aws_iam_role.terraform_ci.arn
}

output "terraform_role_name" {
  description = "Name of the Terraform-CI role for this environment"
  value       = aws_iam_role.terraform_ci.name
}
