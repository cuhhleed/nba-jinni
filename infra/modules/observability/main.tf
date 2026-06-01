resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-${var.environment}-alerts"

  tags = {
    Name = "${var.project_name}-${var.environment}-alerts"
  }
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# Backend Lambda error rate alarm — metric math: (Errors / Invocations) * 100
# Fires when the rate meets or exceeds backend_error_rate_threshold_pct over 2
# consecutive 5-minute evaluation windows.
resource "aws_cloudwatch_metric_alarm" "backend_error_rate" {
  alarm_name          = "${var.project_name}-${var.environment}-backend-error-rate"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 2
  threshold           = var.backend_error_rate_threshold_pct
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  alarm_description   = "Backend Lambda error rate (Errors/Invocations) >= ${var.backend_error_rate_threshold_pct}% over 2 consecutive 5-min windows."

  metric_query {
    id          = "e1"
    return_data = false
    metric {
      metric_name = "Errors"
      namespace   = "AWS/Lambda"
      period      = 300
      stat        = "Sum"
      dimensions = {
        FunctionName = var.backend_lambda_name
      }
    }
  }

  metric_query {
    id          = "i1"
    return_data = false
    metric {
      metric_name = "Invocations"
      namespace   = "AWS/Lambda"
      period      = 300
      stat        = "Sum"
      dimensions = {
        FunctionName = var.backend_lambda_name
      }
    }
  }

  metric_query {
    id          = "e2"
    expression  = "(e1 / IF(i1 > 0, i1, 1)) * 100"
    label       = "ErrorRatePct"
    return_data = true
  }
}

# Backend Lambda Duration p99 alarm.
# Fires when the p99 latency meets or exceeds backend_duration_p99_threshold_ms
# over 2 consecutive 5-minute evaluation windows.
resource "aws_cloudwatch_metric_alarm" "backend_duration_p99" {
  alarm_name          = "${var.project_name}-${var.environment}-backend-duration-p99"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 2
  threshold           = var.backend_duration_p99_threshold_ms
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  alarm_description   = "Backend Lambda Duration p99 >= ${var.backend_duration_p99_threshold_ms} ms over 2 consecutive 5-min windows."
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  extended_statistic  = "p99"
  period              = 300

  dimensions = {
    FunctionName = var.backend_lambda_name
  }
}

# Loader Lambda failure alarm.
# Fires when the Loader has >= 1 error invocation within a 24-hour window.
# Single evaluation period (daily batch job — one failure is already a signal).
resource "aws_cloudwatch_metric_alarm" "loader_failure" {
  alarm_name          = "${var.project_name}-${var.environment}-loader-failure"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  threshold           = 1
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  alarm_description   = "Loader Lambda has had >= 1 error invocation in the last 24h."
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  statistic           = "Sum"
  period              = 86400

  dimensions = {
    FunctionName = var.loader_lambda_name
  }
}

locals {
  ingestion_jobs = {
    nightly            = { period = 3600,  eval = 3,  description = "nightly hourly within game window (3h consecutive miss)", treat_missing = "missing" }
    roster             = { period = 86400, eval = 7,  description = "roster weekly (7-day window, CloudWatch max for daily period)",          treat_missing = "breaching" }
    schedule           = { period = 86400, eval = 7,  description = "schedule weekly (7-day window, CloudWatch max for daily period)",        treat_missing = "breaching" }
    "playoff-schedule" = { period = 86400, eval = 7,  description = "playoff-schedule weekly (7-day window, CloudWatch max for daily period)", treat_missing = "breaching" }
  }
}

resource "aws_cloudwatch_metric_alarm" "ingestion_heartbeat" {
  for_each            = local.ingestion_jobs
  alarm_name          = "${var.project_name}-${var.environment}-ingestion-heartbeat-${each.key}"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = each.value.eval
  datapoints_to_alarm = each.value.eval
  threshold           = 1
  treat_missing_data  = each.value.treat_missing
  alarm_actions       = [aws_sns_topic.alerts.arn]
  alarm_description   = "No IngestionHeartbeat for ${each.key} - ${each.value.description}."
  metric_name         = "IngestionHeartbeat"
  namespace           = "NBAJinni/Ingestion"
  statistic           = "Sum"
  period              = each.value.period
  dimensions          = { JobName = each.key }
}

