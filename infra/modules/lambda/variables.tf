variable "project_name" {
  description = "Name of the project, used for resource naming and tagging"
  type        = string
}

variable "environment" {
  description = "Deployment environment (dev, prod)"
  type        = string
}

variable "function_name" {
  description = "The name of the Lambda function."
  type        = string
}

variable "role" {
  description = "The IAM execution role to be used by the Lambda function."
  type        = string
}

variable "handler" {
  description = "The function entry point in your code."
  type        = string
}

variable "timeout" {
  description = "Amount of time your Lambda Function has to run in seconds."
  type        = number
  default     = 30
}

variable "security_group_ids" {
  description = "List of security group IDs associated with the Lambda function."
  type        = list(string)
}

variable "subnet_ids" {
  description = "List of subnet IDs associated with the Lambda function."
  type        = list(string)
}

variable "environment_variables" {
  description = "Environment variables to be utilized by the Lambda function."
  type        = map(string)
  default     = {}
}

variable "memory_size" {
  description = "Amount of memory in MB your Lambda Function can use at runtime."
  type        = number
  default     = 128
}

variable "filename" {
  description = "Path to the function's deployment package within the local filesystem."
  type        = string
}
