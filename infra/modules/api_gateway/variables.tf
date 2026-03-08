variable "project_name" {
  description = "Name of the project, used for resource naming and tagging."
  type        = string
}

variable "environment" {
  description = "Deployment environment (dev, prod)."
  type        = string
}

# Main API Gateway resource
variable "protocol_type" {
  description = "API protocol. Valid values: HTTP, WEBSOCKET."
  type        = string
  default     = "HTTP"
}

# API Gateway Integration resource
variable "integration_type" {
  description = "Integration type of an integration."
  type        = string
  default     = "AWS_PROXY"
}

variable "lambda_invoke_arn" {
  description = "Invoke ARN (integration URI) for Lambda function to attach to integration."
  type        = string
}

# API Gateway route resource
variable "gateway_route" {
  description = "Route key for the route."
  type        = string
  default     = "ANY /{proxy+}"
}

# API Gateway Lambda permission resource

variable "lambda_arn" {
  description = "ARN for Lambda function to give permission on."
  type        = string
}

