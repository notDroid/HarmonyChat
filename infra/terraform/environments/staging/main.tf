terraform {
  required_version = ">= 1.5.0"

  backend "s3" {
    bucket         = "harmony-chat-tf-state"
    key            = "staging/networking/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "harmony-chat-tf-locks"
    encrypt        = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# Generate a secure random password for PostgreSQL
resource "random_password" "db_password" {
  length           = 16
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# Fetch AZs
data "aws_availability_zones" "available" {
  state = "available"
}

# VPC CIDRs
locals {
  vpc_cidr         = "10.0.0.0/16"
  public_subnets   = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  private_subnets  = ["10.0.10.0/24", "10.0.11.0/24", "10.0.12.0/24"]
  database_subnets = ["10.0.20.0/24", "10.0.21.0/24", "10.0.22.0/24"]
}

module "networking" {
  source = "../../modules/networking"

  vpc_name         = "harmony-staging-vpc"
  environment      = "staging"
  vpc_cidr         = local.vpc_cidr
  azs              = slice(data.aws_availability_zones.available.names, 0, 3)
  public_subnets   = local.public_subnets
  private_subnets  = local.private_subnets
  database_subnets = local.database_subnets
}

module "stateful" {
  source = "../../modules/stateful"

  environment = "staging"
  vpc_id      = module.networking.vpc_id

  database_subnet_group_name = module.networking.database_subnet_group_name
  database_subnet_ids        = module.networking.database_subnet_ids

  private_subnet_cidrs = local.private_subnets

  db_password = random_password.db_password.result
}

module "storage" {
  source = "../../modules/storage"

  environment          = "staging"
  project_name         = "Harmony Chat"
  enable_s3_versioning = false
}

module "compute" {
  source = "../../modules/compute"

  environment        = "staging"
  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  
  cluster_version = "1.35"
  instance_types  = ["t3.large"]
}