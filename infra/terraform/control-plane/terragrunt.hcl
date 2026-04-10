include "root" {
  path = find_in_parent_folders("root.hcl")
}

terraform {
  # The double slash (//) is critical. It tells Terragrunt to copy the entire 
  # 'infra/terraform' folder to the cache, then execute from 'control-plane'
  source = "..//control-plane"
}

locals {
  values = yamldecode(templatefile("${get_repo_root()}/infra/environments/control-plane/values.yaml", {
    AWS_ACCOUNT_ID = get_aws_account_id()
  }))
  ephemeral_secrets = yamldecode(sops_decrypt_file("${get_repo_root()}/infra/environments/ephemeral/secrets.yaml"))
  
  env = local.values.environment
}

generate "spacelift_provider" {
  path      = "provider_spacelift.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
provider "spacelift" {
  api_key_endpoint = "${local.ephemeral_secrets.secrets.spacelift.api_key_endpoint}"
  api_key_id       = "${local.ephemeral_secrets.secrets.spacelift.api_key_id}"
  api_key_secret   = "${local.ephemeral_secrets.secrets.spacelift.api_key_secret}"
}
EOF
}

inputs = {
  # --- Global ---
  project_name = local.values.project_name
  environment  = local.env

  # --- Naming ---
  github_repository_name = local.values.infra.github.repository_name
  ecr_backend_name       = local.values.infra.naming.ecr_backend_name
  state_repo_prefix      = local.values.infra.naming.state_repo_prefix
  spacelift_space_name   = local.values.infra.naming.spacelift_space_name
}