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
