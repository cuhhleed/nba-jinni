variable "project_name" {
  description = "Name of the project, used for resource naming and tagging"
  type        = string
}

variable "environment" {
  description = "Deployment environment (dev, prod)"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC to deploy the RDS instance into"
  type        = string
}

variable "subnet_ids" {
  description = "List of private subnet IDs for the DB subnet group"
  type        = list(string)
}

variable "security_group_id" {
  description = "ID of the RDS security group"
  type        = string
}

variable "username" {
  description = "Master username for the RDS PostgreSQL instance"
  type        = string
  sensitive   = true
}

variable "password" {
  description = "Master password for the RDS PostgreSQL instance"
  type        = string
  sensitive   = true
}

variable "instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "engine" {
  description = "Database engine type"
  type        = string
  default     = "postgres"
}

variable "engine_version" {
  description = "Database engine version"
  type        = string
  default     = "15"
}

variable "allocated_storage" {
  description = "Amount of storage in GB to allocate to the RDS instance"
  type        = number
  default     = 20
}



