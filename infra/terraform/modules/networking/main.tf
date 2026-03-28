locals {
  public_subnets   = [for k, v in var.azs : cidrsubnet(var.vpc_cidr, 8, k + 1)]
  private_subnets  = [for k, v in var.azs : cidrsubnet(var.vpc_cidr, 8, k + 11)]
  database_subnets = [for k, v in var.azs : cidrsubnet(var.vpc_cidr, 8, k + 21)]
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = var.vpc_name
  cidr = var.vpc_cidr

  azs                          = var.azs
  public_subnets               = local.public_subnets
  private_subnets              = local.private_subnets
  database_subnets             = local.database_subnets
  create_database_subnet_group = true

  enable_dns_hostnames = true
  enable_dns_support   = true

  enable_nat_gateway     = true
  single_nat_gateway     = true
  one_nat_gateway_per_az = false

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
    Project     = "Harmony Chat"
  }
}