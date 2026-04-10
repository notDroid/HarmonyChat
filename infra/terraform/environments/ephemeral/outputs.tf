output "rds_endpoint" {
  description = "The endpoint for the PostgreSQL RDS instance"
  value       = module.stateful.rds_endpoint
}

output "redis_endpoint" {
  description = "The endpoint for the ElastiCache Redis cluster"
  value       = module.stateful.redis_endpoint
}

output "ecr_repository_url" {
  description = "The URL of the ECR repository from Bootstrap"
  value       = data.aws_ecr_repository.backend.repository_url
}