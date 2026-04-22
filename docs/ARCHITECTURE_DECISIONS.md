# Architecture Decision Records

This file documents significant architectural decisions made during the development of NBAJinni, including deviations from the original project plan. Each entry captures the context, reasoning, and consequences of the decision so that the rationale is never lost as the project evolves.

---

## ADR-001 — Introduce a `/shared` package for common database models and utilities

**Date:** Epic 3  
**Status:** Accepted

### Context

The original project plan treated `/backend` and `/ingestion` as fully independent packages, each responsible for their own code. As implementation began, it became clear that both packages needed identical SQLAlchemy models to perform database operations against the same PostgreSQL schema. Maintaining duplicate model definitions across two packages would create a brittle codebase — any schema change would require synchronized updates in two places, and drift between the two definitions would be a likely source of bugs.

### Decision

Introduce a `/shared` package at the monorepo root that owns all database models, the SQLAlchemy session initializer, and any utility functions required by more than one package. Both `/backend` and `/ingestion` declare `/shared` as a local dependency and import from it directly.

### Consequences

**Positive:**

- Single source of truth for all database models — schema changes are made once.
- Eliminates the risk of model drift between the API and ingestion layers.
- Establishes a clear, intentional boundary: `/shared` for common concerns, `/backend` and `/ingestion` for their own logic.

**Negative / Watch points:**

- Adds a third package to manage in the local dev setup and deployment pipeline.
- Lambda packaging for `/ingestion` must now include `/shared` as a bundled dependency — this needs to be accounted for in the zip packaging step (Story 4.4) and the backend Lambda packaging step (Story 5.1).
- Care must be taken not to let `/shared` become a catch-all dumping ground. Only genuinely shared code belongs here; package-specific logic stays in its own package.

**Impact on project plan:**

- Story 4.4 (Lambda packaging) and Story 5.1 (FastAPI project setup) should be updated to account for bundling `/shared` as part of each Lambda deployment artifact.

---

## ADR-002 — Replace api-sports.io with the `nba_api` Python package

**Date:** Epic 3  
**Status:** Accepted

### Context

The original data ingestion design (Epics 1–4 of the project plan) was built around the api-sports.io NBA endpoint. During implementation it was discovered that the free tier of api-sports.io restricts access to historical seasons only — current season data is locked behind a paid plan. This is a fundamental incompatibility with NBAJinni's core purpose: providing real-time statistics to inform predictions for upcoming games. An app built on prior-season data would not be useful for its intended audience.

The additional constraint of 100 API calls per 24 hours, while manageable with careful batching, compounded the concern: the budget was being spent on data that didn't serve the product goal.

### Decision

