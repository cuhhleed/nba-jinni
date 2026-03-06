resource "aws_db_instance" "main" {
  allocated_storage      = var.allocated_storage
  db_name                = "${var.project_name}_${var.environment}_db"
  engine                 = var.engine
  engine_version         = var.engine_version
  instance_class         = var.instance_class
  username               = var.username
  password               = var.password
  db_subnet_group_name   = aws_db_subnet_group.rds_subnet_group.name
  vpc_security_group_ids = [var.security_group_id]
  skip_final_snapshot    = true
  publicly_accessible    = false
  multi_az               = false

  tags = {
    Name = "${var.project_name}-${var.environment}-DB"
  }
}

resource "aws_db_subnet_group" "rds_subnet_group" {
  name       = "${var.project_name}-${var.environment}-db-subnet-group"
  subnet_ids = var.subnet_ids

  tags = {
    Name = "${var.project_name}-${var.environment}-DB-subnet-group"
  }

}