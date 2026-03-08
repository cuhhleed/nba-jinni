resource "aws_apigatewayv2_api" "main" {
  name          = "${var.project_name}-${var.environment}-request-api-gateway"
  protocol_type = var.protocol_type

  tags = {
    Name = "${var.project_name}-${var.environment}-request-api-gateway"
  }
}

resource "aws_apigatewayv2_integration" "api_gateway_integration" {
  integration_uri  = var.lambda_invoke_arn
  integration_type = var.integration_type
  api_id           = aws_apigatewayv2_api.main.id
}

resource "aws_apigatewayv2_route" "api_gateway_route" {
  api_id    = aws_apigatewayv2_api.main.id
  target    = "integrations/${aws_apigatewayv2_integration.api_gateway_integration.id}"
  route_key = var.gateway_route
}

resource "aws_apigatewayv2_stage" "api_gateway_stage" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "$default"
  auto_deploy = true

  tags = {
    Name = "${aws_apigatewayv2_api.main.name}-stage"
  }
}

resource "aws_lambda_permission" "lambda_permission" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_arn
  principal     = "apigateway.amazonaws.com"

  # The /* part allows invocation from any stage, method and resource path
  # within API Gateway.
  source_arn = "${aws_apigatewayv2_api.main.execution_arn}/*"
}
