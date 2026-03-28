output "dynamodb_chat_history_table_arn" {
  description = "The ARN of the chat history DynamoDB table"
  value       = aws_dynamodb_table.chat_history.arn
}