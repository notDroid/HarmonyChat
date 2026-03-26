variable "environment" {
  description = "Environment name (e.g., staging, production)"
  type        = string
}

variable "vpc_id" {
  description = "The ID of the VPC where the security groups will be created"
  type        = string
}

variable "private_subnet_cidrs" {
  description = "List of private subnet CIDR blocks allowed to access the databases"
  type        = list(string)
}

variable "database_subnet_group_name" {
  description = "Name of the RDS database subnet group created by the networking module"
  type        = string
}

variable "database_subnet_ids" {
  description = "List of database subnet IDs for the ElastiCache subnet group"
  type        = list(string)
}

variable "db_name" {
  description = "Name of the initial PostgreSQL database"
  type        = string
  default     = "harmony"
}

variable "db_username" {
  description = "Master username for PostgreSQL"
  type        = string
  default     = "harmony_admin"
}

variable "db_password" {
  description = "Master password for PostgreSQL"
  type        = string
  sensitive   = true
}