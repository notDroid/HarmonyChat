output "rds_endpoint" {
  description = "The connection endpoint for the RDS PostgreSQL instance"
  value       = aws_db_instance.postgres.endpoint
}

output "rds_port" {
  description = "The port the RDS instance is listening on"
  value       = aws_db_instance.postgres.port
}

output "redis_endpoint" {
  description = "The connection endpoint for the Redis cluster"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
}

output "redis_port" {
  description = "The port the Redis cluster is listening on"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].port
}