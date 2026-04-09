data "aws_caller_identity" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
}

# ------------------------------------------------------------------------------
# ECR Repository for Backend Image
# ------------------------------------------------------------------------------
resource "aws_ecr_repository" "backend" {
  name                 = "harmony-backend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

# ------------------------------------------------------------------------------
# GitOps State Repository
# ------------------------------------------------------------------------------
resource "github_repository" "state_repo" {
  name        = "harmony-chat-state-${local.account_id}"
  description = "GitOps state repository for ArgoCD (Managed by Terraform)"
  visibility  = "private"
  auto_init   = true
}

# ------------------------------------------------------------------------------
# Spacelift & GitHub Actions IAM Integration
# ------------------------------------------------------------------------------
# OIDC Provider for GitHub Actions
resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"] # Standard GitHub Actions thumbprint
}

# OIDC Provider for Spacelift (replace the thumbprint and url for production setup)
# For the plan we define it as placeholder.
resource "aws_iam_openid_connect_provider" "spacelift" {
  url             = "https://spacelift.io"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["9e99a48a9960b14926bb7f3b02e22da2b0ab7280"]
}

resource "aws_iam_role" "spacelift_provisioner" {
  name = "SpaceliftProvisionerRole-${local.account_id}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Federated = aws_iam_openid_connect_provider.spacelift.arn
        },
        Action = "sts:AssumeRoleWithWebIdentity",
        Condition = {
          "StringLike" = {
            "spacelift.io:sub" = "space:*"
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "spacelift_admin" {
  role       = aws_iam_role.spacelift_provisioner.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}

# ------------------------------------------------------------------------------
# Spacelift Baseline
# ------------------------------------------------------------------------------
resource "spacelift_space" "harmony_ephemeral" {
  name        = "Harmony Ephemeral PRs"
  description = "Space containing all ephemeral PR environments"
}
