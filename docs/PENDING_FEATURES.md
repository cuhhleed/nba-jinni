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
- [x] Update `frontend/src/routes/GameDetail.tsx` to apply the three-state routing rule (`status` + `tipoff_at` + `now`) and render full live box score UI when in live state — deferred to Story 6.8.x
- [x] Build a `<FreshnessBadge />` component for "as of HH:MM" rendering on stale-cache responses — deferred to frontend integration stories
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
- [ ] Cross-link `docs/SCHEMA_AMENDMENTS.md` from any existing alembic conventions notes (e.g. README sections, `shared/alembic/README` if present)
- [ ] Add a brief note to `docs/ARCHITECTURE_DECISIONS.md` ADR-005 (or as a new ADR) acknowledging that schema amendments to populated tables follow this workflow, leveraging the loader's migrate-then-load flow

---

## FEATURE-008 — Terraform CI Workflow with Dedicated TF-CI IAM Roles

### Status

PROPOSED

### Background

Story 7.1 (ADR-010) established OIDC-based AWS authentication with per-environment GitHub Environments (`dev`, `prod`) and tightly scoped app-deploy roles (`nbajinni-<env>-github-actions-role`). Those roles are limited to the operations needed for shipping application code: Lambda update, S3 sync, CloudFront invalidate, and Secrets Manager read. They intentionally exclude IAM management and Terraform state permissions to minimize blast radius.

Story 7.2 needs to run Terraform itself in CI. That requires different, broader permissions that are inappropriate to bolt onto the existing app-deploy roles.

### Problem

- `nbajinni-<env>-github-actions-role` lacks IAM, state-bucket, and lock-table permissions — it cannot run `terraform apply`
- Granting those permissions to the app-deploy role inflates blast radius for every workflow that uses it
- The original Story 7.2 task "store state bucket / region / lock table as GH secrets" does not fit the OIDC model — these values are already public in committed `backend.tf` and are not credentials
- `db_username` / `db_password` are sensitive variables that Terraform consumes at apply time — they must reach CI without being stored as plaintext in Terraform state (chicken-and-egg: Terraform cannot manage the secret it needs to run)

### Constraints

- OIDC trust pattern must match ADR-010 (`repo:cuhhleed/nba-jinni:environment:<env>` sub claim)
- New IAM resources must live in `infra/environments/shared/` (account-wide CI bootstrap, separate from app env state)
- Module shape: both per-env roles (app-deploy + TF-CI) are encapsulated in the existing `github_actions_oidc` module, extended in place — no new module introduced
- Sensitive variables that Terraform consumes must not be Terraform-managed (plaintext-in-state avoidance)

### Proposed Solution

1. Second OIDC-trusted IAM role per environment: `nbajinni-<env>-terraform-ci-role`. Uses the same `github_oidc_trust_policy.json.tpl` (same `sub` claim format), separate deploy policy.

2. Provisioned inside the existing `github_actions_oidc` module (extended with `state_bucket` and `lock_table` inputs) so a single module call per environment creates both roles. Module outputs renamed for clarity: `role_arn` → `app_role_arn`, `role_name` → `app_role_name`; new outputs `terraform_role_arn`, `terraform_role_name`.

3. Policy composition for the TF-CI role: AWS-managed `PowerUserAccess` (covers all non-IAM service actions needed by Terraform) plus a custom policy (`github_oidc_terraform_policy.json.tpl`) granting IAM CRUD scoped to `nbajinni-<env>-*` resources, OIDC provider read (account-level), S3 state-prefix CRUD, and DynamoDB lock-table CRUD.

4. New environment-scoped GitHub Actions secret `TF_ROLE_ARN` (distinct from `AWS_ROLE_ARN`) — Terraform-managed via the same `integrations/github` provider used in Story 7.1.

5. Workflow `.github/workflows/terraform.yml` with three jobs:
   - `plan` — runs on PRs touching `infra/**`; runs `fmt -check`, `validate`, `plan` against `environments/dev`; posts a single auto-updating collapsible PR comment (marker `<!-- terraform-plan-dev -->`)
   - `apply-dev` — runs on push to `main`; runs `terraform apply -auto-approve` against `environments/dev`
   - `apply-prod` — runs on `workflow_dispatch`; statically bound to `environment: prod` for the GitHub approval gate; runs against `environments/prod` (will fail until that directory exists)
   State bucket, region, and lock table are hardcoded in the workflow-level `env:` block — not stored as GH secrets because the values are already public in committed `backend.tf`.

6. `DB_USERNAME` / `DB_PASSWORD` added manually to each GitHub Environment by the operator (one-time setup after `terraform apply` on `infra/environments/shared/`); workflow passes them via `TF_VAR_db_username` / `TF_VAR_db_password`. Plaintext never enters Terraform state.

