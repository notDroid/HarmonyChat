# CI/CD GitOps Migration Plan

## Objective
Migrate the current infrastructure from a push-based model (`task tf:apply`, `task k8s:apply`) to a modern pull-based GitOps CI/CD pipeline. This leverages Spacelift for dynamic infrastructure provisioning, GitHub Actions for orchestration, and ArgoCD for application delivery, while supporting multi-account isolation and secure SOPS decryption for ephemeral PR environments.

## Architecture & State Strategy

1. **Layered Terraform Architecture:**
   - **Bootstrap (`bootstrap/`):** Initializes remote state (S3 bucket, DynamoDB lock table). Manual, once per account.
   - **Control Plane (`control-plane/`):** Provisions shared, long-lived infrastructure (ECR, Spacelift contexts, IAM roles) and the centralized GitOps State Repository. Manual, once per account.
   - **Ephemeral Template (`environments/ephemeral/`):** A stateless Terraform blueprint. Executed dynamically by Spacelift per PR. Provisions an EKS cluster, RDS, and Redis suffixed with the PR ID to guarantee isolation.

2. **Secrets Management (SOPS + GitOps):**
   - Application secrets remain encrypted in Git via SOPS (`secrets.yaml`).
   - Instead of checking a master key into CI, a scoped, environment-specific AGE key is securely injected into the Spacelift worker environment as `SOPS_AGE_KEY`.
   - Terragrunt seamlessly decrypts secrets during the pipeline run and provisions them into AWS Secrets Manager, preserving the GitOps workflow without compromising production keys.

3. **Orchestration & State Separation:**
   - Terraform strictly handles AWS infrastructure. It **does not** install ArgoCD (avoiding K8s provider chicken-and-egg deadlocks).
   - GitHub Actions handles workflow orchestration: it triggers Spacelift to build the infrastructure, installs ArgoCD via standard CLI tools once the cluster is ready, renders application manifests (`helmfile template`), and pushes them to the state repository.

---

## Implementation Plan

### Phase 1: Bootstrap & Control Plane Setup *(Completed)*
1. Provision the `bootstrap/` module (S3 + DynamoDB) locally per account.
2. Provision the `control-plane/` module (ECR, Spacelift configuration, unified GitOps State Repo, and IAM roles).

### Phase 2: CI/CD Pipeline & OIDC Setup *(Completed)*
1. Define GitHub Actions workflows (`.github/workflows/gitops-pr.yaml`) for PR lifecycle events.
2. Configure OIDC role assumption logic based on GitHub User to AWS Account ID mapping.

### Phase 3: Ephemeral Infrastructure Template & Secrets
*Goal: Create a reusable Terraform template for PRs and secure the decryption pipeline.*

1. **Build the Ephemeral Blueprint:** Create `infra/terraform/environments/ephemeral/`. Configure it to strictly use the `TF_VAR_pr_id` variable to suffix all resources (Cluster Name, DB Name, DynamoDB tables).
2. **Remove K8s Dependencies:** Ensure the Helm and Kubernetes Terraform providers are absent from this module to avoid initial connection failures.
3. **Generate Scoped SOPS Key:** Create a dedicated AGE keypair strictly for PR environments.
4. **Inject Spacelift Secrets:** Add the private AGE key to Spacelift's `ephemeral-pr-context` as a secret environment variable named `SOPS_AGE_KEY`.
5. **Testing & Verification:**
   - *Test:* Trigger a manual Spacelift run pointing to the `ephemeral` directory with `TF_VAR_pr_id` set to `test1`.
   - *Verify:* The EKS cluster and databases provision successfully with the `test1` suffix, and Terragrunt successfully decrypts the SOPS file.

### Phase 4: Dynamic Spacelift Orchestration via CI
*Goal: Automate the creation of dedicated Spacelift stacks for every open PR.*

1. **GHA Orchestration:** Update `.github/workflows/gitops-pr.yaml`. On `pull_request: opened` or `synchronize`, use the Spacelift CLI/API to dynamically create a Stack (e.g., `pr-[ID]-stack`) cloned from the base configuration.
2. **Trigger the Run:** Command Spacelift to trigger a plan/apply for the newly created stack, passing the PR ID dynamically.
3. **Taskfile Integration:** Add a `task pipeline:trigger-spacelift PR_ID=<id>` command to simulate the GHA Spacelift trigger locally.
4. **Testing & Verification:**
   - *Test:* Open a dummy PR.
   - *Verify:* GitHub Actions successfully communicates with Spacelift, creates the dynamic stack, and the infrastructure begins provisioning.

### Phase 5: Application State & GitOps Push
*Goal: Install ArgoCD natively and push rendered manifests to the centralized state repo.*

1. **ArgoCD Bootstrap:** Update the GHA workflow to wait for Spacelift success. Once successful, update the runner's `kubeconfig` to the new EKS cluster and run `helm upgrade --install argocd` to bootstrap the GitOps agent.
2. **Render Manifests:** Execute `task k8s:template K8S_ENV=ephemeral PR_ID=${{ github.event.pull_request.number }}` to generate the raw application configurations.
3. **Push to State Repo:** Clone the centralized State Repository, create the directory `envs/pr-<id>`, move the rendered manifests inside, commit, and push.
4. **Testing & Verification:**
   - *Test:* Push an application configuration change to the open PR.
   - *Verify:* GHA renders the new templates, pushes the commit to the State Repository, and ArgoCD syncs the changes on the ephemeral cluster.

### Phase 6: Automated Teardown & Cleanup
*Goal: Ensure zero orphaned infrastructure or state files upon PR closure.*

1. **State Repo Cleanup:** In the `gitops-pr.yaml` teardown job (`github.event.action == 'closed'`), clone the State Repository, delete the `envs/pr-<id>` directory, and push the deletion commit.
2. **Spacelift Teardown:** Use the Spacelift API to trigger a `Destroy` run for the specific PR's stack.
3. **Stack Deletion:** Once the destroy run completes successfully, issue an API command to delete the Spacelift stack entirely.
4. **Testing & Verification:**
   - *Test:* Close the dummy PR.
   - *Verify:* The State Repository directory is removed, AWS infrastructure is destroyed, and the Spacelift stack no longer exists in the dashboard.

---

## Migration & Rollback
- This GitOps transition is purely additive. Existing local commands (`task tf:apply` and `task k8s:apply`) remain fully functional for the `local` environment and direct `staging` access.
- If the CI/CD pipeline encounters blocking issues, developers can temporarily bypass it by running the Terragrunt and Helmfile commands manually against their assigned AWS account.