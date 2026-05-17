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

---

## ADR-007 — Runtime live-game path via `nba_api.live` with in-process `StaleCache`

**Date:** FEATURE-006  
**Status:** Accepted

### Context

ADR-005 established that all backend reads come from RDS via batch ingestion. Story 6.6 (Front Page) and Story 6.8 (Game Detail) surfaced two gaps that batch-only reads cannot fill:

1. Games that are currently in progress have a live score and box score that will not appear in RDS until the nightly ingestion job runs.
2. Games that completed recently but whose ingestion has not yet run will still show as status=1 ("preview") to clients.

Rendering either situation from RDS alone would mislead users — a completed game showing a "preview" card, or a live game showing stale scores.

### Decision

Introduce a runtime path to NBA's live CDN via `nba_api.live.nba.endpoints` (`ScoreBoard` and `BoxScore`) on the backend request path. The live data is served exclusively through two new read endpoints:

- `GET /games/live/today` — today's full slate of games with current scores and status
- `GET /games/live/{game_id}` — full live box score for a single in-progress game

Live data is **cache-only and never written to RDS.** An in-process `StaleCache` (`backend/app/cache/stale_cache.py`) holds entries as `(value, expires_at, last_updated_at)` tuples. TTL is variable by game state:

| State | Bulk endpoint TTL | Per-game endpoint TTL |
|---|---|---|
| Any live game | 30s | 30s |
| All final, not yet ingested | 5 min | 5 min |
| Pre-game / no games today | 30 min | — |

The shorter TTL during live states favors freshness; longer TTLs during quiescent states amortize upstream load.

On upstream failure, the response path degrades gracefully:

1. If a fresh cached value exists, it is returned with `is_stale=False` (cache hit, no upstream call needed).
2. If the cache is stale (TTL expired) and the upstream fails, the expired value is returned with `is_stale=True` and `last_updated_at` reflecting when it was cached.
3. If no cached value exists at all, the endpoint returns HTTP 503 — the frontend hides the live widget without breaking the page.

The per-game endpoint adds a DB validation pass before the upstream call: if `game.status == 3` (final) or `now < game.tipoff_at`, it returns HTTP 409, directing the client to use the standard `/games/{game_id}` endpoint instead. This short-circuit prevents live upstream calls for games that have no live data. The 409 matches the existing pattern at `GET /games/{game_id}` for missing team stats.

### Consequences

**Positive:**

- Live game data is now representable on the frontend without waiting for the nightly ingest.
- Failure modes are explicit and non-catastrophic: stale cache degrades gracefully; total upstream loss yields 503 rather than a crash.
- No new dependencies — `nba_api.live` is already installed transitively alongside `nba_api.stats` used in ingestion.
- No new persistent infrastructure — the cache is in-process, requires no Redis or external coordination.

**Negative / Watch points:**

- This is the first runtime upstream dependency on the request path. All prior upstream calls (NBA.com API) were confined to the ingestion pipeline running off the request path. Upstream latency now directly affects API response times (mitigated by the cache: cold-start is the only slow path).
- The cache is process-local. If the backend scales to multiple replicas, each process maintains its own cache and independently polls the upstream. Cache hit rate degrades linearly with replica count. Acceptable for the current single-replica deploy; revisit with Redis or sticky routing if horizontal scale is needed.
- `asyncio.to_thread` is used to call synchronous `nba_api.live` constructors without blocking the event loop. This is correct but relies on the threadpool having available threads during concurrent live-game traffic. Under extreme concurrency, threadpool exhaustion would produce latency rather than errors.
- The `tipoff_at` column on `games` (introduced in the same PR) is the authoritative pre-game cutoff. If the column is stale (synthesized defaults from the migration window), the 409 short-circuit may not fire correctly until the schedule ingest reruns. The deploy choreography in `docs/SCHEMA_AMENDMENTS.md` must be followed to completion before the live endpoint is in production use.

**Deferred work:**