7. PR comment uses `actions/github-script@v7` with marker-based update-or-create so repeated pushes to the same PR update one comment, not spam.

### Watch Points

- `apply-prod` will fail at `terraform init` until `infra/environments/prod/` exists — planned in a future story. Failure is expected and documented inline in the workflow file.
- `PowerUserAccess` is an AWS-managed policy; AWS may update its action set. If a future Terraform resource requires an IAM action not covered by the custom policy, the failure mode is a clear permissions error on `apply`.
- DB secrets in the GitHub UI are point-in-time. If `db_password` is rotated locally, the relevant `apply` job must be re-run to propagate the change to AWS Secrets Manager.
- Never run `terraform init -upgrade` in CI — the `.terraform.lock.hcl` lockfile pins provider versions and must stay in sync with local development.

### Tasks

- [x] Extend `infra/modules/github_actions_oidc/` with TF-CI role, policy, and attachments
- [x] Rename module outputs `role_arn` → `app_role_arn`, `role_name` → `app_role_name`; add `terraform_role_arn`, `terraform_role_name`
- [x] Update `infra/environments/shared/main.tf` module calls and secret resources
- [x] Add `TF_ROLE_ARN` secrets to `infra/environments/shared/main.tf`
- [x] Expose TF role ARNs in `infra/environments/shared/outputs.tf`
- [x] Create `.github/workflows/terraform.yml`
- [ ] Run `terraform apply` on `infra/environments/shared/` to create new AWS resources and GH secrets
- [ ] Manually add `DB_USERNAME` and `DB_PASSWORD` to the `dev` (and `prod`) GitHub Environments
- [ ] Verify end-to-end per the Story 7.2 verification checklist

---

## FEATURE-009 — Backend Lambda CI/CD Workflow with Schema-Bootstrap Carve-Out

### Status

PROPOSED

### Background

Story 7.1 (ADR-010) established OIDC + per-environment app-deploy IAM roles. Story 7.2 (FEATURE-008) added Terraform CI on top of that. Story 7.3 adds the third leg: a PR-test + dev-deploy + prod-promote pipeline for the backend FastAPI Lambda (handler `app.main.handler`, Mangum-wrapped, deployed to `nbajinni-<env>-request-handler`).

### Problem

- The Story 7.3 task line "promote the same zip to the prod Lambda alias" presupposes an `aws_lambda_alias` resource. The repo has zero `aws_lambda_alias` resources today; nothing in `infra/modules/lambda/` provisions one.
- The task line "store backend Lambda function names as GitHub Actions secrets" puts deterministic non-secret values (`nbajinni-<env>-request-handler`) into a secret store — the same dissonance FEATURE-008 addressed for state bucket / region / lock table.
- Backend tests in `backend/tests/conftest.py` require a real Postgres (transaction-rollback isolation per test) and read `TEST_DATABASE_URL` from env. `conftest.py` does NOT bootstrap the schema, so the CI test DB starts empty. ADR-005 forbids backend CI from running `alembic upgrade head`, but ADR-005's scope is *deploy-to-RDS migrations* (owned by the Loader Lambda), not *ephemeral CI test DB setup*.
- The backend zip bundles `nba_api` (ADR-007) which pulls in pandas + numpy. The resulting artifact is likely past the ~50 MB inline `update-function-code` limit.

### Constraints

- OIDC trust pattern must match ADR-010 (`environment:` declaration is mandatory on every deploy job — sub-claim gate).
- App-deploy role permissions must not be expanded (per Story 7.1 / ADR-010 minimal-scope decision). Phase-1 IAM audit confirmed the existing role already grants `lambda:UpdateFunctionCode`, `lambda:GetFunction`, `lambda:InvokeFunction` scoped to `nbajinni-<env>-*` and `s3:PutObject` to the lambda-artifacts bucket — sufficient.
- Cannot run Alembic in backend CI (ADR-005).
- Cannot alter the existing `scripts/package_backend.sh` bundle contents (ADR-001 + ADR-007 prescribe what goes in the zip).

### Proposed Solution

