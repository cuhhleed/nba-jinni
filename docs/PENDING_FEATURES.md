# Pending Features & Architectural Improvements

This document tracks features, refactors, and architectural improvements that have been identified during development but deferred for dedicated implementation. All features are implemented and merged from the `feature-001` branch.

---

## FEATURE-001 — Security Group Module Extraction

### Status

**COMPLETE**

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

**COMPLETE**

### Background

Identified during Story 2.3 when `terraform destroy` was taking 20+ minutes to complete due to AWS Elastic Network Interfaces (ENIs) lingering for a while after their associated Lambda function is deleted ([GitHub Issue](https://github.com/hashicorp/terraform-provider-aws/issues/10329)). This stalls the deletion of the attached security groups and the subnets the ENIs reside in. To work around that, custom security groups have been configured to be swapped with the default security group when destroying to separate them from the ENI, and `prevent_destroy` was added to foundational VPC resources, including subnets that would still stall. Consequently, this makes a plain `terraform destroy` error out on protected resources. A partial destroy using `-target` flags is required for routine teardowns, but managing that list manually is fragile. The partial destroy was observed to bring down teardown time by over 67%.

### Problem

- Lingering ENI deletions on the AWS side cause teardowns to take over 20+ minutes, mostly waiting.
- `terraform destroy` errors on `prevent_destroy` resources — a targeted destroy is required for routine teardowns.
- Manually maintaining a `-target` list is error-prone and becomes stale as new modules are added to the project.
- The Secrets Manager 30-day recovery window causes redeployment failures if the secret is not force-deleted before recreating.
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

**COMPLETE**

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

- [x] Create `/shared` package with `pyproject.toml` and `nbajinni_shared/` module structure
- [x] Move `DeclarativeBase` from `backend/app/db/base.py` to `shared/nbajinni_shared/base.py`
- [x] Move all models from `backend/app/models/` to `shared/nbajinni_shared/models/`
- [x] Add `nbajinni-shared` as a local path dependency in `backend/pyproject.toml` and `ingestion/pyproject.toml`
- [x] Update `backend/alembic/env.py` imports to reference shared package
- [x] Update all backend imports that reference `app.models` or `app.db.base` to reference `nbajinni_shared`
- [x] Verify migrations still run correctly after refactor
- [x] Verify ingestion seed scripts can import models from shared package

---

## FEATURE-004 — Schema Amendments for Team Statistics and Standings

### Status

**COMPLETE**

### Background

Identified during Epic 4 feature planning when the full statistics dashboard was scoped out. The existing schema was designed before the frontend feature set was fully defined. Now that the data requirements of every dashboard view are understood, three schema changes are needed before ingestion work begins: two new tables for team-level statistics and targeted amendments to the existing `standings` table.

### Problem

- The schema has no team-level box score table — team statistics per game cannot be stored or queried without summing player rows, which is fragile and produces rounding drift on percentage fields
- The schema has no team season averages table — serving comparison stats on the game detail page (e.g. average points allowed) would require expensive aggregate queries on every request
- The existing `standings` model has a redundant `win_streak` boolean that duplicates information already encoded in the sign of the `streak` integer, creating a two-field synchronisation risk on every upsert
- The `standings` model is missing `division_rank`, `points_pg`, and `opp_points_pg` — all of which are returned directly by `LeagueStandingsV3` at no extra cost and are needed for the standings widget and team comparison surface
- The `standings` model has no `updated_at` column — since rows are upserted rather than appended, there is no way to determine when the data was last refreshed without it

### Constraints

- `team_game_stats` must be populated from the team result set returned by `BoxScoreTraditionalV2` — the same call already made for player stats — so no additional API calls are introduced
- `team_season_averages` must be derived locally from `team_game_stats` after each nightly upsert, following the same pattern as `player_season_averages`, to avoid spending an API call on data that can be computed
- The `standings` amendments require a new Alembic migration against an already-deployed table — the migration must use `ALTER TABLE` rather than recreating the table to preserve any existing rows

### Proposed Changes

**New table: `team_game_stats`**

```
game_id (PK, FK → games.id), team_id (PK, FK → teams.id),
points, opponent_points, rebounds, assists, steals, blocks,
turnovers, fg_pct, three_pct, ft_pct
```

**New table: `team_season_averages`**

```
team_id (PK, FK → teams.id), season_id (PK, FK → seasons.id),
games_played, points, opponent_points, rebounds, assists, steals,
blocks, turnovers, fg_pct, three_pct, ft_pct
```

**Amended model: `standings`**

| Field           | Change     | Reason                                                                |
| --------------- | ---------- | --------------------------------------------------------------------- |
| `win_streak`    | **Remove** | Redundant — direction is encoded in the sign of `streak`              |
| `division_rank` | **Add**    | Returned directly by `LeagueStandingsV3`; needed for standings widget |
| `points_pg`     | **Add**    | Returned directly by `LeagueStandingsV3`; needed for team comparison  |
| `opp_points_pg` | **Add**    | Returned directly by `LeagueStandingsV3`; needed for team comparison  |
| `updated_at`    | **Add**    | Tracks data freshness on upserted rows                                |

### Tasks

- [x] Write Alembic migration: create `team_game_stats` table
- [x] Write Alembic migration: create `team_season_averages` table
- [x] Write Alembic migration: amend `standings` — drop `win_streak`, add ~~`division_rank`,~~ `points_pg`, `opp_points_pg`, `updated_at`
- [x] Update `Standing` model in `/shared` to reflect amended schema
- [x] Add `TeamGameStat` and `TeamSeasonAverage` models to `/shared`
- [x] Verify all migrations apply cleanly with `alembic upgrade head`
- [x] Marked indexes in model files otherwise alembic autogenerate reverses manual add_indexes migration.

---

## FEATURE-005 — Historical Season Backfill Lambda

### Status

FURTHER PLANNING NEEDED

### Background

Identified during Story 4.3 development when scoping the nightly ingestion job. Historical season data is on the roadmap (e.g. multi-season vs-opponent and vs-matchup stat views) but is not required for any features currently being implemented. Backfill was originally stubbed as `run_backfill()` inside the main ingestion Lambda handler.

### Problem

- A backfill run for a full historical season can involve hundreds of game stat fetches with throttle delays between each — execution time is unbounded relative to a nightly job and incompatible with sharing a Lambda timeout configuration
- Keeping backfill inside the nightly Lambda forces the timeout to be provisioned for the worst-case backfill scenario, over-provisioning for every other job
- The stub in the current handler should be removed once this feature is promoted to its own function

### Constraints

- Each invocation should process exactly one season, passed as input — this keeps execution time bounded and makes partial backfills resumable by re-invoking with the same season
- The function must use the same `nba_api` wrapper, throttling, and upsert patterns as the nightly job — backfill inserts into the same `player_game_stats`, `team_game_stats`, `player_season_averages`, and `team_season_averages` tables
- Already-ingested games must be skipped idempotently — backfill should be safe to re-run against a season without producing duplicates or overwriting valid data
- The function must respect NBA.com throttling — a full season backfill should not attempt to fetch all games in rapid succession

### Proposed Solution

A dedicated Lambda function that accepts `{ "season": "2023-24" }` as its event payload. The bulk of the implementation already exists — `ingest_games`, `compute_player_averages`, and `compute_team_averages` in `utils.py` are reusable as-is. The remaining work is refactoring `run_schedule_biweekly` and `run_roster_biweekly` in `main.py` so their core logic is extracted into standalone utility functions in `utils.py`, allowing the backfill handler to call schedule and roster fetching for an arbitrary season rather than always defaulting to the current one. The backfill handler then orchestrates these utilities in sequence: fetch roster → fetch schedule → ingest completed games → compute averages.

### Tasks

- [ ] Remove `run_backfill()` stub and `backfill` job routing from the nightly Lambda handler
- [ ] Extract schedule ingestion logic from `run_schedule_biweekly` into a reusable `ingest_schedule(season, session)` utility function in `utils.py`
- [ ] Extract roster ingestion logic from `run_roster_biweekly` into a reusable `ingest_roster(season, session)` utility function in `utils.py`
- [ ] Refactor `run_schedule_biweekly` and `run_roster_biweekly` in `main.py` to call the new utility functions rather than containing the logic directly
- [ ] Create a new Lambda function under `/ingestion` with its own handler entry point
- [ ] Accept `season` as a required event input — error clearly if missing or malformed
- [ ] Orchestrate `ingest_roster`, `ingest_schedule`, `ingest_games`, `compute_player_averages`, and `compute_team_averages` in the backfill handler
- [ ] Add Terraform `lambda` module for the backfill function with independently configurable timeout and memory
- [ ] Document invocation instructions in the README

---
