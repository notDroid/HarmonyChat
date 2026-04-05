variable "environment" { type = string }
variable "project_name" {
  type    = string
  default = "Harmony Chat"
}
variable "enable_s3_versioning" {
  type    = bool
  default = false
}

variable "chat_history_table_name" {
  description = "The exact name of the DynamoDB table"
  type        = string
}

variable "automq_data_bucket_name" {
  description = "The exact name of the AutoMQ Data bucket"
  type        = string
}

variable "automq_ops_bucket_name" {
  description = "The exact name of the AutoMQ Ops bucket"
  type        = string
}