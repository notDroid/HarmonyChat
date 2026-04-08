resource "aws_secretsmanager_secret" "harmony_secrets" {
  name        = "harmony/${var.environment}/secrets"
  description = "Application secrets for ${var.environment} environment"
  
  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_secretsmanager_secret_version" "harmony_secrets" {
  secret_id     = aws_secretsmanager_secret.harmony_secrets.id
  secret_string = var.raw_secrets
}

# --- IAM for External Secrets Operator (ESO) ---

data "aws_iam_policy_document" "eso_access" {
  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret"
    ]
    resources = [aws_secretsmanager_secret.harmony_secrets.arn]
  }
}

resource "aws_iam_policy" "eso_policy" {
  name        = "harmony-${var.environment}-eso-policy"
  description = "Policy for External Secrets Operator to access Harmony secrets"
  policy      = data.aws_iam_policy_document.eso_access.json
}

data "aws_iam_policy_document" "eso_assume_role" {
  statement {
    effect = "Allow"
    actions = [
      "sts:AssumeRole",
      "sts:TagSession"
    ]
    principals {
      type        = "Service"
      identifiers = ["pods.eks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "eso_role" {
  name               = "harmony-${var.environment}-eso-role"
  assume_role_policy = data.aws_iam_policy_document.eso_assume_role.json
  
  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_iam_role_policy_attachment" "eso_attach" {
  role       = aws_iam_role.eso_role.name
  policy_arn = aws_iam_policy.eso_policy.arn
}

resource "aws_eks_pod_identity_association" "eso_identity" {
  cluster_name    = var.cluster_name
  namespace       = "external-secrets"
  service_account = "external-secrets"
  role_arn        = aws_iam_role.eso_role.arn
}
