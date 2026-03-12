resource "aws_security_group" "main" {
  name   = "${var.project_name}-${var.environment}-${var.sg_name}"
  vpc_id = var.vpc_id

  dynamic "ingress" {
    for_each = var.ingress_rules
    content {
      from_port       = ingress.value.from_port
      to_port         = coalesce(ingress.value.to_port, ingress.value.from_port)
      protocol        = ingress.value.protocol
      cidr_blocks     = ingress.value.cidr_blocks
      security_groups = ingress.value.security_groups
      description     = ingress.value.description
    }
  }

  dynamic "egress" {
    for_each = var.egress_rules
    content {
      from_port       = egress.value.from_port
      to_port         = coalesce(egress.value.to_port, egress.value.from_port)
      protocol        = egress.value.protocol
      cidr_blocks     = egress.value.cidr_blocks
      security_groups = egress.value.security_groups
      description     = egress.value.description
    }
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-${var.sg_name}"
  }

  lifecycle {
    create_before_destroy = true
  }
}
