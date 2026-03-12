# NOTE: prevent_destroy is set on foundational network resources.
# For a full teardown, temporarily remove these lifecycle blocks before running terraform destroy.

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  instance_tenancy     = "default"
  enable_dns_hostnames = var.enable_dns_hostnames
  enable_dns_support   = var.enable_dns_support

  tags = {
    Name = "${var.project_name}-${var.environment}-VPC"
  }

  lifecycle {
    prevent_destroy = true
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_subnet" "public_1" {
  availability_zone       = data.aws_availability_zones.available.names[0]
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, 1)
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-${var.environment}-public-subnet-1"
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_subnet" "private_1" {
  availability_zone = data.aws_availability_zones.available.names[0]
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, 2)

  tags = {
    Name = "${var.project_name}-${var.environment}-private-subnet-1"
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_subnet" "public_2" {
  availability_zone       = data.aws_availability_zones.available.names[1]
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, 3)
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-${var.environment}-public-subnet-2"
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_subnet" "private_2" {
  availability_zone = data.aws_availability_zones.available.names[1]
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, 4)

  tags = {
    Name = "${var.project_name}-${var.environment}-private-subnet-2"
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-${var.environment}-IGW"
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_route_table" "public_route_table" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-public-RT"
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_route_table" "private_route_table" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-${var.environment}-private-RT"
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_route_table_association" "public_association_1" {
  subnet_id      = aws_subnet.public_1.id
  route_table_id = aws_route_table.public_route_table.id
}

resource "aws_route_table_association" "public_association_2" {
  subnet_id      = aws_subnet.public_2.id
  route_table_id = aws_route_table.public_route_table.id
}

resource "aws_route_table_association" "private_association_1" {
  subnet_id      = aws_subnet.private_1.id
  route_table_id = aws_route_table.private_route_table.id
}

resource "aws_route_table_association" "private_association_2" {
  subnet_id      = aws_subnet.private_2.id
  route_table_id = aws_route_table.private_route_table.id
}

# initialize default security group with no rules to secure fallback
resource "aws_default_security_group" "default" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-${var.environment}-default-sg"
  }
}
