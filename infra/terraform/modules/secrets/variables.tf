variable "environment" {
  description = "Environment name (e.g., staging)"
  type        = string
}

variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
}

variable "secret_manager_name" {
  description = "The exact name of the secret in AWS Secrets Manager"
  type        = string
}

variable "raw_secrets" {
  description = "JSON-encoded secrets from SOPS"
  type        = string
  sensitive   = true
}

variable "project_name" {
  description = "Project name for tagging"
  type        = string
  default     = "Harmony Chat"
}
