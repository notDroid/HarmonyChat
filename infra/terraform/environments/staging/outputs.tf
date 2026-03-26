output "chat_history_table_name" {
  description = "The DynamoDB table name for Chat History"
  value       = module.storage.dynamodb_chat_history_table_name
}

output "automq_data_bucket_name" {
  description = "The globally unique S3 bucket name for AutoMQ Data"
  value       = module.storage.s3_automq_data_bucket_name
}

output "automq_ops_bucket_name" {
  description = "The globally unique S3 bucket name for AutoMQ Ops"
  value       = module.storage.s3_automq_ops_bucket_name
}

output "eks_cluster_name" {
  description = "The name of the staging EKS cluster"
  value       = module.compute.cluster_name
}