Replace api-sports.io with the [`nba_api`](https://github.com/swar/nba_api) Python package. `nba_api` is open source, completely free, and interfaces directly with the official NBA.com APIs, providing current season game logs, player statistics, team rosters, and injury data with no call budget ceiling.

The Python API client class planned in Story 4.1 (wrapping `httpx` with key injection, rate limiting, and call counting) is no longer needed in its original form. It is replaced by direct usage of `nba_api` endpoints, with a lightweight wrapper retained for error handling, logging, and any request throttling needed to stay within NBA.com's informal rate limits.

### Consequences

**Positive:**

- Current season data is fully accessible, making the app viable for its intended use case.
- No API key management, no Secrets Manager entry for a third-party API key, no call budget to track.
- The DynamoDB call-counter utility planned in Story 4.1 is no longer necessary, simplifying the ingestion architecture.
- `nba_api` is actively maintained and widely used in the NBA analytics community — endpoint reliability is well understood.

**Negative / Watch points:**

- NBA.com does not publish an official rate limit, but aggressive polling can result in temporary IP blocks. The ingestion layer must include polite request throttling (e.g., small delays between calls) to avoid this.
- `nba_api` is an unofficial client — if NBA.com changes their internal API structure, the package may break until maintainers release an update. This is an accepted risk given the alternative.
- Response schemas from `nba_api` differ from api-sports.io — all ingestion transformation logic must be written against the `nba_api` data structures rather than the ones originally anticipated.

**Impact on project plan:**

- Story 4.1: The api-sports.io client class, Secrets Manager API key setup, and DynamoDB call counter are removed from scope. Replace with a lightweight `nba_api` wrapper focused on throttling, error handling, and structured logging.
- Story 2.3: Remove the Secrets Manager entry for the api-sports.io API key from the Terraform plan.
- The data architecture notes at the top of the project plan (describing the 100 calls/day constraint and batching strategy) are superseded by this decision.

---

## ADR-003 — Defer user authentication and personalization features

**Date:** Epic 4  
**Status:** Accepted

### Context

The original project plan included JWT-based user authentication (register, login, protected routes) as a core deliverable in Epic 5, with the intent to support personalization features — specifically player and team watchlists and a persistent comparison tool. During feature planning for EPIC 4, the question was raised as to what auth actually buys the user in the current scope. NBAJinni's core value is read-only access to statistics; none of the primary stat views require a user identity. The personalization features that would justify auth (watchlists, saved comparisons) are additive enhancements, not core functionality.

Building auth now would consume a meaningful portion of Epic 5 and introduce frontend complexity (auth context, protected route wrappers, login/register views) that delivers no value to a user who just wants to look up player stats.

### Decision

Defer authentication and all personalization features to a future iteration. The `users` table will be created and migrated now to reserve the schema slot, but will remain empty and unused. No auth endpoints, no JWT middleware, no login/register views, and no user-associated tables (`user_tracked_players`, `user_tracked_teams`) will be built at this time. All routes will remain public for the initial release.

### Consequences

**Positive:**

- Epic 5 scope is meaningfully reduced, allowing more focus on the stats endpoints that deliver core user value.
- The frontend is simpler — no auth context, no protected route logic, no login/register views to build and test.
- The app is fully functional for its primary use case without auth.

**Negative / Watch points:**

- The app will have no rate limiting at the user level — API-level rate limiting via `slowapi` (Story 8.2) is therefore more important and should not be skipped.
- When auth is eventually added, the frontend will need an auth context layer retrofitted around existing views. This is straightforward but should be scoped as its own dedicated sprint rather than bolted onto another epic.

**Reversibility:**
Auth is one of the more reversible deferrals possible in this codebase. The data model is global and read-only — no existing tables are user-scoped — so adding auth later means new tables and new routes only, with no modifications to existing schema or endpoints. The `users` table being pre-migrated further reduces the footprint of that future work.

**Impact on project plan:**

- Story 5.2 (Authentication endpoints) is removed from Epic 5 scope.
- Story 6.2 (Authentication views) is removed from Epic 6 scope.
- `user_tracked_players` and `user_tracked_teams` migrations are removed from the EPIC 4 schema amendment story.
- The `users` table migration is retained but noted as unpopulated.
- Story 8.2 (Security hardening) rate limiting task is elevated in priority given the absence of user-level access control.

---

## ADR-004 — Ingestion Lambda topology, throttle strategy, and per-game commit model for cold-start resilience

**Date:** Epic 4 / Story 4.4
**Status:** Accepted

### Context

The ingestion Lambda (`ingestion/main.py`) serves two fundamentally different workload shapes from the same codebase:

- **Nightly steady-state runs** process 0–15 completed games per day, finishing in under 30 seconds.
- **First-start cold-start runs** must ingest the entire current season up to the current date on the first deploy — approximately 1,170 games at the point mid-season, taking 20+ minutes of wall time at safe throttle levels.

Three interrelated problems emerged when designing for both workloads:

1. **AWS Lambda has a hard 15-minute timeout ceiling.** A full-season first-start run cannot fit in a single Lambda invocation regardless of throttle tuning. The original plan of "set a large timeout and let it run" is not viable.

2. **NBA.com's informal rate limit tightens under sustained high call volume.** Testing during Story 4.3 showed that aggressive or default throttle timings (≤1s) resulted in retry exhaustion during large-volume runs. The NBA API requires _longer_ pauses per call under high volume, not shorter — counterintuitive to standard rate-limit thinking. Empirically, 5–10s throttles were needed to complete full-season ingestion without exhausting retries.

3. **The original single-transaction model loses all partial progress on timeout.** `run_nightly()` wrapped `ingest_games()` and all downstream steps in one `session.begin()`. If the Lambda timed out mid-run, every partially-ingested game was rolled back. Combined with the fact that first-start requires multiple Lambda invocations to complete, this meant each invocation would restart from zero — making convergence impossible.

A fourth discovery made as part of this work: the existing EventBridge target for the nightly cron did not pass an `input` payload, so every scheduled invocation landed in the `unknown_job` branch of the handler and logged an error. The nightly job had never successfully executed on schedule.

### Decision

Four interlocking changes were made to resolve these problems:

**1. Split into two Lambda functions.** The single `lambda_ingestion` module is supplemented by a new `lambda_ingestion_first_start` module, both deploying the same zip artifact but with different configurations:

|                   | `daily-ingestion`           | `ingestion-first-start` |
| ----------------- | --------------------------- | ----------------------- |
| Timeout           | 300s                        | 900s (max)              |
| Memory            | 512 MB                      | 512 MB                  |
| Trigger           | EventBridge cron (9 AM UTC) | Manual invocation only  |
| Throttle env vars | 1.0s / 1.0s                 | 5.0s / 5.0s             |

Separating the two functions preserves duration-based observability on the nightly (an invocation over ~60s is anomalous and alertable), caps the hang/runaway blast radius on the short-running function, and gives the long-running first-start invocation the full 900s ceiling without polluting the nightly's metrics.

**2. Make wrapper throttles configurable per Lambda via environment variables and a `reconfigure()` method.** `NbaApiWrapper` now reads `NBA_API_BACKOFF_THROTTLE` and `NBA_API_CALL_COUNT_THROTTLE` at construction time, with a `reconfigure(back_off_throttle, call_count_throttle)` method that mutates the instance in place without resetting `call_count`. The `reconfigure()` call is used in `run_first_start()` to apply conservative throttles for local development runs where Lambda env vars are not set; in production, the `ingestion-first-start` Lambda's env vars (5.0s/5.0s) are already applied at construction. The `daily-ingestion` Lambda uses 1.0s/1.0s defaults. Throttle policy is set at the Lambda level (terraform) rather than hardcoded in application logic.

**3. Refactor `ingest_games()` to commit per game.** Each game's player stats, team stats, and status update are wrapped in their own `session.begin()` transaction that commits on completion. If the Lambda times out mid-run, all previously committed games are preserved in the database. The existing `game.status` field (1 = unprocessed, 3 = complete) serves as the idempotency checkpoint — subsequent invocations of `run_first_start()` resume from the remaining `status == 1` games. A full-season first-start converges in 2–3 manual invocations at 5s throttles.

To preserve test isolation with per-game commits, the shared test session fixture in `conftest.py` was updated to use `join_transaction_mode="create_savepoint"`. This ensures `session.commit()` inside `ingest_games()` releases a savepoint against the outer connection transaction rather than committing to the database, so the fixture's `connection.rollback()` at teardown still cleans up correctly.

**4. Fix the EventBridge input payload.** The `event_bridge` terraform module was updated to accept an `input` variable, and the nightly rule was updated to pass `{"job": "games_stats_nightly"}` as the Lambda event. Without this, the nightly cron was effectively a no-op.

### Consequences

**Positive:**

- First-start cold-start is now safe and resumable. Each invocation commits progress game-by-game; a timeout is a pause, not a reset.
- Nightly and first-start workloads have cleanly separated observability profiles and failure blast radii.
- Throttle policy is owned at the infrastructure level (env vars per Lambda) with a code-level override for local development — no magic constants buried in application logic.
- The EventBridge fix means the nightly cron will actually execute its job for the first time.
- `ingest_games()` is now robust to invalid box score data via `InvalidGameData` exception handling, which rolls back a single game without affecting others.

**Negative / Watch points:**

- First-start requires **2–3 manual `aws lambda invoke` calls** to converge on a fresh mid-season deploy. This is operational overhead with no automation — acceptable for a one-time event per deploy, but should be noted in the deployment runbook.
- The 5s throttle values for first-start are empirically derived from prior testing, not a published limit. If NBA.com tightens further, these may need to be increased to 10s. Monitor `retries_exhausted` logs during first-start runs.
- `ingestion-first-start` shares the same IAM role and VPC config as `daily-ingestion`. When FEATURE-005 (historical season backfill) is implemented, it will likely extend `ingestion-first-start` or share its infrastructure — care should be taken to scope any FEATURE-005 changes to the long-running Lambda only.
- The single-transaction model is preserved for biweekly roster and schedule jobs (`run_roster_biweekly`, `run_schedule_biweekly`). These are small enough (1–2 API calls each) that per-game commits are unnecessary, but if either grows in scope, the same per-item commit pattern should be applied.

**Impact on project plan:**

- Story 4.4 (Lambda packaging and deployment) should note that two Lambda functions are deployed from a single zip artifact, and that first-start requires manual sequential invocations to complete initial season backfill.
- FEATURE-005 (historical season backfill) should be implemented within the `ingestion-first-start` Lambda or a sibling thereof — not in `daily-ingestion`.

_Lambda topology superseded by ADR-005; per-game commit and throttle strategies remain in effect for local execution._

---

## ADR-005 — Hybrid local-cloud ingestion with S3-mediated sync

**Date:** Epic 4 / Story 4.4  
**Status:** Accepted

### Context

Story 4.4 (Lambda packaging and deployment) surfaced a fundamental networking constraint that blocks the original fully-serverless ingestion design.

Lambda functions inside a VPC cannot reach the public internet without a NAT gateway. The ingestion Lambda requires both internet access to call the NBA.com API and VPC access to reach the RDS instance in a private subnet. The `map_public_ip_on_launch` setting on public subnets does not help — AWS Lambda uses Hyperplane ENIs that never receive public IPs regardless of subnet configuration.

A managed NAT gateway would satisfy both requirements but costs approximately $32/month — disproportionate for a portfolio project where cost efficiency is a stated goal. Alternative approaches were considered:

- **NAT instance (t4g.nano):** ~$3/month, but adds EC2 management overhead and single point of failure
- **fck-nat AMI:** Same cost as NAT instance, pre-configured, but still requires EC2 management
- **Split Lambda architecture:** One Lambda outside VPC for API calls, another inside VPC for DB writes — adds complexity and intermediate storage
- **EC2-based ingestion:** ~$3/month, but changes the architecture entirely and adds instance management

The chosen approach — local ingestion with S3-mediated sync — costs $0 in incremental AWS spend, reuses all existing ingestion code unchanged, and simplifies Lambda networking requirements.

### Decision

Replace the fully-serverless ingestion model with a hybrid local-cloud architecture. The data flow becomes:

1. **Local cron** triggers ingestion jobs (nightly game stats, bi-weekly roster/schedule) on the developer's machine.
2. **Ingestion pipeline** (existing code, completely unchanged) fetches from NBA.com API and upserts into local PostgreSQL running in Docker.
3. **Export script** (new) queries each table from local PostgreSQL and writes JSON files to a local directory.
4. **S3 upload** (new) pushes the JSON files to a designated S3 bucket.
5. **Loader Lambda** (new) is triggered by manual invocation, downloads the JSON files, and performs truncate + insert into RDS. The Lambda supports two actions via the event payload:
   - `{"action": "load"}` — truncate + insert data from S3 JSON exports
   - `{"action": "migrate"}` — run Alembic migrations against RDS before loading data (used on first deploy or schema changes)

The Loader Lambda lives inside the VPC but requires only two things: access to RDS (via private subnet routing) and access to S3 (via a free VPC Gateway Endpoint). It does not need internet access, eliminating the NAT gateway requirement entirely.

**Data format choice:** JSON was selected over CSV because `json.dump(default=str)` handles date, datetime, and decimal serialization automatically. On import, only date fields require parsing back — integers, booleans, and nulls survive the JSON round-trip as their native types. This results in approximately 20–30 fewer lines of type coercion code compared to CSV.

**Load strategy choice:** Truncate + insert (full table replacement) was selected over row-by-row upsert for simplicity. This eliminates `ON CONFLICT` clause logic and primary key detection. The brief data unavailability during the truncate-insert window is acceptable if sync runs during off-hours. As a side benefit, the S3 JSON exports serve as daily point-in-time backups that can be used for recovery.

**Table ordering:** Both export and import must respect foreign key dependencies. Tables are deleted in reverse dependency order (leaf tables first) and inserted in forward dependency order (root tables first): Season → Team → Player → Game → PlayerGameStats, TeamGameStats → PlayerSeasonAverages, TeamSeasonAverages → Standings.

### Components Changed

**Removed from scope:**

- `lambda_ingestion` (daily-ingestion) — ingestion now runs locally, not in Lambda
- `lambda_ingestion_first_start` — cold-start backfill handled locally
- `event_bridge` module for ingestion cron — replaced by local cron scheduling
- NAT gateway / NAT instance — Loader Lambda has no internet requirement

**New components:**

- `scripts/export_to_json.py` — queries local PostgreSQL, writes one JSON file per table
- `scripts/upload_to_s3.py` — pushes JSON files to S3 (may be combined with export script)
- `scripts/package_loader.sh` — builds the Loader Lambda deployment zip, bundling `/shared` and Alembic artifacts
- `loader/` package — new Lambda that downloads JSON from S3 and loads into RDS; includes `migrate` action for schema management
- S3 bucket or prefix for data exports — stores JSON files with optional versioning for backup retention
- S3 VPC Gateway Endpoint — added to `infra/modules/vpc/`, enables Lambda to reach S3 without NAT (free)

**Modified components:**

- `infra/environments/dev/main.tf` — remove `lambda_ingestion`, `lambda_ingestion_first_start`, and `event_bridge` module calls; add Loader Lambda module, S3 bucket resource, and S3 VPC endpoint
- `infra/modules/vpc/main.tf` — add `aws_vpc_endpoint` resource for S3 gateway
- `shared/nbajinni_shared/session.py` — must support Lambda environment by assembling `DATABASE_URL` from `DB_HOST`, `DB_PORT`, `DB_NAME` plus credentials from environment variables or Secrets Manager; this change is a shared prerequisite for both Loader Lambda and Backend Lambda
- `shared/alembic/` — Alembic configuration and migrations relocated from `backend/alembic/` to `/shared`. Both the Loader Lambda (for RDS schema management) and local development now reference the same migration history. The Loader Lambda bundles `alembic.ini` and the `alembic/` directory in its deployment artifact.

**Unchanged components:**

- `ingestion/main.py` — runs locally exactly as written, no modifications needed
- `shared/nbajinni_shared/utils.py` — all ingestion logic unchanged
- `shared/nbajinni_shared/models/*` — models reused by Loader Lambda for inserts
- `lambda_backend` (request-handler) — unaffected, continues serving API from RDS
- RDS instance configuration — remains in private subnet, no changes

### Consequences

**Positive:**

- Zero incremental AWS cost for ingestion infrastructure — no NAT gateway, no always-on EC2, no EventBridge rules for ingestion scheduling.
- Existing ingestion code runs completely unchanged — `ingestion/main.py` and all utility functions in `/shared` simply execute locally instead of in Lambda.
- Daily backups as a side effect — S3 JSON exports provide point-in-time recovery at no additional effort or cost.
- Faster local development iteration — ingestion runs directly on the dev machine with full debugger access, no Lambda deploy/invoke cycle required for testing.
- Simpler Lambda networking — Loader Lambda needs only VPC-internal routing and S3 access, both of which are straightforward to configure.

**Negative / Watch points:**

- Data freshness depends on local machine availability — if the dev machine is offline during scheduled ingestion windows, data becomes stale until the next successful run. The ingestion is idempotent and will catch up, but real-time freshness is not guaranteed.
- Manual operational step introduced — after local ingestion and export, the developer must upload to S3 and optionally trigger the Loader Lambda. This contrasts with the original fully-automated EventBridge design.
- Brief data unavailability during sync — truncate + insert means tables are empty momentarily during the load window. Mitigated by running sync during off-hours when no users are active.
- Historical data risk at local DB layer — if the local PostgreSQL container is lost and the NBA API has since removed data (e.g., stats for a retired player purged from the API), that data is unrecoverable unless restored from S3 JSON backups. Risk is mitigated by retaining S3 exports and by the fact that NBA rarely removes historical game data.

**Reversibility:**

This decision is fully reversible. If cost constraints relax (employer-sponsored AWS credits, paid tier budget, etc.), the original Lambda-based ingestion can be restored by adding a NAT gateway to the VPC, re-deploying `lambda_ingestion` and `lambda_ingestion_first_start` with the existing code, and re-enabling EventBridge cron triggers. The Loader Lambda and S3 sync infrastructure can be retained as a secondary mechanism or removed entirely.

### Impact on project plan

**Confirmed Stack table:**

- Update the Ingestion row from "Python Lambda + EventBridge" to "Local Python + cron, S3 sync via Loader Lambda"

**Repository Structure:**

- Update `ingestion/` description from "Nightly Lambda data pipeline" to "Local ingestion pipeline (runs on dev machine)"
- Add `loader/` directory with description "S3-to-RDS sync Lambda"
- Add export and upload scripts to `scripts/`

**Story 2.3 (Provision compute and API infrastructure):**

- Remove task: "Write Terraform `lambda` module for the ingestion function (separate function)"
- Remove task: "Write Terraform for EventBridge rule (nightly cron) triggering the ingestion Lambda"
- Retain task: "Configure Lambda VPC settings so it can reach RDS" — applies to Loader Lambda and Backend Lambda
- Add task: Write Terraform for Loader Lambda (VPC-attached, S3-triggered or manually invoked)
- Add task: Write Terraform for S3 bucket for data exports
- Add task: Write Terraform for S3 VPC Gateway Endpoint

**Story 4.4 (Lambda packaging and deployment):**

- Original scope is entirely obsolete; replace with new task list for Loader Lambda and sync infrastructure

**Story 5.1 (FastAPI project structure):**

- Add prerequisite: Update `shared/session.py` to support Lambda environment; this change is shared by both Loader Lambda and Backend Lambda

**Story 7.3 (Backend API CI/CD):**

- Add CI/CD for Loader Lambda deployment (package zip with `/shared`, deploy on merge to main)

**Story 8.1 (End-to-end verification):**

- Update verification flow: local ingestion → export JSON → upload to S3 → trigger Loader Lambda → verify data in RDS

**Story 8.3 (Final documentation):**

- Document hybrid architecture with updated diagram
- Document local cron setup for ingestion scheduling
- Document manual sync workflow (export → upload → invoke)
- Document data recovery procedures using S3 JSON backups

**Key Technical Decisions Log:**

- Update "Data freshness" row from "Nightly Lambda (EventBridge)" to "Local cron + S3 sync — cost-optimized hybrid pattern"

---

## ADR-006 — Endpoint redesign from ENDPOINTS.md review, schema fixes, and Story 5.3/5.4 scope shift

**Date:** Epic 5 / Story 5.3–5.4
**Status:** Accepted

### Context

Story 5.3 originally scoped four basic endpoints: `/teams`, `/teams/{id}/roster`, `/players/search`, and `/players/{player_id}`. After 5.3 was merged, `docs/backend/ENDPOINTS.md` was written to reverse-engineer the full API surface from the planned frontend pages (Front Page, Teams Page, Team Page, Game Page, Player Page, and a newly-added Standings Page). The exercise surfaced four concerns that forced a broader redesign than the project plan anticipated:

1. **Endpoint coverage gap.** The original plan's Story 5.4 listed six stats endpoints but no game-detail, head-to-head, top-players preview, or standings endpoints — all of which the planned frontend pages require. Conversely, three originally-planned endpoints (`/players/{id}/vs-matchup?position=`, `/players/{id}/injuries`, `/players/compare?ids=`) had no corresponding page and were speculative.

2. **Existing `GET /games/{game_id}` returned the wrong shape for past games.** It always eager-loaded team `season_averages`, which is only meaningful for a game preview. For completed games the page needs `team_game_stats` (that game's actual box score), not season averages.

3. **`PlayerDetail` over-fetched.** The Story 5.3 implementation eager-loaded every `game_stats` row and every `season_averages` row for the player — potentially hundreds of rows — despite no page consumer needing that bulk data at the detail endpoint.

4. **Two latent SQLAlchemy model bugs would break any endpoint touching standings:**
   - `Team.standing` was typed as a scalar (`Mapped["Standing"]`), but `Standing` has a composite `(season, team_id)` PK — in practice it's a list. `selectinload(Team.standing)` would fail once multiple seasons existed in the database.
   - `Standing.season` was typed `Mapped[int]` but FKs `Season.season: Mapped[str]` — a silent type mismatch.

### Decision

#### Endpoint surface (as implemented against ENDPOINTS.md)

| Endpoint | Page served | Status in plan |
| --- | --- | --- |
| `GET /teams` | Teams | Existing (Story 5.3) |
| `GET /teams/{team_id}` | Team | Formalized under ADR-006 |
| `GET /teams/{team_id}/roster` | Team | Existing (Story 5.3) |
| `GET /teams/{team_id}/games` | Team | New — merges originally-planned games + allgamestats into one endpoint with nested `team_game_stats` (null for unplayed games) |
| `GET /players/search` | All | Existing (Story 5.3) |
| `GET /players/{player_id}` | Player | Existing, **trimmed** to `base + team` only |
| `GET /players/{player_id}/season-averages` | Player | Built (was planned 5.4) |
| `GET /players/{player_id}/last-5-games` | Player | Built (was planned 5.4) — response includes `game_date` + `opponent_team_id` |
| `GET /players/{player_id}/vs-opponent?team_id=` | Player | Built — current season only |
| `GET /players/top/preview` | Front | New — returns `{points, rebounds, assists, steals, blocks}` → top 3 each |
| `GET /games/upcoming` | Front | Pre-existing |
| `GET /games/{game_id}` | Game | **Redesigned** — returns a discriminated union (`GamePreview` vs `GameResult`) |
| `GET /games/{game_id}/playerstats` | Game | New — player box scores for both teams |
| `GET /games/h2h?team_a=&team_b=` | Game | New — symmetric query params, current-season scope |
| `GET /standings` | Standings | New — all 30 teams, current season |
| `GET /standings/preview` | Front | New — top 10 by `win_pct` crossing both conferences |

**Endpoints removed from scope:**

- `/players/{id}/vs-matchup?position=` — no frontend page requires it.
- `/players/{id}/injuries` — injuries table exists but no ingestion pipeline is wired; drop until injuries are planned.
- `/players/compare?ids=` — the compare page (Story 6.5) is dropped from near-term scope along with this endpoint.

#### Design decisions worth preserving

1. **Discriminated union for `GET /games/{game_id}`.** The endpoint returns either `GamePreview` (team standing + season averages for both teams) or `GameResult` (team box-score stats). A `kind: Literal["preview"|"result"]` field on each variant serves as the Pydantic discriminator. `Game.status: int` could not be used directly — Pydantic discriminated unions require a field inspectable during validation, and narrowing `status` into per-variant literals would have required overriding it in every subclass. `kind` is a real field with a default value, not a `@computed_field`; computed fields are output-only and cannot be used as discriminators.

2. **`PlayerDetail` trimmed to `base + team`.** Every per-stat-row consumer now has a dedicated endpoint, eliminating the N+1 over-fetch from the detail endpoint.

3. **Single `/teams/{team_id}/games` endpoint with nested stats.** Merges the originally-planned `/games` + `/allgamestats` pair. Unplayed games return nulls in both stat fields; client-side joins by `game_id` are unnecessary.

4. **Top players preview: sequential queries, not `asyncio.gather`.** `AsyncSession` is not safe for concurrent coroutine access on the same session object. Five sequential queries (one per stat category) accept a minor latency penalty in exchange for session safety. The `games_played >= 10` floor applies only when `max(games_played) across the league >= 10` — at the start of a season with no player yet at 10 games, the floor is disabled so the widget still shows meaningful results.

5. **Lean game payloads.** List endpoints return games with `home_team_id` / `away_team_id` as IDs only — no nested team objects. The frontend caches `/teams` once and joins client-side for name/logo rendering. Keeps list responses tight and avoids duplicating team metadata on every row.

6. **`/standings/preview` crosses conferences.** Top 10 teams by `win_pct` overall, not top 5 per conference, so the front-page widget showcases the best teams regardless of conference. The full conference-grouped table is served by `/standings` on the Standings Page.

7. **Current season inferred from `Standing`.** `get_current_season(db)` queries `max(Standing.season)`. Standings is the smallest seasonal table and is always populated when the season is in progress. When empty (fresh deploy pre-ingest), the helper raises `HTTPException(503, "Season data not yet loaded")` — a degraded-state response rather than a 500 crash.

8. **Endpoints that require current season are not optional.** `/teams/{id}/games`, `/players/top/preview`, `/players/{id}/vs-opponent`, `/games/h2h`, and both standings endpoints all depend on current-season inference. Tests for these endpoints must include a `Standing` fixture.

#### Schema fixes applied to `/shared`

1. **`Team.standing` rewritten as a season-scoped scalar relationship.** The relationship is now defined post-class via a helper function (`_configure_team_standing_relationship()`), using a `primaryjoin` that correlates against `select(func.max(Season.season)).scalar_subquery()`, with `uselist=False` and `viewonly=True`. The post-class configuration pattern is required because SQLAlchemy's string `primaryjoin` evaluator cannot parse Python call chains like `.scalar_subquery()`. A consequence of `viewonly=True`: `Standing.team` can no longer carry `back_populates="team"` — `standing.team = some_team` assignments have no effect on `Team.standing`. Acceptable because standings are only ever written by ingestion, never by API handlers.

2. **`Standing.season` retyped `Mapped[int]` → `Mapped[str]`.** No migration required; Postgres column types already matched `Season.season`. The fix corrects only the Python-side type annotation.

### Consequences

**Positive:**

- Every endpoint documented in `docs/backend/ENDPOINTS.md` is implemented and covered by at least one happy-path test, with a clear mapping back to the frontend page it serves.
- Eliminated two latent SQLAlchemy bugs that would have produced hard-to-diagnose failures once multi-season historical data accumulated.
- Removed speculative endpoints whose purpose was unclear, reducing surface area to test and maintain.
- `PlayerDetail` now loads in O(1) rows for the header card instead of O(seasons × games) — a meaningful win once historical data accumulates.
- Discriminated union for game detail lets the frontend narrow type at parse time without extra round trips or schema-guessing.

**Negative / Watch points:**

- Frontend is now fully responsible for caching `/teams` and joining client-side for game lists. If a team is renamed or re-logoed mid-session, stale cache could briefly show incorrect info — mitigate by invalidating on navigation to `/teams`.
- `get_current_season` raising 503 is appropriate for a pre-ingest deploy state but would surface as a user-visible degradation if the standings table ever goes empty mid-season due to ingestion failure. Monitoring should alert on 503s from these endpoints.
- The `Team.standing` `primaryjoin` with a correlated subquery is unusual. SQLAlchemy emits it as a subquery inside an `IN (...)` lateral — worth smoke-testing on RDS before the first prod deploy. Verified working against local Docker Postgres.
- Test conftest requires a `Standing` fixture for every endpoint that depends on current-season inference. Tests that forget it will see 503s rather than the endpoint's actual behavior — the failure mode is obvious, but the first-time experience is a minor friction point.

### Impact on project plan

- **Story 5.3 (Player and team endpoints):** Scope expanded. Adds `/teams/{team_id}` (formalized) and `/teams/{team_id}/games`. Originally-completed tasks unchanged; new endpoints appended.
- **Story 5.4 (Stats endpoints):** Scope rewritten. Drops `vs-matchup`, `injuries`, and `compare`. Adds `/players/top/preview`, `/games/{game_id}` (discriminated union), `/games/{game_id}/playerstats`, `/games/h2h`, `/standings`, `/standings/preview`. Retains `/players/{id}/season-averages`, `/players/{id}/last-5-games`, `/players/{id}/vs-opponent`.
- **Story 6.4 (Player detail and stat views):** Drops the "vs Matchup" tab and "injury badge". Remaining tabs (Season Averages, Last 5 Games, vs Opponent) remain in scope.
- **Story 6.5 (Player comparison view):** Removed from scope entirely — no corresponding endpoint in ENDPOINTS.md.
- **Story 6.6 (Dashboard / Front Page):** Tasks expanded to match ENDPOINTS.md Front Page. "Today's game schedule" maps to `/games/upcoming`; "players to watch" to `/players/top/preview`; a new "standings preview" widget maps to `/standings/preview`.
- **Story 6.7 (new) — Standings Page:** Displays the full `/standings` table grouped by conference.
- **Story 6.8 (new) — Game Page:** Game detail view that branches on the discriminated union response; includes head-to-head history for upcoming games and player box scores for completed games.
- **Schema Design block:** Add `standings` entity (team_id, season, conference, conference_rank, wins/losses, win_pct, games_behind, streak, points_pg, opp_points_pg).
- **Key Technical Decisions Log:** Add a row for the ENDPOINTS.md-driven API redesign pattern.
