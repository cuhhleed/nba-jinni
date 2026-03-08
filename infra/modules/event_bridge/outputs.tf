output "rule_arn" {
  description = "ARN of provisioned Event Bridge rule."
  value       = aws_cloudwatch_event_rule.main.arn
}

