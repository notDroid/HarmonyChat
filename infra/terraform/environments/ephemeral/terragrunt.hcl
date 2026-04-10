include "root" {
  path = find_in_parent_folders("root.hcl")
}

terraform {
  source = "../..//environments/ephemeral"
}

locals {
  # Reuse staging values for the ephemeral environment baseline
  values = yamldecode(templatefile("${get_repo_root()}/infra/environments/ephemeral/values.yaml", {
    AWS_ACCOUNT_ID = get_aws_account_id()
  }))
  secrets = yamldecode(sops_decrypt_file("${get_repo_root()}/infra/environments/ephemeral/secrets.yaml"))
  control_plane_values = yamldecode(file("${get_repo_root()}/infra/environments/control-plane/values.yaml"))
  
  env = "ephemeral"
}

inputs = {
  pr_id = get_env("TF_VAR_pr_id")

  # --- Global ---
  project_name     = local.values.project_name
  environment      = local.env
  ecr_backend_name = local.control_plane_values.infra.naming.ecr_backend_name

  # --- Networking ---
  vpc_cidr  = local.values.infra.vpc.cidr
  azs_count = local.values.infra.vpc.azs_count

  # --- Compute (EKS) ---
  cluster_name    = local.values.infra.compute.cluster_name
  cluster_version = local.values.infra.compute.cluster_version

  # --- Databases ---
  db_name              = local.values.infra.postgres.dbname
  db_user              = local.values.infra.postgres.user
  db_password          = local.secrets.secrets.postgres.password
  db_instance_class    = local.values.infra.postgres.instance_class
  db_allocated_storage = local.values.infra.postgres.allocated_storage_gb
  
  redis_node_type      = local.values.infra.redis.node_type

  # --- Storage ---
  chat_history_table_name = local.values.infra.dynamodb.chat_history_table_name

  automq_data_bucket_name = local.values.infra.s3.buckets.automq_data
  automq_ops_bucket_name  = local.values.infra.s3.buckets.automq_ops

  secret_manager_name = local.values.infra.secrets.manager_name
  raw_secrets         = jsonencode(local.secrets.secrets)
}
