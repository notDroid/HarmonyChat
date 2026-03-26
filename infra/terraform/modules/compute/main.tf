module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.31"

  cluster_name    = "harmony-${var.environment}-eks"
  cluster_version = var.cluster_version

  # Cluster endpoint access configuration
  cluster_endpoint_public_access  = true
  cluster_endpoint_private_access = true

  vpc_id     = var.vpc_id
  subnet_ids = var.private_subnet_ids

  # Enable OIDC integration for IRSA
  enable_irsa = true

  # Managed Node Groups
  eks_managed_node_groups = {
    main = {
      min_size     = 1
      max_size     = 3
      desired_size = 2

      instance_types = var.instance_types
      capacity_type  = "ON_DEMAND"

      tags = {
        ExtraTag = "HarmonyWorker"
      }
    }
  }

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
    Project     = "Harmony Chat"
  }
}