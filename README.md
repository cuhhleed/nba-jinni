# NBA-Jinni

The only NBA stats and performance tool you'll wish for.

## Teardown Script

A helper script for tearing down the dev environment without destroying protected VPC resources.

### Usage

```bash
./scripts/teardown.sh
```

### What it does

1. Builds a `-target` list from Terraform state, automatically excluding `module.vpc` and its protected resources (subnets, route tables, internet gateway)
2. Runs a destroy plan and displays a resource summary before prompting for confirmation
3. Destroys all targeted resources
4. Force-deletes the Secrets Manager secret to bypass the 30-day recovery window, ensuring a clean `terraform apply` on the next deployment

### Notes

- Script is scoped to `infra/environments/dev` — not intended as a generic tool
- The `-target` list is dynamically built from state, so new modules are automatically included without any script changes needed
- The only hardcoded exclusion is `module.vpc`, which is stable by design
