variable "aws_region" {
  description = "AWS region to deploy resources into"
  type        = string
}

variable "environment" {
  description = "Deployment environment (dev, prod)"
  type        = string
}

variable "project_name" {
  description = "Name of the project, used for resource naming and tagging"
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR range for the VPC resource to cover"
  type        = string
  default     = "10.0.0.0/16"
}

variable "enable_dns_support" {
  description = "Whether or not DNS support should be enabled in this VPC"
  type        = bool
  default     = true
}

variable "enable_dns_hostnames" {
  description = "Whether or not DNS hostnames should be enabled in this VPC"
  type        = bool
  default     = true
}