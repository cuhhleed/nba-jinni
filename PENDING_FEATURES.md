# Pending Features & Architectural Improvements

This document tracks features, refactors, and architectural improvements that have been identified during development but deferred for dedicated implementation.

---

## FEATURE-001 — Security Group Module Extraction — **COMPLETE**

### Status

Pending

### Background

Security groups for Lambda and RDS are currently defined directly inside `modules/vpc/main.tf`. This was identified as an architectural concern during Story 2.3 development when designing the teardown workflow.

### Problem

- Security groups are application-layer concerns (Lambda, RDS specific) but live inside a generic networking module — violating separation of concerns
- The dynamic teardown script excludes `module.vpc` to preserve foundational network resources, but this inadvertently preserves the custom security groups which should be destroyed and recreated freely
- The VPC module is not reusable across projects because it carries NBAJinni-specific security rules
- Both `lambda_sg` and `rds_sg` are tightly coupled to specific application modules (Lambda, RDS) but defined in an unrelated module

### Constraints

- `lambda_sg` is currently shared between `module.lambda_backend` and `module.lambda_ingestion` — any solution must support security group reuse across multiple Lambda functions without duplication
- `rds_sg` ingress rule references `lambda_sg` by ID — dependency ordering between modules must be preserved
- `aws_default_security_group` should remain in the VPC module as it is tied to the VPC lifecycle
- The refactor must cleanly rewire all existing module references without breaking deployment

### Proposed Solution

Create a dedicated `modules/security_groups/` module that is entirely generic — no knowledge of Lambda or RDS. The module accepts a VPC ID, name, and ingress/egress rule definitions as inputs and outputs a single security group ID. `environments/dev/main.tf` is responsible for instantiating it twice with the appropriate rules — once for Lambda, once for RDS — and wiring the output IDs to the compute modules. This keeps the module reusable for any security group without encoding application-specific knowledge inside it.

### Tasks

- [x] Create generic `modules/security_groups/` module — accepts vpc_id, project_name, environment, and ingress/egress rule configuration, outputs a single security group ID
- [x] Remove `lambda_sg` and `rds_sg` from `modules/vpc/main.tf` and their outputs from `modules/vpc/outputs.tf`
- [x] Instantiate the module twice in `environments/dev/main.tf` for Lambda and RDS respectively, wiring outputs to the appropriate compute modules
- [x] Update teardown script to exclude `module.vpc` only — security groups are destroyed as part of normal targeted teardown
- [x] Verify plan, apply, and targeted destroy work correctly end-to-end

---

## FEATURE-002 — Dynamic Teardown Script — **COMPLETE**

### Status

Pending — implement after FEATURE-001

### Background

Identified during Story 2.3 when `terraform destroy` was taking 20+ minutes to complete due to AWS Elastic Network Interfaces (ENIs) lingering for a while after their associated Lambda function is deleted ([GitHub Issue](https://github.com/hashicorp/terraform-provider-aws/issues/10329)). This stalls the deletion of the attached security groups and the subnets the ENIs reside in. To work around that, custom security groups have been configured to be swapped with the default security group when destroying to separate them from the ENI, and `prevent_destroy` was added to foundational VPC resources, including subnets that would still stall. Consequently, this makes a plain `terraform destroy` error out on protected resources. A partial destroy using `-target` flags is required for routine teardowns, but managing that list manually is fragile. The partial destroy was observed to bring down teardown time by over 67%.

### Problem

- Lingering ENI deletions on the AWS side cause teardowns to take over 20+ minutes, mostly waiting.
- `terraform destroy` errors on `prevent_destroy` resources — a targeted destroy is required for routine teardowns.
- Manually maintaining a `-target` list is error-prone and becomes stale as new modules are added to the project.
- The Secrets Manager 30-day recovery window causes redeployment failures if the secret is not force-deleted before recreating.
  <<<<<<< Updated upstream
  =======
- Current workaround:

```
terraform destroy \
  -target=aws_secretsmanager_secret.db_credentials \
  -target=aws_secretsmanager_secret_version.db_credentials_secret \
  -target=module.lambda_security_group \
  -target=module.rds_security_group \
  -target=module.rds \
  -target=aws_iam_role.lambda_exec \
  -target=aws_iam_policy.lambda_secrets \
  -target=aws_iam_role_policy_attachment.lambda_secrets_attach \
  -target=aws_iam_role_policy_attachment.lambda_vpc_attach \
  -target=module.lambda_ingestion \
  -target=module.lambda_backend \
  -target=module.api_gateway \
  -target=module.event_bridge \
  -target=module.s3_frontend \
  -target=module.cloudfront_frontend \
  -target=aws_s3_bucket_policy.s3-policy-frontend
```

### Proposed Solution

A shell script at `scripts/teardown.sh` that dynamically builds the `-target` list by querying Terraform state and excluding `module.vpc`:

```bash
TARGETS=$(terraform state list | grep -v "module.vpc" | sed 's/^/-target=/' | tr '\n' ' ')
terraform destroy $TARGETS
```

This is self-maintaining — new modules are automatically included without any script updates needed. The only hardcoded exclusion is `module.vpc`, which is stable by design. The script should also handle the Secrets Manager force-delete step before running the destroy.

### Tasks

- [x] Create `scripts/teardown.sh` — dynamically build `-target` list from state, exclude `module.vpc`, force-delete Secrets Manager secret, run `terraform destroy`
- [x] Document usage in README

---

## FEATURE-003 — Shared Models Package

### Status

Pending

### Background

Identified during Epic 3 development when seed scripts in the `/ingestion` package needed access to SQLAlchemy models defined in `/backend`. Both packages currently maintain separate model definitions, violating the single source of truth principle.

### Problem

- SQLAlchemy models are defined in `backend/app/models/` but are needed by the ingestion pipeline and seed scripts
- Duplicating models across packages means schema changes must be applied in multiple places — a maintenance burden and a source of drift
- The `DeclarativeBase` in `backend/app/db/base.py` is tightly coupled to the backend package, making it inaccessible to other packages
- As the project grows, any new consumer of the models (e.g. data analysis scripts, admin tools) would face the same duplication problem

### Constraints

- Both `backend` and `ingestion` have separate `pyproject.toml` files and are independently deployable — the shared package must not introduce tight coupling between them
- The backend's `alembic/env.py` imports `Base` and all models — these imports must be updated to reference the shared package without breaking migrations
- The refactor must not break existing migration history or require schema changes

### Proposed Solution

Create a dedicated `/shared` package containing the `DeclarativeBase` and all SQLAlchemy models. Both `backend` and `ingestion` declare it as a local path dependency in their `pyproject.toml` using Poetry's editable install feature. This keeps models as a single source of truth while preserving the independent deployability of each package.

### Tasks

- [ ] Create `/shared` package with `pyproject.toml` and `nbajinni_shared/` module structure
- [ ] Move `DeclarativeBase` from `backend/app/db/base.py` to `shared/nbajinni_shared/base.py`
- [ ] Move all models from `backend/app/models/` to `shared/nbajinni_shared/models/`
- [ ] Add `nbajinni-shared` as a local path dependency in `backend/pyproject.toml` and `ingestion/pyproject.toml`
- [ ] Update `backend/alembic/env.py` imports to reference shared package
- [ ] Update all backend imports that reference `app.models` or `app.db.base` to reference `nbajinni_shared`
- [ ] Verify migrations still run correctly after refactor
- [ ] Verify ingestion seed scripts can import models from shared package

---
