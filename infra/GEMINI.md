# Infrastructure Agents Guide

*Note: For granular specifics, check for or create `AGENTS.md` in `infra/k8s/` and `infra/terraform/`.*

## Stack
- Terraform: `>= 1.5.0` (AWS Provider `~> 6.0`)
- Terragrunt
- Kubernetes: `1.35`
- Helm & Helmfile
- SOPS: `3.12.2` (age-based)

## Commands
```bash
# Local Dev
task run         # Starts docker-compose environment
task kind:setup  # Bootstraps local k8s cluster via kind
task clean       # Tears down docker-compose

# Terraform (via Terragrunt)
task tf:plan K8S_ENV=staging
task tf:apply K8S_ENV=staging

# Kubernetes (Helmfile)
task k8s:apply K8S_ENV=staging

# Deployment
task deploy K8S_ENV=staging
```

## Hard Limits
- **NEVER** commit unencrypted secrets. Always encrypt with SOPS (`task secrets:encrypt K8S_ENV=<env>`).
- **NEVER** run `terraform` directly in `infra/terraform/environments/*`. Always use `terragrunt` or the `task tf:*` wrappers.

## Conventions
- **Config Rendering:** Docker-compose relies on `infra/scripts/render_config.py` to generate `.env` and JSON configs from `docker/config.yaml` using Jinja2 (`.j2`) templates. Do not edit generated configs directly.
- **Helmfile Templates:** K8s values pull heavily from `infra/k8s/environments/base/values/*.yaml.gotmpl`.
- **Terraform/Terragrunt:** Terragrunt passes variables into Terraform by parsing the shared `infra/environments/<env>/values.yaml`.

## Gotchas
- **Terragrunt Double Slash:** `terragrunt.hcl` uses a double slash (`../..//environments/<env>`) to cache the entire `infra/terraform` directory. Do not remove it.
- **Helm/Terraform Coupling:** K8s remote deployments depend on `tf-outputs.json` (generated via `task tf:output`) to resolve RDS, Redis, and ECR endpoints dynamically.
- **AutoMQ S3 Dependency:** AutoMQ Kafka requires `automq-data` and `automq-ops` S3 buckets to be provisioned (via Terraform or local Minio script) *before* deployment.

## Structure Pointers
- `infra/environments/<env>/`: Source of truth for environment-specific variables and SOPS secrets. Both Helm and Terragrunt read from here.
- `infra/terraform/environments/<env>/`: Holds Terragrunt entrypoints, not the raw variables.
- `infra/docker/templates/`: Jinja2 `.j2` templates that generate the final docker configs and env files.
