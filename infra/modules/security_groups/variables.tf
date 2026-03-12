variable "environment" {
  description = "Deployment environment (dev, prod)"
  type        = string
}

variable "project_name" {
  description = "Name of the project, used for resource naming and tagging"
  type        = string
}

variable "sg_name" {
  description = "Name of the security group"
}

variable "vpc_id" {
  description = "The ID of the VPC to associate the security group with"
  type        = string
}

variable "ingress_rules" {
  type = list(object({
    from_port       = number
    to_port         = optional(number, null)
    protocol        = optional(string, "tcp")
    cidr_blocks     = optional(list(string), [])
    security_groups = optional(list(string), [])
    description     = optional(string, "")
  }))
  default = []
}

variable "egress_rules" {
  type = list(object({
    from_port       = number
    to_port         = optional(number, null)
    protocol        = optional(string, "tcp")
    cidr_blocks     = optional(list(string), ["0.0.0.0/0"])
    security_groups = optional(list(string), [])
    description     = optional(string, "")
  }))
  default = []
}

