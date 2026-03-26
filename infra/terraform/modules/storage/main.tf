resource "random_string" "s3_suffix" {
  length  = 8
  special = false
  upper   = false
}

# ------------------------------------------------------------------------------
# DynamoDB Table
# ------------------------------------------------------------------------------
resource "aws_dynamodb_table" "chat_history" {
  name         = "harmony_${var.environment}_chat_history"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "chat_id"
  range_key    = "message_id"

  attribute {
    name = "chat_id"
    type = "S"
  }

  attribute {
    name = "message_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
    Project     = var.project_name
  }
}

# ------------------------------------------------------------------------------
# S3 Buckets
# ------------------------------------------------------------------------------
locals {
  automq_buckets = {
    data = "harmony-automq-data-${var.environment}-${random_string.s3_suffix.result}"
    ops  = "harmony-automq-ops-${var.environment}-${random_string.s3_suffix.result}"
  }
}

resource "aws_s3_bucket" "automq" {
  for_each = local.automq_buckets
  bucket   = each.value

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
    Project     = var.project_name
  }
}

# Block all public access for both buckets
resource "aws_s3_bucket_public_access_block" "automq_access" {
  for_each = aws_s3_bucket.automq

  bucket                  = each.value.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable SSE-S3 encryption by default for both buckets
resource "aws_s3_bucket_server_side_encryption_configuration" "automq_encryption" {
  for_each = aws_s3_bucket.automq

  bucket = each.value.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Control versioning based on the environment toggle
resource "aws_s3_bucket_versioning" "automq_versioning" {
  for_each = aws_s3_bucket.automq

  bucket = each.value.id
  versioning_configuration {
    status = var.enable_s3_versioning ? "Enabled" : "Suspended"
  }
}