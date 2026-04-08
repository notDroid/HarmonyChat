output "secret_arn" {
  description = "ARN of the Secrets Manager secret"
  value       = aws_secretsmanager_secret.harmony_secrets.arn
}

output "eso_role_arn" {
  description = "ARN of the IAM role for External Secrets Operator"
  value       = aws_iam_role.eso_role.arn
}