1. New workflow `.github/workflows/backend.yml` with three jobs: `pr-checks` (lint + pytest against Postgres service container, runs on every PR), `deploy-dev` (fires on `pull_request` events whose base is `main` — every push to the PR branch redeploys to dev as a preview, mirroring `terraform.yml`'s `apply-dev` pattern), `deploy-prod` (fires on `push` to `main` after PR merge, or on `workflow_dispatch`; gated by the prod GitHub Environment approval from Story 7.1).

2. Backend Lambda function names hardcoded in the workflow-level `env:` block (`BACKEND_LAMBDA_DEV: nbajinni-dev-request-handler`, `BACKEND_LAMBDA_PROD: nbajinni-prod-request-handler`) — not stored as GH secrets. Same rationale as FEATURE-008's state-bucket rewrite: deterministic public values do not belong in a secret store. The original Story 7.3 task is rewritten to reflect this.

3. No Lambda alias. The prod-promote job runs `aws lambda update-function-code` directly against `nbajinni-prod-request-handler`. Blue/green / canary strategy is deferred to a future story; the watch-point below records the trade-off (no atomic rollback).

4. Zip is staged through `s3://nbajinni-<env>-lambda-artifacts/backend.zip`, then deployed via `aws lambda update-function-code --s3-bucket / --s3-key` (handles zips larger than the inline limit). Mirrors how `terraform.yml` stages `loader.zip`.

5. PR pytest job uses a Postgres 16 service container with `pg_isready` healthcheck. Schema is bootstrapped via a one-shot Python step that imports every `nbajinni_shared.models.*` module and calls `Base.metadata.create_all()` against `TEST_DATABASE_URL`. **This is the documented carve-out from ADR-005:** ADR-005 governs deploy-to-RDS migrations (where the Loader Lambda owns Alembic and is the only path that touches the dev/prod databases). Ephemeral CI test DBs are out of that ADR's scope — they need a schema to exist somehow, and `create_all()` avoids dragging Alembic into the backend's dep set. Recorded here so a future reader does not mistake it for ADR drift.

6. Smoke test via `curl -sf` against `GET /health`, with the API URL read from `terraform output -raw api_gateway_url` (mirrors the `frontend.yml` pattern of running `terraform init` purely to read state). Three retries with 5 s sleep between to cover Lambda cold-start latency.

7. Workflow asserts the zip bundles both `nbajinni_shared/` and `nba_api/` (via `unzip -l | grep -q`) before staging — ADR-001 + ADR-007 enforcement at CI time, not just docs.

### Watch Points

- `deploy-prod` will fail until `infra/environments/prod/` exists AND `nbajinni-prod-request-handler` Lambda + `nbajinni-prod-lambda-artifacts` bucket are provisioned. Documented inline in the workflow; matches Story 7.2's `apply-prod` wire-but-fail shape.
- No Lambda alias = no atomic rollback. If a bad deploy reaches prod, mitigation is re-deploy from a previous commit, not an alias flip. Revisit when prod traffic justifies blue/green.
- The schema-bootstrap step is fragile against new model additions: a new `nbajinni_shared.models.<x>.py` requires updating the import block in `backend.yml`, or `create_all()` will silently skip that model's table. Acceptable trade-off — explicit imports are grep-friendly and the failure mode is clear (test fails on missing table).
- Poetry version is pinned in the workflow (`pipx install poetry==1.8.3`); bump in sync with local dev.

### Tasks

- [x] Create `.github/workflows/backend.yml` with `pr-checks`, `deploy-dev`, `deploy-prod` jobs
- [x] Hardcode backend Lambda function names + artifacts bucket names in workflow `env:` (no GH secrets for these)
- [x] Add Postgres 16 service container and schema-bootstrap step for PR tests
- [x] Add zip content assertion (`/shared` + `nba_api`) before deploy
- [x] Update `docs/project-plan.md` Story 7.3 task checkboxes (rewrite the "store function names as secrets" line)
- [ ] Verify end-to-end: trivial backend PR exercises `pr-checks`, merge to main exercises `deploy-dev`, `workflow_dispatch` exercises `deploy-prod` (expected to fail until prod env exists)
- [ ] After prod env exists in a future story, manually run `Actions → Backend CI → Run workflow` to confirm prod path and flip this FEATURE to IMPLEMENTED

---

## FEATURE-010 — Schema-Amendment Lint for CI

### Status

PROPOSED

### Background

FEATURE-007 (`docs/SCHEMA_AMENDMENTS.md`) prescribes a four-touch-point workflow for schema amendments to populated tables. Today the checklist is enforced by code review + the runtime `add_required_column()` helper, which only validates the migration's own shape. Stories 7.2 / 7.3 added CI gating for Terraform and the backend Lambda; Story 7.5 adds a parallel gate for schema amendments — a static lint that runs on every PR touching `shared/alembic/versions/` and verifies the four touch-points are updated together.

### Problem

1. The highest-risk omission (`set_={...}` on conflict) is structurally invisible to existing test suites: rows insert successfully with the wrong (synthesized) value and propagate to RDS via the JSON export. Failures manifest at production query time as "every row has the same value," not as a constraint error.
2. The model / `DATE_COLUMNS` / `.values()` omissions each manifest at different points downstream (next ingestion, next loader invocation, next backfill). All three are caught at PR review *if the reviewer remembers the checklist* — a weak gate.
3. The runtime `add_required_column` helper only enforces migration-side correctness. It cannot inspect other files.

### Constraints

- Lint must run in CI without `poetry install` overhead (used in fast-path PR jobs).
- Lint must only fail on touch-points that the PR's specific migration diff requires — must not flag pre-existing inconsistencies.
- Lint must handle three migration shapes (`op.add_column`, `add_required_column`, `op.create_table`) per the existing repo conventions.
- Lint must be runnable locally (`python scripts/lint_schema_amendments.py shared/alembic/versions/<file>.py`) so an author can iterate before pushing.

### Proposed Solution

1. New script `scripts/lint_schema_amendments.py` — stdlib-only Python (`ast`, `pathlib`, `argparse`, `re`, `sys`). Takes migration file paths as positional args, parses each to extract added columns (`(table, column, sql_type, nullable, server_default)` tuples), and verifies the four touch-points per the FEATURE-007 checklist. Exits 1 on any violation, 0 otherwise.
2. Wired into `.github/workflows/backend.yml`'s `pr-checks` job as a step that runs after Python setup and before any other lint step (fail-fast). The step uses `git diff --diff-filter=AM` against the PR base SHA to discover changed migrations; passes them as positional args. `actions/checkout@v4` is updated with `fetch-depth: 0` so the diff works.
3. Will be wired into `.github/workflows/loader.yml`'s PR job by Story 7.4's executor using the snippet documented in Story 7.5's plan.
4. New `scripts/tests/test_lint_schema_amendments.py` — pytest cases for each check (happy path + each failure mode + `create_table` carve-out + PK/FK exclusion). Runnable via `cd scripts && python -m pytest tests/`. Not wired into the workflow's pytest job (different package); covered by manual local runs and any future scripts-package CI.
5. Violation messages are formatted as one line per violation with the citation `(FEATURE-007: <touch-point>)` so PR authors can find the doc.

### Watch Points

- Lint maps tables to model files by naming convention (`<table>` → `shared/nbajinni_shared/models/<table>.py`). If a future model is named differently (e.g., a single file declaring multiple tables), the lint will false-negative on the model check. Acceptable tradeoff: keep the convention; if it ever breaks, the lint's fix is a small `__tablename__` AST-walk extension.
- Lint scans `shared/nbajinni_shared/utils.py` for upsert patterns. If a future ingestion module moves to a different file (e.g., `shared/nbajinni_shared/ingest/<table>.py`), the lint must be extended. Track this as a follow-up if/when the ingestion code is split.
- `op.create_table` carve-out skips upsert + DATE_COLUMNS + server_default checks for every column in the table. If a developer adds a `create_table` for a populated-data table (rare), they bypass the lint. The carve-out is correct for genuinely new tables; document this as a known tradeoff.
- The lint does not check `op.alter_column` or `op.drop_column` operations. Modifying or removing columns is rare enough today that code review remains the gate. Revisit if drop-column omissions become a recurring issue.

### Tasks

- [ ] Create `scripts/lint_schema_amendments.py` (stdlib-only)
- [ ] Create `scripts/tests/test_lint_schema_amendments.py` (pytest cases for each check)
- [ ] Add `scripts/tests/__init__.py`
- [ ] Update `.github/workflows/backend.yml` `pr-checks` job: `fetch-depth: 0` on checkout, new lint step before flake8
- [ ] Document the `loader.yml` wiring snippet for Story 7.4's executor (in this plan + here)
- [ ] Verify end-to-end per Story 7.5 verification checklist

---

## FEATURE-011 — Loader Lambda CI/CD Workflow

### Status

PROPOSED

### Background

Story 7.1 (ADR-010) established OIDC + app-deploy IAM roles. Stories 7.2 and 7.3 (FEATURE-008, FEATURE-009) added Terraform and backend Lambda CI pipelines. Story 7.4 adds the Loader Lambda's PR-test + dev-deploy + prod-promote pipeline. The Loader Lambda is distinct from the backend Lambda: it's a one-shot migration orchestrator invoked via `aws lambda invoke --payload '{"action":"migrate"}'` during deploys, not a stateless request handler.

### Problem

1. Today, migrations are run manually (`alembic upgrade head`) or not at all in CI. Every deploy's risk includes "are migrations up to date?" as a hidden concern.
2. Schema amendments (new columns, type changes) are validated via code review + the FEATURE-007 touch-point checklist, but there's no automated check that migrations are syntactically correct until they run in prod (first time touched).
3. Pre-flight checks (RDS reachability) are manual; infrastructure problems surface at the wrong moment (during migration, not during deploy validation).

### Constraints

- OIDC trust pattern must match ADR-010 (`environment:` declaration is mandatory on every deploy job — sub-claim gate).
- App-deploy role permissions must not be expanded. IAM audit confirms current role already grants `lambda:UpdateFunctionCode`, `s3:PutObject` to lambda-artifacts bucket, and `rds:DescribeDBInstances` — sufficient.
- Loader zip with Alembic + shared models + migrations is large; must be S3-staged like backend (inline ~50 MB limit).
- Loader invocation payload is JSON; response parsing must handle edge cases (non-JSON response, error key, non-200 status).
- Schema-amendment lint (Story 7.5 / FEATURE-010) must run in this PR job as a cross-check (migration syntax validated at PR time, not first-deploy time).

### Proposed Solution

1. New workflow `.github/workflows/loader.yml` with three jobs: `pr-checks` (lint + pytest against Postgres service container + schema-amendment lint), `deploy-dev` (fires on `pull_request` events whose base is `main` — preview-deploy pattern), `deploy-prod` (fires on `push` to `main` after PR merge, or on `workflow_dispatch`; gated by prod GitHub Environment approval).

2. Loader Lambda function names hardcoded in workflow-level `env:` block (`LOADER_LAMBDA_DEV: nbajinni-dev-loader`, `LOADER_LAMBDA_PROD: nbajinni-prod-loader`) — not stored as GH secrets. Same rationale as FEATURE-008 and FEATURE-009.

3. Zip staged through `s3://nbajinni-<env>-lambda-artifacts/loader.zip`, then deployed via `aws lambda update-function-code --s3-bucket / --s3-key`. Handles large zips with Alembic migrations + /shared + dependencies.

4. Pre-deploy RDS reachability check via socket connectivity test (Python) — fails fast if infrastructure is unavailable. Reads RDS endpoint from `terraform output -raw rds_endpoint`.

5. Loader invocation with `{"action":"migrate"}` — captures output, parses JSON response, checks for error keys and HTTP status. Timeout set to 5 min (300 sec) to cover slow migrations.

6. Schema-amendment lint (FEATURE-010) wired into PR job — exact copy of the step from Story 7.5's backend.yml snippet. Validates touch-points (model, migration, parser, DATE_COLUMNS) before the PR is merged.

7. PR pytest uses Postgres 16 service container + schema bootstrap (`Base.metadata.create_all()`), mirroring backend.yml. Carve-out from ADR-005 documented in FEATURE-009 applies here as well.

### Watch Points

- `deploy-prod` will fail until `infra/environments/prod/` exists AND `nbajinni-prod-loader` Lambda + `nbajinni-prod-lambda-artifacts` bucket are provisioned. Documented inline in the workflow; matches Stories 7.2–7.3 wire-but-fail shape.
- RDS pre-flight checks for connectivity via socket — if RDS is restarting / upgrading, migration fails. Intentional (don't run migrations on unstable DB). Operator must investigate delay and re-run workflow.
- The Loader invocation response parsing is defensive (handles non-JSON, missing fields, non-200 status). If Lambda response format changes, workflow may need updates.
- Zip assertion checks for `alembic/` in the archive; if future refactoring moves migrations elsewhere, the assertion must be updated.
- Poetry version pinned in workflow (`pipx install poetry==1.8.3`); bump in sync with local dev.

### Tasks

- [x] Create `.github/workflows/loader.yml` with `pr-checks`, `deploy-dev`, `deploy-prod` jobs
- [x] Hardcode loader Lambda function names + artifacts bucket names in workflow `env:` (no GH secrets for these)
- [x] Add Postgres 16 service container and schema-bootstrap step for PR tests
- [x] Wire schema-amendment lint from FEATURE-010 into PR job
- [x] Add RDS pre-flight connectivity check before migration invocation
- [x] Add Loader invocation with `{"action":"migrate"}` and response parsing
- [x] Add zip content assertion (`/shared` + `alembic`) before deploy
- [x] Update `docs/project-plan.md` Story 7.4 task checkboxes (rewrite the "store function names as secrets" line)
- [ ] Verify end-to-end: trivial loader PR exercises `pr-checks`, merge to main exercises `deploy-dev`, `workflow_dispatch` exercises `deploy-prod` (expected to fail until prod env exists)
- [ ] After prod env exists in a future story, manually run `Actions → Loader CI → Run workflow` to confirm prod path and flip this FEATURE to IMPLEMENTED

---

## FEATURE-012 — Observability Provisioning (Log Groups, Alarms, SNS, Dashboard)

### Status

PROPOSED

### Background

Story 7.1 (ADR-010) established OIDC + per-env IAM roles. Stories 7.2–7.6 wired Terraform, backend, Loader, schema-lint, and frontend CI. Story 7.7 closes the operational feedback loop: log retention, alarms, alert routing, and a single-pane dashboard. **No new GitHub workflow** — Story 7.2's `terraform.yml` deploys the new resources alongside the rest of `environments/dev`. While auditing the existing state, a latent bug was found in the `lambda` module (log group named to a non-emission target) and is fixed in the same PR.

### Problem

1. `aws_cloudwatch_log_group` in `modules/lambda/main.tf` is named `/aws/lambda/${var.function_name}-logs` (e.g. `/aws/lambda/request-handler-logs`), but the Lambda function name is `${var.project_name}-${var.environment}-${var.function_name}` (e.g. `nbajinni-dev-request-handler`). Lambda's default log group is `/aws/lambda/<full_function_name>`. The Terraform-managed log group is orphaned with no log streams; the actual log group is AWS-auto-created with no retention policy. Story 7.7's "log groups with retention policies" deliverable cannot be met without fixing this.
2. There is no alarm path — Lambda errors, slow responses, RDS connection saturation, and Loader failures are invisible until a human opens the CloudWatch console.
3. There is no alert routing — even with alarms, there's nowhere for them to fire to.
4. There is no single-pane dashboard — debug context is spread across Lambda Insights, RDS Performance Insights, CloudFront monitoring, and per-Lambda log groups.
5. The Loader Lambda has no machine-readable "last successful run" signal beyond Invocations − Errors metric math (which can't distinguish a successful `load` from a no-op `migrate`).

### Constraints

- Must deploy via existing `terraform.yml` (Story 7.2 / FEATURE-008) — no new workflow file.
- Must not expand the TF-CI IAM role's permissions. Verified `PowerUserAccess` covers all CloudWatch + SNS actions.
- Sensitive `alert_email` must follow the same handling pattern as `db_username` / `db_password` (manual GitHub env secret, never in Terraform state).
- Log group rename forces destroy+recreate. AWS-side auto-created log group must be `terraform import`-ed to avoid `AlreadyExistsException` on apply.
- SNS email subscriptions cannot be auto-confirmed — operator must click the AWS-sent link.

### Proposed Solution

1. Rename `aws_cloudwatch_log_group.lambda_log` in `modules/lambda/main.tf` to `/aws/lambda/${var.project_name}-${var.environment}-${var.function_name}`. Add `log_retention_days` variable (default 14). Override to 30 days for `module.lambda_loader`.
2. New `infra/modules/observability/` module: SNS topic + email subscription, four CloudWatch alarms (backend error rate via metric math, backend duration p99, Loader failure, RDS connection saturation), one log metric filter for Loader success, one dashboard.
3. Expose `aws_db_instance.main.identifier` as a new RDS module output (required for the `DatabaseConnections` metric dimension).
4. Re-export the dashboard name and SNS topic ARN at `environments/dev/outputs.tf` for operator visibility after apply.
5. New `alert_email` variable in `environments/dev/variables.tf`, passed via `TF_VAR_alert_email` from a manually-set GitHub Environment secret `ALERT_EMAIL`.
6. Loader Lambda emits one log line `"Loader run complete"` on successful exit; the log metric filter publishes `LoaderRunSuccess` to namespace `NBAJinni/Loader`.
7. State reconciliation (one-time, per env): `terraform state rm` the orphaned log group, `terraform import` the AWS-auto-created log group at its new module address.

### Watch Points

- The log group rename is destructive at the state level (forces `replace`) and at the AWS level it requires `terraform import` to avoid `AlreadyExistsException`. Documented in Story 7.7's Open Items.
- Email subscription stays in `PendingConfirmation` until the operator clicks the confirmation link. Alerts fired before confirmation are silently dropped (AWS does NOT queue them). After confirmation, the operator should manually trigger one alarm to verify end-to-end delivery.
- `cloudfront_distribution_id` is passed by the observability module to the dashboard widget, but the CloudFront 5xx metric must be queried against `us-east-1` regardless of `var.aws_region` — hardcoded in Widget 3.
- The `LoaderRunSuccess` metric depends on the exact log substring `"Loader run complete"`. If Loader's logging format changes, the dashboard widget goes silent — no alarm fires, but the dashboard becomes misleading. Mitigated by the `# CloudWatch dashboard signal — do not rename` comment next to the log line in `loader/main.py`.
- `PowerUserAccess` is a managed policy. AWS could in theory remove a CloudWatch/SNS action from it; if a future apply fails with `AccessDenied`, the custom policy (`infra/policies/github_oidc_terraform_policy.json.tpl`) may need a targeted addition.

### Tasks

- [x] Rename log group in `infra/modules/lambda/main.tf`; add `log_retention_days` variable
- [x] Add `instance_identifier` output to `infra/modules/rds/outputs.tf`
- [x] Create `infra/modules/observability/` (variables.tf, main.tf, outputs.tf)
- [x] Wire module into `infra/environments/dev/main.tf`; override loader retention to 30; re-export outputs
- [x] Add `alert_email` variable to `infra/environments/dev/variables.tf` (and `.tfvars.example`)
- [x] Emit `"Loader run complete"` log line in `loader/main.py`
- [x] Append `TF_VAR_alert_email` to all job env blocks in `.github/workflows/terraform.yml`
- [x] Extend `infra/environments/shared/README.md` manual-secrets section to include `ALERT_EMAIL`
- [ ] Operator: set `ALERT_EMAIL` secret on dev (and prod, proactively) GitHub Environments
- [ ] Operator: pre-apply state reconciliation (`terraform state rm` + `terraform import` for log groups)
- [ ] Verify end-to-end: apply, click email confirmation, trigger a test alarm

---

## FEATURE-013 — Dynamic Lambda Dependency Bundling from Poetry

### Status

PROPOSED

### Background

Both Lambda packaging scripts build their deployment zips by `pip install`-ing a **hardcoded list** of packages into `dist/`: `scripts/package_backend.sh:18-30` and `scripts/package_loader.sh:18-25`. Each list must be manually kept in sync with its package's `pyproject.toml`. This drift is invisible to the test suite (CI runs `poetry install`, which pulls in every declared dependency) and to the deploy step (the zip uploads and `update-function-code` succeeds regardless of contents) — it surfaces only when the Lambda cold-starts and a runtime `import` fails, which is caught last in the pipeline by the `/health` smoke test (FEATURE-009).

This was hit in practice: the rate-limiting work added `from slowapi import ...` to `backend/app/main.py` and declared `slowapi` in `backend/pyproject.toml`, but did not add `slowapi` to `package_backend.sh`'s list. The deployed Lambda raised `Runtime.ImportModuleError` on every invocation; `/health` returned 500; the smoke test failed all three attempts. It was quick-fixed by appending `slowapi` to the hardcoded list (`scripts/package_backend.sh:21`) — a patch that does not address the underlying drift hazard and leaves the same trap for the next dependency.

### Problem

- Two hardcoded dependency lists (`package_backend.sh`, `package_loader.sh`) must be manually synchronized with two `pyproject.toml` files. The source of truth (Poetry) and the deployed artifact (the zip) can diverge with no signal until cold-start.
- The failure mode is maximally delayed and expensive: green tests, green deploy, red smoke test — the regression is only observable at the end of the pipeline against already-deployed code.
- **Latent landmines (under-bundling).** `passlib`, `python-jose`, and `python-multipart` are declared runtime deps in `backend/pyproject.toml` that are absent from `package_backend.sh`'s list. They are harmless only because no currently-loaded module imports them; wiring up auth will reproduce the `slowapi` cold-start failure verbatim.
- **Over-bundling.** The inverse problem also exists: `uvicorn` (a local-dev server — Mangum is the Lambda adapter) and `alembic` (migrations, owned by the Loader) are backend main-group deps that the request handler does not need at runtime. A naive "bundle everything in main" approach would inflate the backend zip.
- The two Lambdas have genuinely different runtime sets (backend needs `fastapi`/`mangum`/`slowapi`/`nba-api`; loader needs `alembic` and no web framework), so a single shared requirements file cannot serve both.

### Constraints

- `nbajinni-shared` is a local path/editable dependency (`{ path = "../shared", develop = true }` in both `pyproject.toml` files) and is bundled separately via `rsync` of `nbajinni_shared/` (ADR-001). `poetry export` emits it as a path/editable entry that will not `pip install --target` cleanly from the Lambda build cwd — it must be excluded from any generated requirements, and the existing `rsync` of `nbajinni_shared/` must be preserved unchanged.
- The CI zip-content assertions must still pass: backend asserts `nbajinni_shared/` + `nba_api/` are present (`.github/workflows/backend.yml:157-162` and `:229-234`); loader asserts `nbajinni_shared/` + `alembic/`.
- Dev dependencies (`pytest`, `pytest-asyncio`, `httpx`, `black`, `flake8`, `isort`) must never be bundled — the export/install must scope to runtime deps only.
- The `deploy-dev` and `deploy-prod` jobs in `backend.yml` (and their loader equivalents) currently install only `setup-python` + Terraform + AWS creds — they do **not** install Poetry (only the `pr-checks` job does, `backend.yml:80-81`). If the packaging script calls `poetry export` at build time, those deploy jobs must gain a Poetry install step; the alternative is to commit a generated requirements file consumed by the script, guarded by a CI staleness check.
- Poetry is pinned to `1.8.3` in CI (`pipx install poetry==1.8.3`). `poetry export` emits a deprecation notice under 1.8 and may require the `poetry-plugin-export` plugin on newer Poetry — the chosen mechanism must pin/document this.
- The fix must apply consistently to **both** packaging scripts; fixing only the backend leaves the loader exposed to the identical failure.

### Proposed Solution

Derive each Lambda's bundled dependencies from its `pyproject.toml` so the artifact can never silently drift from the declared dependency set. Two candidate mechanisms — the choice is a decision point for the team, not prescribed here:

1. **Poetry dependency groups.** Define an explicit `lambda-runtime` grouping per package (e.g. move `uvicorn`/`alembic` out of the backend's runtime set, keep `fastapi`/`mangum`/`slowapi`/`nba-api` in it) and export/install only that group. Most precise — solves both under- and over-bundling — but requires restructuring the `pyproject.toml` groups and is the larger change.
2. **Plain export of the main group.** `poetry export --only main --without-hashes -f requirements.txt`, filter out the local path dep (`nbajinni-shared`), then `pip install -r requirements.txt --target "$DIST_DIR"`. Simplest change; still bundles `uvicorn`/`alembic` unless they are moved to a non-runtime group, so it trades a little zip size for simplicity.

Either way: retain the existing `rsync` of `nbajinni_shared/` (and the loader's `alembic.ini` + `alembic/` copy), retain the CI zip-content assertions, and ensure the deploy jobs have whatever tooling the script needs at build time. Shared logic between the two scripts may be factored into a small helper if it reduces duplication — a minor judgment call, not a requirement.

**Decision points to resolve before implementation** (flagged, not decided here):

- (a) Dependency groups vs. plain `--only main` export.
- (b) Whether to accept over-bundling `uvicorn`/`alembic` in the backend zip or move them into a non-runtime group.
- (c) Whether deploy jobs install Poetry at build time, or whether a generated `requirements.txt` is committed per package and guarded by a CI staleness check.
- (d) Optional defense-in-depth: a CI step that imports the handler module (`app.main`) in a clean environment to catch any missing runtime dependency *before* the smoke test, rather than relying on declared-deps parity alone.

### Watch Points

- The temporary hardcoded `slowapi` line (`scripts/package_backend.sh:21`) must be removed when this lands, so the dynamic resolution and the manual patch do not coexist.
- The local path dep (`nbajinni-shared`) must be filtered from any exported requirements; otherwise `pip` will attempt to resolve `../shared` from the Lambda build cwd and fail.
- Export with hashes (`poetry export` default) fails `pip install` if any transitive dep lacks a hash — use `--without-hashes`.
- Backend and loader runtime sets diverge — a single shared requirements file would wrongly bundle `fastapi` into the loader. Keep resolution per-package.
- `poetry export` deprecation / plugin requirement under the pinned Poetry `1.8.3`.

### Tasks

- [ ] Decide the mechanism (dependency groups vs. plain `--only main` export) and how deploy jobs obtain runtime deps (build-time Poetry vs. committed + staleness-checked `requirements.txt`)
- [ ] Rewrite `scripts/package_backend.sh` to derive runtime deps from `backend/pyproject.toml`, excluding the local path dep and retaining the `nbajinni_shared/` rsync
- [ ] Apply the same approach to `scripts/package_loader.sh` (retaining the `alembic.ini` + `alembic/` copy)
- [ ] Remove the temporary hardcoded `slowapi` line from `scripts/package_backend.sh` once dynamic resolution covers it
- [ ] If build-time Poetry is chosen: add an "Install Poetry" step to the `deploy-dev`/`deploy-prod` jobs in `.github/workflows/backend.yml` and `.github/workflows/loader.yml`; otherwise commit generated requirements per package and add a CI staleness check
- [ ] Confirm the existing zip-content assertions still pass (`nbajinni_shared/` + `nba_api/` for backend; `nbajinni_shared/` + `alembic/` for loader)
- [ ] (Optional) Add a clean-environment handler-import check in CI as defense-in-depth before the smoke test
- [ ] Verify end-to-end: add a throwaway runtime dep to `pyproject.toml`, confirm it appears in the zip with no script edit, and confirm the smoke test stays green

---
