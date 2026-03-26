variable "environment" {
  description = "Environment name (e.g., staging, production)"
  type        = string
}

variable "project_name" {
  description = "Name of the project for tagging"
  type        = string
  default     = "Harmony Chat"
}

variable "enable_s3_versioning" {
  description = "Toggle to enable/disable S3 versioning (Disabled for staging, enabled for prod)"
  type        = bool
  default     = false
}