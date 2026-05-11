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

## FEATURE-006 — Live Game Data via Cached Backend Proxy

### Status

COMPLETE

### Depends On

- **FEATURE-007** — the `tipoff_at` column added in this feature is the first user of the schema-amendment workflow defined there. The migration pattern, deploy choreography, and touch-point checklist (model, migration, parser, upsert `set_` dict, loader `DATE_COLUMNS`) are documented in FEATURE-007 and must be followed when implementing the schema portion of this feature.

### Background

Identified during Story 6.6 (Front Page) planning when scoping widgets that surface today's games and recent results. The site has no live-game plumbing — all data flows through nightly batch ingestion (9 AM UTC, ADR-005). The `Game` model has only two effective states: `status = 1` (not yet ingested) and `status = 3` (completed and ingested). It also lacks tip-off time — `game_date` is a date with the time component zero'd out — so there is no way to distinguish "game starts in 4 hours" from "game ended 30 minutes ago" using the current schema. The result is that any in-progress or recently-completed-but-uningested game renders as a stale "preview" everywhere (front page widgets and the existing GameDetail page from Story 6.8).

### Problem

- Front page cannot credibly surface "today's games" or "recent results" — both require data more current than the last nightly ingest
- The GameDetail page renders preview UI for completed games whose nightly ingest has not yet run, misleading the user with stale schedule data and no scores
- Live games (in progress) have no rendering path at all — they fall through into the same preview branch as upcoming games
- Without a tip-off datetime, the frontend cannot route between "show preview" and "show live" deterministically — date-only comparison cannot resolve the difference between a 7pm tip and a 10pm tip on the same calendar day
- Persisting live data into RDS is the wrong fit — it goes stale within seconds, conflicts with the truncate-and-insert loader pattern (ADR-005), and inflates write volume on data that is inherently ephemeral

### Constraints

- All current backend reads come from RDS (per ADR-005); adding `nba_api` as a runtime dependency on the request path is an architectural shift and must be explicitly documented
- Live data must be **cache-only** — never written to RDS — to avoid clashing with the truncate-and-insert nightly loader and to keep the live concern fully separated from the durable data model
- The wrapper must avoid hammering NBA's CDN — central caching is required; per-user fan-out is unacceptable
- Failures of the upstream (timeout, rate limit, schema change) must degrade gracefully — neither blank pages nor misleading preview-fallbacks
- The Game page UI (`frontend/src/routes/GameDetail.tsx`) must integrate live rendering without forking into a separate route — one page, three states (preview / live / final)
- `Game.status` remains the source of truth for "is this row ingested yet" — wall-clock heuristics must not be used to bypass it
- Tip-off datetime is already present in the existing `ScheduleLeagueV2` response (`gameDateTimeUTC`) — no new ingestion call should be introduced to obtain it

### Proposed Solution

**Schema amendment.** Add a `tipoff_at` (timezone-aware UTC datetime) column to `Game` following the workflow defined in **FEATURE-007**. Update the schedule parser at `shared/nbajinni_shared/utils.py:276` to read `gameDateTimeUTC` instead of `gameDate`, add `tipoff_at` to both the `.values(...)` and `set_={...}` blocks of the `ingest_schedule` upsert at `shared/nbajinni_shared/utils.py:287-294`, and add `"tipoff_at"` to the `games` set in `loader/main.py:43` (`DATE_COLUMNS`). The deploy sequence (parser change → local alembic → local schedule ingest → JSON export → loader migrate-then-load on RDS) ensures both DBs end up with real values and a NOT NULL constraint, with no nullable phase visible in application code.

**Two backend endpoints, both cached in-process via `cachetools.TTLCache`:**

- `GET /games/live/today` — bulk endpoint wrapping `nba_api.live.nba.endpoints.ScoreBoard`. Returns today's slate with current scores, period, clock, status text, and tip-off times. Single cache key. Variable TTL based on aggregate state of the slate: ~30s while any game is live, ~5 min when all games are over and awaiting ingest, ~30 min when no games have started yet. Powers the front page games widget.
- `GET /games/live/{game_id}` — per-game endpoint wrapping `nba_api.live.nba.endpoints.BoxScore`. Validates the game exists and `status != 3` (returns DB result if already ingested — short-circuit, no NBA call). Returns full live box score: per-player stats, team aggregates, period breakdowns, arena, officials. Cache key is `game_id`. Variable TTL: ~15-30s while live, ~5-10 min if game appears over but not yet ingested, near-zero (or 404) if tip-off has not passed. Powers the GameDetail page when a game is in live or finished-not-ingested state.

**Frontend routing rule** (used by both the front page widget and the GameDetail page) — keys off `status` and `tipoff_at`, never on wall-clock heuristics alone:

- `status == 3` → DB (`/games/{id}` final result)
- `status != 3` AND `now < tipoff_at` → DB preview
- `status != 3` AND `now >= tipoff_at` → live endpoint

