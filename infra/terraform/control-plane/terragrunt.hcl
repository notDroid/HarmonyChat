include "root" {
  path = find_in_parent_folders("root.hcl")
}

terraform {
  # The double slash (//) is critical. It tells Terragrunt to copy the entire 
  # 'infra/terraform' folder to the cache, then execute from 'control-plane'
  source = "../..//control-plane"
}

locals {
  values = yamldecode(templatefile("${get_repo_root()}/infra/environments/control-plane/values.yaml", {
    AWS_ACCOUNT_ID = get_aws_account_id()
  }))
  
  env = local.values.environment
}

inputs = {
  # --- Global ---
  project_name = local.values.project_name
  environment  = local.env
}