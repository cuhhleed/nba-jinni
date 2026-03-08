output "api_endpoint" {
  description = "URI of the API."
  value       = aws_apigatewayv2_api.main.api_endpoint
}
