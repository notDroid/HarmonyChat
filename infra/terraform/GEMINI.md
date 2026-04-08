# Terraform Agents Guide

## Stack
- Terraform: `>= 1.5.0`
- AWS Provider: `~> 6.0`
- Terragrunt

## Commands
```bash
# Bootstrap remote state (Run once per AWS account)
task tf:bootstrap

# Infrastructure management
task tf:plan K8S_ENV=<env>
task tf:apply K8S_ENV=<env>
task tf:destroy K8S_ENV=<env>

# Generate outputs for Kubernetes downstream
task tf:output K8S_ENV=<env>
```

## Hard Limits
- **NEVER** run `terraform init`, `plan`, or `apply` directly within `infra/terraform/environments/<env>`. Always use `terragrunt` or the wrapped `task tf:*` commands to ensure state and variable injections are handled correctly.
- **NEVER** commit the generated `tf-outputs.json`. It is a transient artifact used to pass infrastructure coordinates to Helmfile.

## Conventions
- **Dynamic State:** The `root.hcl` dynamically configures the AWS provider and S3 backend state using the caller's AWS Account ID. 
- **Centralized Values:** Terragrunt reads from the global `infra/environments/<env>/values.yaml` and decrypts `secrets.yaml` using SOPS to pass inputs to Terraform. Do not duplicate variable definitions in `.tfvars`.
- **Module Encapsulation:** All resources are encapsulated in `modules/` (e.g., `compute`, `networking`, `stateful`, `storage`). Environments simply stitch these modules together.

## Gotchas
- **Terragrunt Double Slash:** In `environments/<env>/terragrunt.hcl`, the `source = "../..//environments/<env>"` double slash is critical. It forces Terragrunt to cache the entire `infra/terraform` directory, which is necessary for local module resolution.
- **EBS CSI Driver:** The `compute` module automatically creates the necessary IAM roles and IRSA (IAM Roles for Service Accounts) associations for the EBS CSI driver via the EKS module addons.

## Structure Pointers
- `root.hcl`: The parent Terragrunt configuration. Generates `provider.tf` and `backend.tf` automatically.
- `bootstrap/`: Standalone Terraform root module that provisions the S3 state bucket, DynamoDB lock table, and base ECR repository. Run this before anything else.