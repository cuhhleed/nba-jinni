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

## FEATURE-002 — Dynamic Teardown Script

### Status

Pending — implement after FEATURE-001

### Background

Identified during Story 2.3 when `terraform destroy` was taking 20+ minutes to complete due to AWS Elastic Network Interfaces (ENIs) lingering for a while after their associated Lambda function is deleted ([GitHub Issue](https://github.com/hashicorp/terraform-provider-aws/issues/10329)). This stalls the deletion of the attached security groups and the subnets the ENIs reside in. To work around that, custom security groups have been configured to be swapped with the default security group when destroying to separate them from the ENI, and `prevent_destroy` was added to foundational VPC resources, including subnets that would still stall. Consequently, this makes a plain `terraform destroy` error out on protected resources. A partial destroy using `-target` flags is required for routine teardowns, but managing that list manually is fragile. The partial destroy was observed to bring down teardown time by over 67%.

### Problem

- Lingering ENI deletions on the AWS side cause teardowns to take over 20+ minutes, mostly waiting.
- `terraform destroy` errors on `prevent_destroy` resources — a targeted destroy is required for routine teardowns.
- Manually maintaining a `-target` list is error-prone and becomes stale as new modules are added to the project.
- The Secrets Manager 30-day recovery window causes redeployment failures if the secret is not force-deleted before recreating.

### Proposed Solution

A shell script at `scripts/teardown.sh` that dynamically builds the `-target` list by querying Terraform state and excluding `module.vpc`:

```bash
TARGETS=$(terraform state list | grep -v "module.vpc" | sed 's/^/-target=/' | tr '\n' ' ')
terraform destroy $TARGETS
```

This is self-maintaining — new modules are automatically included without any script updates needed. The only hardcoded exclusion is `module.vpc`, which is stable by design. The script should also handle the Secrets Manager force-delete step before running the destroy.

### Tasks

- [ ] Create `scripts/teardown.sh` — dynamically build `-target` list from state, exclude `module.vpc`, force-delete Secrets Manager secret, run `terraform destroy`
- [ ] Document usage in README

---