# RDS connection saturation alarm.
# 60 connections ≈ 70% of db.t3.micro max (~85). Fires over 2 consecutive
# 5-minute windows so transient spikes during deploys don't page.
resource "aws_cloudwatch_metric_alarm" "rds_connection_saturation" {
  alarm_name          = "${var.project_name}-${var.environment}-rds-connection-saturation"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 2
  threshold           = var.rds_connections_threshold
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  alarm_description   = "RDS DatabaseConnections >= ${var.rds_connections_threshold} over 2 consecutive 5-min windows (~70% of db.t3.micro max ~85)."
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  statistic           = "Maximum"
  period              = 300

  dimensions = {
    DBInstanceIdentifier = var.rds_instance_identifier
  }
}

# Log metric filter that counts successful Loader runs.
# Watches for the literal substring "Loader run complete" emitted by loader/main.py
# and publishes a LoaderRunSuccess count to the NBAJinni/Loader namespace.
# IMPORTANT: the log line text in loader/main.py must match this pattern exactly.
resource "aws_cloudwatch_log_metric_filter" "loader_success" {
  name           = "${var.project_name}-${var.environment}-loader-run-success"
  log_group_name = var.loader_log_group_name
  pattern        = "\"Loader run complete\""

  metric_transformation {
    name          = "LoaderRunSuccess"
    namespace     = "NBAJinni/Loader"
    value         = "1"
    default_value = "0"
  }
}

# CloudWatch dashboard: three widgets covering backend latency, Loader success
# signal, and CloudFront 5xx error rate.
# NOTE: Widget 3 (CloudFront) always queries us-east-1 regardless of var.aws_region
# because CloudFront metrics are only available in us-east-1.
resource "aws_cloudwatch_dashboard" "overview" {
  dashboard_name = "${var.project_name}-${var.environment}-overview"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 8
        height = 6
        properties = {
          title  = "Backend latency (Duration)"
          region = var.aws_region
          view   = "timeSeries"
          period = 300
          metrics = [
            ["AWS/Lambda", "Duration", "FunctionName", var.backend_lambda_name, { stat = "p50" }],
            ["AWS/Lambda", "Duration", "FunctionName", var.backend_lambda_name, { stat = "p90" }],
            ["AWS/Lambda", "Duration", "FunctionName", var.backend_lambda_name, { stat = "p99" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 8
        y      = 0
        width  = 8
        height = 6
        properties = {
          title  = "Loader runs (success signal)"
          region = var.aws_region
          view   = "timeSeries"
          period = 3600
          metrics = [
            ["NBAJinni/Loader", "LoaderRunSuccess", { stat = "Sum" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 16
        y      = 0
        width  = 8
        height = 6
        properties = {
          title  = "CloudFront 5xx error rate"
          region = "us-east-1"
          view   = "timeSeries"
          period = 300
          metrics = [
            ["AWS/CloudFront", "5xxErrorRate", "DistributionId", var.cloudfront_distribution_id, "Region", "Global", { stat = "Average" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 24
        height = 6
        properties = {
          title  = "Ingestion heartbeats per job"
          region = var.aws_region
          view   = "timeSeries"
          period = 3600
          metrics = [
            ["NBAJinni/Ingestion", "IngestionHeartbeat", "JobName", "nightly", { stat = "Sum" }],
            ["NBAJinni/Ingestion", "IngestionHeartbeat", "JobName", "roster", { stat = "Sum" }],
            ["NBAJinni/Ingestion", "IngestionHeartbeat", "JobName", "schedule", { stat = "Sum" }],
            ["NBAJinni/Ingestion", "IngestionHeartbeat", "JobName", "playoff-schedule", { stat = "Sum" }],
          ]
        }
      },
    ]
  })
}
