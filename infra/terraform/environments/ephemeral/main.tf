terraform {
  required_version = ">= 1.5.0"
  required_providers { aws = { source = "hashicorp/aws", version = "~> 6.0" } }
}

variable "pr_id" { type = string }
variable "project_name" { type = string }
variable "environment" { type = string }
variable "ecr_backend_name" { type = string }
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

variable "secret_manager_name" { type = string }

variable "raw_secrets" {
  type      = string
  sensitive = true
}

data "aws_availability_zones" "available" {
  state = "available"
}

module "networking" {
  source       = "../../modules/networking"
  vpc_name     = "harmony-${var.environment}-pr-${var.pr_id}-vpc"
  environment  = "${var.environment}-pr-${var.pr_id}"
  project_name = var.project_name
  vpc_cidr     = var.vpc_cidr
  azs          = slice(data.aws_availability_zones.available.names, 0, var.azs_count)
  cluster_name = "pr-${var.pr_id}-eks"
}

module "secrets" {
  source              = "../../modules/secrets"
  environment         = "${var.environment}-pr-${var.pr_id}"
  cluster_name        = "pr-${var.pr_id}-eks"
  secret_manager_name = "${var.secret_manager_name}-pr-${var.pr_id}"
  raw_secrets         = var.raw_secrets
  project_name        = var.project_name
}

module "stateful" {
  source                     = "../../modules/stateful"
  environment                = "${var.environment}-pr-${var.pr_id}"
  project_name               = var.project_name
  vpc_id                     = module.networking.vpc_id
  database_subnet_group_name = module.networking.database_subnet_group_name
  database_subnet_ids        = module.networking.database_subnet_ids
  private_subnet_cidrs       = module.networking.private_subnets_cidr_blocks

  db_name              = "${var.db_name}_pr_${var.pr_id}"
  db_username          = var.db_user
  db_password          = var.db_password
  db_instance_class    = var.db_instance_class
  db_allocated_storage = var.db_allocated_storage
  redis_node_type      = var.redis_node_type
}

module "storage" {
  source                  = "../../modules/storage"
  environment             = "${var.environment}-pr-${var.pr_id}"
  project_name            = var.project_name
  chat_history_table_name = "${var.chat_history_table_name}_pr_${var.pr_id}"
  automq_data_bucket_name = "${var.automq_data_bucket_name}-pr-${var.pr_id}"
  automq_ops_bucket_name  = "${var.automq_ops_bucket_name}-pr-${var.pr_id}"
}

module "compute" {
  source             = "../../modules/compute"
  environment        = "${var.environment}-pr-${var.pr_id}"
  project_name       = var.project_name
  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  cluster_name       = "pr-${var.pr_id}-eks"
  cluster_version    = var.cluster_version
}

data "aws_ecr_repository" "backend" {
  name = var.ecr_backend_name
}