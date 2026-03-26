module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  # VPC
  name = var.vpc_name
  cidr = var.vpc_cidr

  # Subnets and AZs
  azs                          = var.azs
  public_subnets               = var.public_subnets
  private_subnets              = var.private_subnets
  database_subnets             = var.database_subnets
  create_database_subnet_group = true

  # DNS
  enable_dns_hostnames = true
  enable_dns_support   = true

  # NAT Gateway Configuration
  enable_nat_gateway     = true
  single_nat_gateway     = true
  one_nat_gateway_per_az = false

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
    Project     = "Harmony Chat"
  }
}