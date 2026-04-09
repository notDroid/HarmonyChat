variable "project_name" {
  description = "The name of the project"
  type        = string
}

variable "environment" {
  description = "The environment name"
  type        = string
}

variable "github_repository_name" {
  description = "The name of the source GitHub repository"
  type        = string
}

variable "ecr_backend_name" {
  description = "The name of the ECR repository for the backend"
  type        = string
}

variable "state_repo_prefix" {
  description = "The prefix for the GitOps state repository"
  type        = string
}

variable "spacelift_space_name" {
  description = "The name of the Spacelift space for PR environments"
  type        = string
}
