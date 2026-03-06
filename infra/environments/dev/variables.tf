variable "aws_region" {
  description = "AWS region to deploy resources into"
  type        = string
}

variable "project_name" {
  description = "Name of the project, used for resource naming and tagging"
  type        = string
}

variable "environment" {
  description = "Deployment environment (dev, prod)"
  type        = string
}

variable "db_username" {
  description = "Master username for the RDS PostgreSQL instance"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "Master password for the RDS PostgreSQL instance"
  type        = string
  sensitive   = true
}