- `GameDetail.tsx` integration: deferred to Story 6.8.x. The `/games/live/{game_id}` endpoint is complete; the frontend component to consume it is not yet built.
- Front page widget integration: deferred to Story 6.6. The `/games/live/today` endpoint is complete; the frontend component is not yet built.

---

## ADR-008 — NAT Gateway for live-data egress (interim), with split-Lambda migration plan

**Date:** Epic 7 deployment / post-FEATURE-006
**Status:** Accepted (NAT Gateway, interim) / Proposed (split-Lambda end state)

### Context

ADR-005 chose a hybrid local-cloud ingestion model specifically to **avoid** a NAT Gateway, on the basis that no Lambda on the request path needed internet access — ingestion ran locally, the Loader Lambda needed only S3 (via free Gateway Endpoint) and RDS, and the backend Lambda was a pure RDS reader.

ADR-007 (FEATURE-006) changed that premise. It introduced two backend endpoints — `GET /games/live/today` and `GET /games/live/{game_id}` — that call `nba_api.live` synchronously on the request path. These calls hit `https://cdn.nba.com/...` and require outbound HTTPS from the backend Lambda. The ADR was written and merged before deployment surfaced the missing connectivity, so the gap was not flagged at the time.

First-deploy testing of the live endpoints returned `503 "Live data unavailable"` after a 15-second hang on every call. Root cause: the backend Lambda was placed in `public_subnet_ids` with the assumption that public subnets ⇒ internet access. AWS Lambda Hyperplane ENIs never receive public IPs, so traffic to the IGW has no return path regardless of subnet routing — the same constraint ADR-005 originally documented. The backend therefore had RDS access (in-VPC) but no internet.

A frontend-only workaround was explored: have the browser fetch directly from `cdn.nba.com`. The CDN does not return permissive CORS headers for our origin, so the browser blocks the request. Confirmed empirically.

This leaves three viable architectures:

| Option | Cost | Complexity | Notes |
|---|---|---|---|
| **A. NAT Gateway** | ~$32/mo + data | Trivial Terraform diff | Backend stays a single Lambda, moves to private subnets. Standard AWS pattern. |
| **B. Split live endpoints into a non-VPC Lambda** | $0 | New deployment unit, API Gateway routing changes | Live endpoints get free egress; main backend keeps VPC for RDS; NAT not needed. |
| **C. Make RDS publicly accessible, drop VPC from backend** | $0 | Trivial | Real security regression — RDS exposed to the public internet even if SG-locked. Not viable. |

### Decision

A two-phase architecture: deploy NAT Gateway now (Phase 1), migrate to split-Lambda when ready (Phase 2).

#### Phase 1 — NAT Gateway (Accepted, this PR)

Provision a single NAT Gateway in `public_1` with an Elastic IP, add a `0.0.0.0/0 → NAT` route to the private route table, and move the backend Lambda from `public_subnet_ids` to `private_subnet_ids`. Loader and RDS configuration are unaffected (already in private subnets).

Single-AZ NAT was chosen over HA (one NAT per AZ) because the cost ratio (~$32/mo single vs ~$66/mo HA) does not justify HA for a dev environment with no SLA. Cross-AZ NAT traffic from `private_2` is a minor latency and data-transfer cost, acceptable here.

#### Phase 2 — Split-Lambda end state (Proposed, future work)

The live endpoints have **no DB dependency** for the bulk endpoint (`/games/live/today` is a pure passthrough), and the per-game endpoint's DB lookup is small enough to be replaced by a cross-Lambda HTTP hop or by replicating the lookup in the live Lambda's own minimal SQLAlchemy session. Either way, the live endpoints can run in an unattached (non-VPC) Lambda with native internet access, eliminating NAT cost entirely.

End state:

