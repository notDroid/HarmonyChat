locals {
  common_tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
    Project     = var.project_name
  }
}

# ==============================================================================
# Security Groups
# ==============================================================================

# PostgreSQL Security Group
resource "aws_security_group" "rds" {
  name        = "harmony-${var.environment}-rds-sg"
  description = "Allow PostgreSQL inbound traffic from private subnets only"
  vpc_id      = var.vpc_id

  ingress {
    description = "PostgreSQL access from private compute subnets"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = var.private_subnet_cidrs
  }

  tags = merge(local.common_tags, {
    Name = "harmony-${var.environment}-rds-sg"
  })
}

# Redis Security Group
resource "aws_security_group" "redis" {
  name        = "harmony-${var.environment}-redis-sg"
  description = "Allow Redis inbound traffic from private subnets only"
  vpc_id      = var.vpc_id

  ingress {
    description = "Redis access from private compute subnets"
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = var.private_subnet_cidrs
  }

  tags = merge(local.common_tags, {
    Name = "harmony-${var.environment}-redis-sg"
  })
}

# ==============================================================================
# Relational Database (PostgreSQL)
# ==============================================================================

resource "aws_db_instance" "postgres" {
  identifier     = "harmony-${var.environment}-postgres"
  engine         = "postgres"
  engine_version = "15"

  instance_class    = var.db_instance_class
  allocated_storage = var.db_allocated_storage

  storage_type = "gp3"
  db_name      = var.db_name
  username     = var.db_username
  password     = var.db_password

  # Network & Security
  db_subnet_group_name   = var.database_subnet_group_name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false
  multi_az               = false # Keep it simple for staging, consider multi-AZ for production

  # Backups & Maintenance (keep it simple for staging, maybe adjust for production)
  skip_final_snapshot     = true
  deletion_protection     = false
  backup_retention_period = 0

  tags = local.common_tags
}

# ==============================================================================
# In-Memory Cache (Redis)
# ==============================================================================

resource "aws_elasticache_subnet_group" "redis" {
  name       = "harmony-${var.environment}-redis-subnet-group"
  subnet_ids = var.database_subnet_ids

  description = "Subnet group for Harmony Redis cache"

  tags = local.common_tags
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id     = "harmony-${var.environment}-redis"
  engine         = "redis"
  engine_version = "7.0"

  node_type = var.redis_node_type

  num_cache_nodes = 1
  port            = 6379

  subnet_group_name  = aws_elasticache_subnet_group.redis.name
  security_group_ids = [aws_security_group.redis.id]

  tags = local.common_tags
}