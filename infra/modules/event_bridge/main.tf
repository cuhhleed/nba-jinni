resource "aws_cloudwatch_event_rule" "main" {
  name                = "${var.project_name}-${var.environment}-${var.rule_name}"
  schedule_expression = var.schedule_expression
}

resource "aws_cloudwatch_event_target" "event_target" {
  arn  = var.lambda_arn
  rule = aws_cloudwatch_event_rule.main.name
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_arn
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.main.arn
}
