output "dynamodb_chat_history_table_name" {
  description = "The name of the chat history DynamoDB table"
  value       = aws_dynamodb_table.chat_history.name
}

output "dynamodb_chat_history_table_arn" {
  description = "The ARN of the chat history DynamoDB table"
  value       = aws_dynamodb_table.chat_history.arn
}

output "s3_automq_data_bucket_name" {
  description = "The generated name of the AutoMQ data S3 bucket"
  value       = aws_s3_bucket.automq["data"].id
}

output "s3_automq_ops_bucket_name" {
  description = "The generated name of the AutoMQ ops S3 bucket"
  value       = aws_s3_bucket.automq["ops"].id
}