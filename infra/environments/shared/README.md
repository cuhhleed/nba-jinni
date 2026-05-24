# infra/environments/shared

## Purpose

This environment is the **CI bootstrap** for the nba-jinni project. It provisions account-wide infrastructure that all GitHub Actions workflows depend on before they can deploy anything:

- One AWS IAM OIDC Identity Provider (`token.actions.githubusercontent.com`)
- Two IAM roles with tightened deploy permissions: `nbajinni-dev-github-actions-role` and `nbajinni-prod-github-actions-role`
- Two GitHub Environments (`dev`, `prod`) with appropriate approval gates
- Four environment-scoped GitHub Actions secrets: `AWS_ROLE_ARN` and `AWS_REGION` on each environment

## Why separate state from dev/prod app environments

The dev and prod app environments manage application infrastructure (VPC, RDS, Lambda, S3, CloudFront). Their state files change every time an app env is updated.

The shared env manages account-level and GitHub-side resources that exist independently of any app deployment. Keeping it in its own state file (`environments/shared/terraform.tfstate`) means:

- An apply on dev cannot accidentally touch the OIDC provider or GitHub secrets.
- The shared env can be applied once and left stable while app envs iterate.
- Destroying a dev or prod app env does not destroy the OIDC provider or GitHub Environments.

## Prerequisites

1. **AWS CLI** authenticated as a principal with rights to create IAM resources and OIDC providers (the same principal used to apply the dev env is sufficient).

2. **`GITHUB_TOKEN` env var** set to a fine-grained Personal Access Token. See "Creating the PAT" below.

## Creating the PAT

Go to GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token.

Required settings:

| Setting | Value |
|---|---|
| Resource owner | cuhhleed |
| Repository access | Only selected repositories → nba-jinni |
| Administration | Read and write |
| Secrets | Read and write |
| Environments | Read and write |
| Metadata | Read-only (always required by GitHub) |

Expiry: 90 days is reasonable. Note the expiry date — see "PAT renewal" below.

**Never put the token in `.tfvars`, commit it, or pass it via `-var`.**

## Apply

```bash
cd infra/environments/shared

terraform init

export GITHUB_TOKEN=ghp_...
terraform apply
```

The `GITHUB_TOKEN` env var is picked up by the `integrations/github` provider directly. After apply, the env var can be unset.

## PAT renewal

The fine-grained PAT expires. When it does, `terraform plan` or `terraform apply` on this env will fail with a GitHub authentication error.

To renew: generate a new token on GitHub with the same scopes listed above, then re-export `GITHUB_TOKEN` and re-apply. No Terraform resources change — only the provider's auth credential rotates.

## Re-running the OIDC smoke test

Go to GitHub → Actions → OIDC Smoke Test → Run workflow. The `verify-dev` job runs immediately. The `verify-prod` job pauses for manual approval.

Both jobs run `aws sts get-caller-identity`. A successful response shows the assumed role ARN — confirm it matches `nbajinni-<env>-github-actions-role`.

Run this any time OIDC authentication appears broken in a deploy workflow.
