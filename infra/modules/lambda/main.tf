resource "aws_cloudwatch_log_group" "lambda_log" {
  name              = "/aws/lambda/${var.function_name}-logs"
  retention_in_days = 14

  tags = {
    Name = "${var.project_name}-${var.environment}-${var.function_name}-logs"
  }
}

resource "aws_lambda_function" "main" {
  filename         = var.filename
  function_name    = var.function_name
  role             = var.role
  runtime          = "python3.12"
  handler          = var.handler
  memory_size      = var.memory_size
  timeout          = var.timeout
  source_code_hash = filebase64sha256(var.filename)

  # Advanced logging configuration
  logging_config {
    log_format            = "JSON"
    application_log_level = "INFO"
    system_log_level      = "WARN"
  }

  vpc_config {
    subnet_ids         = var.subnet_ids
    security_group_ids = var.security_group_ids
  }

  environment {
    variables = var.environment_variables
  }

  # Ensure log group exists before function
  depends_on = [aws_cloudwatch_log_group.lambda_log]

  tags = {
    Name = "${var.project_name}-${var.environment}-${var.function_name}"
  }
}