```
                      ┌─────────────────────────────────┐
                      │ API Gateway (HTTP)              │
                      └────────────┬────────────────────┘
                                   │ /games/live/* ───┐
                                   │ everything else  │
                                   ▼                  ▼
                       ┌──────────────────┐  ┌──────────────────┐
                       │ lambda_backend   │  │ lambda_backend_  │
                       │ (VPC, RDS)       │  │ live (no VPC,    │
                       │ no nba_api dep   │  │  internet OK)    │
                       └────────┬─────────┘  └────────┬─────────┘
                                │                     │
                                ▼                     ▼
                              RDS                  cdn.nba.com
```

The NAT Gateway, EIP, and private-route `0.0.0.0/0` entry are decommissioned. Backend Lambda stays in private subnets — RDS is in-VPC, no internet needed for the main path.

### Migration plan (Phase 2)

The plan below is the prescription to execute when migrating off NAT. It is intentionally detailed so a future executor (human or agent) can implement without re-deriving decisions.

**1. New package: `backend_live/`**
   - Mirrors `backend/app/` structure, but contains only:
     - `app/main.py` — FastAPI app with `app.include_router(games_live.router)` and Mangum handler
     - `app/routers/games_live.py` — the two live endpoints, lifted from `backend/app/routers/games.py` lines 148-302
     - `app/cache/stale_cache.py` — copied (or shared via `/shared` if promoted; see note below)
     - `app/schemas/game.py` — only the Pydantic shapes the live endpoints use (`LiveScoreboardResponse`, `LiveScoreboardEntry`, `GameLive`, `PlayerLiveStat`)
   - Dependencies: `fastapi`, `mangum`, `nba-api`, `pydantic`, `structlog`. **No** SQLAlchemy, asyncpg, or RDS env vars.
   - For the per-game endpoint's DB lookup: easiest is to keep that endpoint on the main backend and have the frontend make two calls (one for game metadata via main backend, one for live data via live Lambda). Cleanest separation, lowest coupling. Alternative: live Lambda makes an HTTP call to the main backend's `/games/{game_id}` to validate state — adds a hop but keeps the contract single-Lambda.

**2. New script: `scripts/package_backend_live.sh`**
   - Pattern: copy of `scripts/package_backend.sh` with `DIST_DIR=backend_live/dist`, `ZIP_PATH=infra/backend_live.zip`, pip install list trimmed to (fastapi, mangum, nba-api, pydantic, structlog).
   - **Significantly smaller zip** — no pandas/numpy via nba_api's transitive deps? Actually `nba_api.live` does NOT depend on pandas; pandas comes in via `nba_api.stats.*` modules. Confirm by `import nba_api.live.nba.endpoints` in isolation and inspecting the import tree. If clean, the live zip stays well under the 50MB direct-upload limit and does not need S3-backed deploy.

**3. New script: `scripts/deploy_backend_live.sh`**
   - If zip < 50MB: use direct `aws lambda update-function-code --zip-file fileb://...`.
   - Otherwise: reuse the S3 artifacts bucket pattern from ADR-008-Phase-1 (`scripts/deploy_backend.sh`).

**4. Terraform changes**
   - Add `module "lambda_backend_live"` using the existing `infra/modules/lambda/` module. **No** `subnet_ids` / `security_group_ids` (omit entirely to skip `vpc_config`). The module currently requires those — extend the module to make them optional (default `null`), or use a thin wrapper.
   - Update `infra/modules/api_gateway/` to support routing rules. The current module hardcodes `ANY /{proxy+}` to a single Lambda. Either:
     - (a) Add a second route `ANY /games/live/{proxy+}` with higher priority pointing at `lambda_backend_live`, OR
     - (b) Use API Gateway HTTP API's built-in route precedence (longer paths win).
   - Remove `aws_eip.nat`, `aws_nat_gateway.main`, `aws_route.private_internet` from `infra/modules/vpc/main.tf`.
   - Remove `nba-api` from `scripts/package_backend.sh` pip-install list. Drop the import in `backend/app/routers/games.py` (the live endpoints are gone from this file by now).