**Failure handling.** On upstream failure during a cache miss, serve the most recent stale cache value with a `last_updated_at` field. The frontend renders an "as of HH:MM" badge on stale data. If there is no cache value at all, the endpoint returns a structured error and the frontend hides the live widget without breaking the page.

**Architectural documentation.** Add a new ADR documenting (a) the introduction of a runtime upstream dependency on nba_api, (b) the cache-only-never-RDS rule, (c) TTL strategy and rationale, (d) failure mode contract.

### Tasks

- [x] Add `tipoff_at: Mapped[datetime]` (non-nullable, timezone-aware) to `Game` model in `shared/nbajinni_shared/models/games.py`
- [x] Write Alembic migration for `tipoff_at` using the FEATURE-007 pattern (NOT NULL with `server_default=sa.func.now()`, then `DROP DEFAULT` immediately after)
- [x] Update schedule parser at `shared/nbajinni_shared/utils.py:276` to read `gameDateTimeUTC` as a timezone-aware datetime
- [x] Add `tipoff_at` to both the `.values(...)` and `set_={...}` blocks of the `ingest_schedule` upsert (`shared/nbajinni_shared/utils.py:287-294`) so existing rows are populated on conflict
- [x] Add `"tipoff_at"` to `DATE_COLUMNS["games"]` in `loader/main.py:43` so the loader hydrates ISO datetime strings from the JSON export
- [x] Implement `GET /games/live/today` — wraps `nba_api.live.nba.endpoints.ScoreBoard`, in-process `StaleCache` with variable TTL based on slate state, stale-cache fallback on upstream failure
- [x] Implement `GET /games/live/{game_id}` — wraps `nba_api.live.nba.endpoints.BoxScore`, validates existence + `status != 3` short-circuit + `tipoff_at` pre-game short-circuit, variable TTL, stale-cache fallback
- [x] Define Pydantic response schemas for both endpoints (`GameLive`, `PlayerLiveStat`, `LiveScoreboardEntry`, `LiveScoreboardResponse`) including `last_updated_at` and `is_stale` for badge rendering
- [ ] Update `frontend/src/routes/GameDetail.tsx` to apply the three-state routing rule (`status` + `tipoff_at` + `now`) and render full live box score UI when in live state — deferred to Story 6.8.x
- [ ] Build a `<FreshnessBadge />` component for "as of HH:MM" rendering on stale-cache responses — deferred to frontend integration stories
- [ ] Update front page games widget (Story 6.6) to call `/games/live/today` and render scores/clocks for in-progress and finished-not-ingested games — deferred to Story 6.6
- [x] Add a new ADR under `docs/ARCHITECTURE_DECISIONS.md` covering runtime nba_api dependency, cache-only rule, TTL strategy, and failure-mode contract (ADR-007)
- [ ] Verify end-to-end: live game in progress → bulk endpoint reflects score within TTL; live game over but not ingested → per-game endpoint serves live box score; same game post-ingest → endpoint short-circuits to DB result (requires live NBA game window)

**Deferred frontend work:** GameDetail.tsx integration deferred to Story 6.8.x; front page widget integration deferred to Story 6.6.

---

## FEATURE-007 — Schema Amendment Workflow for Populated Tables

### Status

PROPOSED

### Background

Adding columns to tables that already contain rows is a recurring need as the project's data model evolves. Past amendments (e.g. FEATURE-004's standings work) used Alembic autogen output that adds `nullable=False` columns directly via `op.add_column`. This succeeds only if the target table is empty at migration time — which has worked so far because the loader uses truncate-and-insert and the local DB has been cleared manually before each amendment. That convention is implicit, undocumented, and breaks down the moment a new column needs values derived from data that isn't already in the DB (e.g. an API field that wasn't previously parsed). FEATURE-006 (Live Game Data) is the first amendment that hits this case: `tipoff_at` requires a value pulled from `gameDateTimeUTC` via `ingest_schedule`, and that ingestion must run between the migration and the JSON export — a sequencing requirement that no current docs capture.

### Problem

- Adding `NOT NULL` columns directly via Alembic autogen fails on populated tables — and the loader's `migrate` action runs the migration **before** the truncate (`loader/main.py:120-138`), so on RDS the migration sees a populated table during `action: "migrate"` invocations
- Making columns nullable as a workaround forces `Optional`/null checks throughout downstream code, undermining the value of the type system; a brief operational window of nullability should not become a permanent application-code concern
- The deploy choreography needed to populate a new column with real values (parser change → local migrate → ingestion → export → RDS migrate-then-load) is undocumented — engineers approaching FEATURE-006 (and any future similar feature) have no canonical reference and risk inventing the pattern inconsistently
- The full set of touch points beyond the model and migration — `ingest_*` upsert `set_={...}` dicts, `loader/main.py` `DATE_COLUMNS`, the parser itself — is easy to miss; partial implementations fail silently (e.g. existing rows keep synthesized defaults forever) or loudly (e.g. loader insert errors on missing column) only at integration time

### Constraints

