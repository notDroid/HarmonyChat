terraform {
  required_version = ">= 1.5.0"
  required_providers { aws = { source = "hashicorp/aws", version = "~> 6.0" } }
}

# Variables mapped from Terragrunt
variable "project_name" { type = string }
variable "environment" { type = string }
variable "vpc_cidr" { type = string }
variable "azs_count" { type = number }

variable "cluster_name" { type = string }
variable "cluster_version" { type = string }

variable "db_name" { type = string }
variable "db_user" { type = string }
variable "db_password" {
  type      = string
  sensitive = true
}
variable "db_instance_class" { type = string }
variable "db_allocated_storage" { type = number }

variable "redis_node_type" { type = string }

variable "chat_history_table_name" { type = string }
variable "automq_data_bucket_name" { type = string }
variable "automq_ops_bucket_name" { type = string }

data "aws_availability_zones" "available" {
  state = "available"
}

module "networking" {
  source       = "../../modules/networking"
  vpc_name     = "harmony-${var.environment}-vpc"
  environment  = var.environment
  vpc_cidr     = var.vpc_cidr
  azs          = slice(data.aws_availability_zones.available.names, 0, var.azs_count)
  cluster_name = var.cluster_name
}

module "stateful" {
  source                     = "../../modules/stateful"
  environment                = var.environment
  vpc_id                     = module.networking.vpc_id
  database_subnet_group_name = module.networking.database_subnet_group_name
  database_subnet_ids        = module.networking.database_subnet_ids
  private_subnet_cidrs       = module.networking.private_subnets_cidr_blocks

  db_name              = var.db_name
  db_username          = var.db_user
  db_password          = var.db_password
  db_instance_class    = var.db_instance_class
  db_allocated_storage = var.db_allocated_storage
  redis_node_type      = var.redis_node_type
}

module "storage" {
  source                  = "../../modules/storage"
  environment             = var.environment
  project_name            = var.project_name
  chat_history_table_name = var.chat_history_table_name
  automq_data_bucket_name = var.automq_data_bucket_name
  automq_ops_bucket_name  = var.automq_ops_bucket_name
}

module "compute" {
  source             = "../../modules/compute"
  environment        = var.environment
  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  cluster_name       = var.cluster_name
  cluster_version    = var.cluster_version
}

data "aws_ecr_repository" "backend" {
  name = "harmony-backend"
}