output "arn" {
  description = "Identifying ARN for the Lambda function."
  value       = aws_lambda_function.main.arn
}

output "invoke_arn" {
  description = "Invoking ARN for the Lambda function to be used by API Gateway."
  value       = aws_lambda_function.main.invoke_arn
}