- Pattern must work for both the local DB (upsert-based, persistent across runs) and RDS (truncate-and-insert via the loader Lambda) without divergent logic
- Pattern must not introduce a nullable phase that surfaces in the application code's type model — DB column is `NOT NULL` from the moment it exists, model is non-nullable, no `Optional` in routers or services
- Pattern must work with the existing `loader/main.py` migrate-then-load flow without modifying the loader
- Existing migrations must not be retrofitted — they ran cleanly against empty/cleared tables and rewriting them would be churn for no benefit; this workflow applies prospectively only
- Documentation must be discoverable from the developer entry points (`CLAUDE.md` and any existing alembic conventions notes) so the workflow is found before mistakes are made

### Proposed Solution

**1. Standard Alembic pattern for adding NOT NULL columns to populated tables**

Use a `server_default` to atomically backfill existing rows during `ALTER TABLE`, then immediately drop the default so future inserts must provide a real value. Synthesized defaults are placeholders that exist only between the migration and the next data-rewriting operation (a truncate on RDS, or an upsert on the local DB).

```python
def upgrade() -> None:
    op.add_column(
        "<table>",
        sa.Column(
            "<column>",
            <type>,
            nullable=False,
            server_default=<placeholder_expression>,  # e.g. sa.func.now() for datetimes
        ),
    )
    op.execute("ALTER TABLE <table> ALTER COLUMN <column> DROP DEFAULT")

def downgrade() -> None:
    op.drop_column("<table>", "<column>")
```

The distinction matters: `server_default` is part of the column DDL and is applied by Postgres during `ALTER TABLE` to backfill existing rows. A Python-side `default=` does nothing here because Alembic isn't issuing inserts. The `op.execute(...)` line drops the default so the application is forced to provide values from now on.

**2. Codified deploy choreography for amendments that derive values from external data**

When a new column's real values must come from data not already in the DB (an API field that wasn't previously parsed, a computed value, etc.), the sequence is:

1. Single PR contains: model field, migration (server*default + drop), parser update, ingest upsert `set*={...}`update, and any loader`DATE_COLUMNS` update
2. Run alembic locally → existing local rows briefly hold synthesized defaults
3. Run the relevant local ingestion path → upsert overwrites synthesized defaults with real values
4. Export JSON to S3 → captures real values
5. Invoke loader with `action: "migrate"` → migrates RDS, truncates, reloads with real values from JSON

End state: both DBs have NOT NULL constraint with real values. Synthesized defaults are never visible to users — they exist only inside the migration window on each DB (seconds locally, milliseconds on RDS).

**3. Touch-point checklist**

For each amendment, verify all applicable touch points are updated in the same PR:

- `shared/nbajinni_shared/models/<table>.py` — add the field as non-nullable in the SQLAlchemy model
- `shared/alembic/versions/<rev>_<name>.py` — migration following the pattern above
- `shared/nbajinni_shared/utils.py` — parser to extract the value from the source response, **and** the corresponding upsert's `set_={...}` dict so existing rows are populated on conflict (not just on initial insert)
- `loader/main.py` `DATE_COLUMNS` — if the new column is a date or datetime, add the column name to the relevant table's set so the loader correctly casts ISO strings back to Python types during JSON load

Missing the upsert `set_` update is the highest-risk omission: locally, existing rows keep their synthesized defaults; the JSON export carries those fakes to RDS; symptoms manifest as "every row has the same suspicious value" rather than as a constraint violation.

**4. Optional: helper function**

A small helper in a new `shared/alembic/utils.py` module would standardize the pattern and make intent grep-able:

```python
def add_required_column(table: str, column: sa.Column) -> None:
    """Add a NOT NULL column to a populated table.

    The column must declare a `server_default` to backfill existing rows.
    The default is dropped immediately after the column is created so future
    inserts are required to provide a real value.
    """
    assert column.server_default is not None, "add_required_column requires server_default"
    op.add_column(table, column)
    op.execute(f'ALTER TABLE {table} ALTER COLUMN {column.name} DROP DEFAULT')
```

Whether to introduce the helper or stick with the two-line inline pattern is a small judgment call — the inline form is already short, but the helper makes intent explicit and prevents a future engineer from forgetting the `DROP DEFAULT` step.

### Tasks

- [ ] Decide whether to introduce the `add_required_column` helper or document the inline pattern as a convention; if chosen, add it to a new `shared/alembic/utils.py`
- [ ] Create `docs/SCHEMA_AMENDMENTS.md` documenting the Alembic pattern, the deploy choreography, and the touch-point checklist
- [ ] Cross-link `docs/SCHEMA_AMENDMENTS.md` from `CLAUDE.md` under the Project Workflow section so the runbook is found before mistakes are made
- [ ] Cross-link `docs/SCHEMA_AMENDMENTS.md` from any existing alembic conventions notes (e.g. README sections, `shared/alembic/README` if present)
- [ ] Add a brief note to `docs/ARCHITECTURE_DECISIONS.md` ADR-005 (or as a new ADR) acknowledging that schema amendments to populated tables follow this workflow, leveraging the loader's migrate-then-load flow

---
