# CI/CD GitOps Migration Plan

## Objective
Migrate the current infrastructure from a push-based model (`task tf:apply`, `task k8s:apply`) to a modern pull-based GitOps CI/CD pipeline using Spacelift, ArgoCD, and a centralized state repository, while supporting multi-account isolation for ephemeral environments.

## Background & Motivation
The current setup relies on local execution of Terraform and Helmfile. Moving to a CI/CD model with GitOps principles increases automation, improves auditing, and ensures environments are ephemeral and reproducible. The goal is to provision fully isolated ephemeral environments (EKS, RDS, Redis) per Pull Request across multiple independent AWS accounts, depending on the user/developer.

## Scope & Impact
- **Terraform:** Transition execution from local Terragrunt wrappers to managed Spacelift stacks. Structure into `bootstrap`, `control-plane`, and `ephemeral` modules.
- **Kubernetes (CD):** Transition from local Helmfile execution to ArgoCD syncing from a state repository.
- **CI/CD:** Introduce GitHub Actions to manage OIDC authentication to multi-account setups and render Helmfiles.
- **State Repository:** Provision a single, centralized state repository via Terraform to hold all ephemeral environment states.

## Proposed Solution

1. **Architecture Layering:**
   - **Bootstrap (`bootstrap/`):** The absolute minimum required to initialize remote state (S3 bucket, DynamoDB lock table). This runs once manually (with local state) per AWS account to establish the foundation.
   - **Control Plane (`control-plane/`):** Uses the remote state established in bootstrap. This provisions shared, long-lived infrastructure per account (ECR Registries, Spacelift integrations) AND provisions the global GitOps State Repository (via the GitHub Terraform provider) if it doesn't exist.
   - **Ephemeral Infrastructure (`environments/ephemeral/`):** Executed by Spacelift per PR. Provisions an EKS cluster, RDS, Redis, and bootstraps ArgoCD.

2. **State Repository Strategy:**
   - **Single Repo vs Multiple:** We will use a **single, centralized state repository** managed by the `control-plane` module. Using a single state repo provides a unified view of all active ephemeral environments and simplifies ArgoCD ApplicationSet configuration. Multiple state repos are generally discouraged unless strict compliance/access boundaries between developers require absolute isolation of manifest visibility.
   - **Provisioning:** The state repo will be automatically provisioned by Terraform in the `control-plane` module, which will also configure necessary webhook secrets and deploy keys for Spacelift/ArgoCD access.

3. **Multi-Account OIDC & Secrets:**
   - Use GitHub Actions with AWS OIDC integration. The CI determines the target AWS account based on the PR author or a label, and assumes the appropriate role.
   - External Secrets Operator (ESO) will continue to manage application secrets, with Spacelift securely injecting the base SOPS keys or AWS Secrets Manager access into the cluster.

4. **GitOps State & Application Delivery:**
   - When a PR is opened, Spacelift provisions the ephemeral infrastructure and ArgoCD points to the state repo's `envs/pr-<id>` directory.
   - GitHub Actions runs `helmfile template` to generate raw Kubernetes manifests for the application stack.
   - The CI commits these manifests to the centralized state repository under `envs/pr-<id>`.
   - ArgoCD syncs the state, pulling in the application workloads and ESO configurations.

5. **Teardown:**
   - Upon PR merge or closure, GitHub Actions triggers a Spacelift destroy operation for the environment.
   - CI removes the `envs/pr-<id>` directory from the state repository.

## Alternatives Considered
- **Shared Cluster with Ephemeral Namespaces:** Faster and cheaper, but rejected in favor of full cluster isolation to maximize parity and prevent cross-contamination.
- **Forking/Independent Repos:** Simpler billing and access control, but rejected in favor of a centralized repository (Multi-Account) to maintain a single source of truth for code and CI/CD pipelines.
- **Manual State Repo Creation:** Rejected. Provisioning the state repo via the `github` Terraform provider ensures consistency, automates deploy key setup, and adheres to Infrastructure as Code principles.

## Implementation Plan

### Phase 1: Bootstrap & Control Plane Setup
1. Define the `bootstrap/` module (S3 + DynamoDB). Run once locally per account.
2. Define the `control-plane/` module to provision ECR, Spacelift configuration, and the unified K8s State Repo (using the GitHub provider). Run once per account (or once globally for the state repo).
3. Ensure SOPS keys and GitHub tokens are available to Spacelift contexts.

### Phase 2: CI/CD Pipeline & OIDC Setup
1. Define GitHub Actions workflows for PR creation and closure.
2. Implement OIDC role assumption logic based on a mapping of GitHub user -> AWS Account ID (stored in GitHub Variables).

### Phase 3: Ephemeral Infrastructure Provisioning
1. Create `environments/ephemeral/` parameterizing Terraform modules (Compute, Stateful, Networking) to suffix resources with the PR ID (e.g., `eks-pr-123`).
2. Add a new Terraform module to install ArgoCD onto the EKS cluster post-creation.
3. Configure ArgoCD via Terraform to target the state repo `envs/pr-<id>` path.

### Phase 4: Application State Management (Helmfile)
1. Add a CI job to run `helmfile template` using the PR-specific values (e.g., dynamic database endpoints).
2. Commit the rendered output to the state repository.
3. Validate ArgoCD successfully syncs and the application becomes healthy.

### Phase 5: Teardown Automation
1. Add a CI job triggered on `pull_request: closed` that deletes the state repo directory.
2. Trigger the Spacelift API to destroy the ephemeral stack and delete it.

## Verification & Testing
- **Control Plane Test:** Verify `control-plane` successfully creates the State Repo and configures deploy keys.
- **Multi-Account Test:** Open a PR from User A and verify it deploys to Account A. Open a PR from User B and verify it deploys to Account B.
- **End-to-End GitOps Test:** Push a commit to an open PR modifying a Kubernetes value. Verify CI updates the state repo and ArgoCD applies the change automatically.
- **Cleanup Test:** Close a PR and verify the EKS cluster, databases, and state repo directory are completely destroyed.

## Migration & Rollback
- The transition is purely additive and ephemeral. Current local commands (`task tf:apply` and `task k8s:apply`) will remain functional for the `local` environment and direct `staging` access.
- If the new pipeline fails, development can fall back to running the existing Terragrunt/Helmfile setup manually.