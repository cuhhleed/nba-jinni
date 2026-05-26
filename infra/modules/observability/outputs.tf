output "sns_topic_arn" {
  description = "ARN of the alerts SNS topic."
  value       = aws_sns_topic.alerts.arn
}

output "dashboard_name" {
  description = "Name of the CloudWatch dashboard for this environment."
  value       = aws_cloudwatch_dashboard.overview.dashboard_name
}

output "alarm_arns" {
  description = "Map of alarm-key to ARN for all alarms in this env."
  value = {
    backend_error_rate        = aws_cloudwatch_metric_alarm.backend_error_rate.arn
    backend_duration_p99      = aws_cloudwatch_metric_alarm.backend_duration_p99.arn
    loader_failure            = aws_cloudwatch_metric_alarm.loader_failure.arn
    rds_connection_saturation = aws_cloudwatch_metric_alarm.rds_connection_saturation.arn
  }
}