**5. Backend code cleanup**
   - Delete the live endpoint handlers from `backend/app/routers/games.py`.
   - Delete `backend/app/cache/stale_cache.py` if not referenced elsewhere (or promote to `/shared` if reused).
   - Drop `nba-api` from `backend/pyproject.toml` runtime deps.

**6. Frontend integration**
   - If the live Lambda lives on the same API Gateway, no frontend change — same base URL.
   - If on a separate domain (e.g., own API Gateway), add a second axios client in `frontend/src/lib/` and switch the live React Query hooks to use it.

**7. Decommission order**
   - Deploy live Lambda + API Gateway routing first; confirm `/games/live/today` returns data from the new Lambda (check CloudWatch log group).
   - Only then redeploy the slimmed main backend (without nba_api).
   - Only then `terraform apply` the VPC module changes that remove the NAT Gateway.

### Consequences

**Positive (Phase 1):**

- Unblocks live-data endpoints immediately with a 5-line VPC diff. No code changes.
- NAT also benefits Loader Lambda (now has internet too) — useful if Loader ever needs to call an external service for enrichment.
- Fully reversible — remove the NAT resources and revert the subnet-ids change.

**Positive (Phase 2):**

- Eliminates ~$32/mo recurring NAT cost.
- Cleanly separates concerns: DB-bound logic in VPC, internet-bound logic outside.
- Shrinks the main backend Lambda zip meaningfully (no nba_api → no transitively-pulled deps). May allow reverting from S3-backed deploy back to direct upload.
- Failure isolation: live API outages (Akamai rate limits, NBA CDN hiccups) cannot impact the DB-serving backend's cold-start time or memory budget.

**Negative / Watch points (Phase 1):**

- NAT Gateway is the single largest line item on the dev AWS bill (~$32/mo + ~$0.045/GB processed). For a dev env with low traffic, total ~$35–40/mo. Plan to migrate to Phase 2 before this compounds.
- Single-AZ NAT is a single point of failure. If `us-east-1a` has an AZ-level outage, all backend Lambda outbound traffic fails. Acceptable for dev; would not be for prod.
- Cross-AZ data transfer from `private_2` Lambdas to the NAT in `private_1`'s AZ incurs ~$0.01/GB. Negligible at dev scale.

**Negative / Watch points (Phase 2):**

- Two Lambda functions to deploy, monitor, and version. More CI complexity.
- The per-game live endpoint's DB lookup splits across two services — either the frontend orchestrates two calls or one Lambda calls the other over HTTP. Either way, more moving parts than the single-Lambda model.
- API Gateway routing precedence must be configured carefully. A misrouted `/games/live/foo` going to the main backend would 404 silently (handler doesn't exist there post-migration); a misrouted `/games/foo` going to the live Lambda would 404 the same way.
- `StaleCache` is process-local. Splitting concerns means the cache can no longer be shared across endpoints — acceptable since the only consumers were the live endpoints themselves.

**Reversibility:**

Phase 1 is fully reversible — delete NAT resources, switch backend back to public subnets (or keep in private if that's fine; backend doesn't need internet without the live endpoints).

Phase 2 is reversible by re-merging the live router into the main backend and re-adding NAT. The cost of reversal is mostly code-move work; Terraform state changes are straightforward.

### Impact on project plan / docs

- **Update ADR-005 cross-reference:** ADR-005's "no NAT" stance was correct under its scope (ingestion). The runtime live-data path introduced by ADR-007 falls outside that scope and motivates Phase 1 here. No edit to ADR-005 — its decision remains valid for its stated context.
- **Update ADR-007 watch points:** add a note that runtime upstream dependency on the request path now also requires outbound network configuration, addressed by ADR-008.
- **Story 7.x (CI/CD):** when Phase 2 lands, the backend CI workflow (Story 7.3) needs a sibling workflow for `backend_live`. Defer until Phase 2 is scheduled.
- **PENDING_FEATURES.md:** add an entry pointing to ADR-008 Phase 2 as a planned cost-optimization migration (out of scope this iteration).
