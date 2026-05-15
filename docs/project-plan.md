# NBAJinni — Project Plan

## Project Overview

A full-stack web application for viewing NBA player and team statistics, designed to assist in predicting player performance in upcoming games. Built as an end-to-end portfolio project with a production-grade deployment pipeline on AWS.

---

## Confirmed Stack

| Layer          | Technology                                                                               | Rationale                                                                                        |
| -------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Frontend       | React + TypeScript (Vite)                                                                | Industry-standard, portfolio-visible, type safety                                                |
| Backend API    | Python + FastAPI                                                                         | Shared language with ingestion, modern, auto-docs                                                |
| Database       | PostgreSQL (AWS RDS)                                                                     | Relational data fits the domain, industry gold standard                                          |
| Ingestion      | ~~Python Lambda + EventBridge~~ Local Python + cron, S3 sync via Loader Lambda [ADR-005] | ~~Serverless, free tier friendly, nightly schedule~~ Cost-optimized hybrid local-cloud [ADR-005] |
| Hosting (FE)   | S3 + CloudFront                                                                          | Static hosting, effectively free                                                                 |
| Hosting (API)  | Lambda + API Gateway                                                                     | Serverless, free tier friendly                                                                   |
| IaC            | Terraform                                                                                | Cloud-agnostic, widely recognized                                                                |
| CI/CD          | GitHub Actions                                                                           | Native to repo, employer visible, AWS OIDC integration                                           |
| Auth           | JWT (email/password)                                                                     | Simple, standard, no third-party dependency                                                      |
| Migrations     | Alembic                                                                                  | Python-native, pairs with SQLAlchemy                                                             |
| Repo Structure | Monorepo                                                                                 | Solo project, single pipeline, clean folder separation                                           |

---

## Repository Structure

```
/
├── frontend/          # React + TypeScript app
├── backend/           # FastAPI application
├── ingestion/         # Local ingestion pipeline (runs on dev machine) [ADR-005]
├── loader/            # S3-to-RDS sync Lambda [ADR-005]
├── shared/            # [ADR-001] Shared database models, utilities, and session initializer
├── scripts/           # Export and upload scripts for S3 sync [ADR-005]
├── infra/             # Terraform configurations
│   ├── modules/
│   └── environments/
│       ├── dev/
│       └── prod/
├── .github/
│   └── workflows/     # CI/CD pipelines
└── README.md
```

---

## Data Architecture Notes

### ~~API Constraint Strategy~~

> ~~The free tier of api-sports.io allows **100 calls per 24 hours**. The ingestion pipeline must be designed to maximize data extracted per call:~~
>
> - ~~Fetch game logs by date range rather than game-by-game~~
> - ~~Prioritize endpoints that return bulk player stats in a single response~~
> - ~~Cache reference data (teams, rosters) and only re-fetch on a weekly basis, not nightly~~
> - ~~Nightly job should focus only on games played in the last 24 hours~~

### [ADR-002] Data Source Strategy

The `nba_api` Python package is used for all data ingestion. It interfaces directly with NBA.com APIs, is completely free, and provides current season data. There is no hard API call budget, but NBA.com may throttle aggressive requests — the ingestion layer must include polite delays between calls. Roster and reference data should still be fetched weekly rather than nightly to reduce unnecessary load.

### Schema Design (Core Entities)

```
teams           — id, name, abbreviation, conference, division
players         — id, name, team_id, position, jersey_number, active
seasons         — id, year, label
games           — id, date, home_team_id, away_team_id, season_id, status
player_game_stats — id, player_id, game_id, points, rebounds, assists, steals,
                    blocks, turnovers, fg_pct, three_pct, ft_pct, minutes
player_season_averages — player_id, season_id, (same stat cols as above)
standings       — team_id, season, conference, conference_rank, wins, losses,
                  win_pct, games_behind, streak, points_pg, opp_points_pg [ADR-006]
injuries        — id, player_id, status, description, updated_at
users           — id, email, hashed_password, created_at
```

This schema directly supports every required stat view and is extensible to other sports by scoping queries to a sport/league dimension in future iterations.

---

## Epics & User Stories

---

### EPIC 1 — Project Foundation & Repository Setup

**Goal:** Get a clean, well-structured monorepo in place with all tooling configured before writing any application code.

---

**Story 1.1 — Initialize monorepo**
_As a developer, I want a clean repository structure so that all parts of the project are logically organized and easy to navigate._

Tasks:

- [x] Create GitHub repository (public, for portfolio visibility)
- [x] Initialize monorepo folder structure: `/frontend`, `/backend`, `/ingestion`, `/infra`, `/.github/workflows`
- [x] Add root-level `README.md` with project description, stack overview, architecture diagram placeholder, and local dev setup instructions
- [x] Add `.gitignore` covering Python, Node, Terraform, and environment files
- [x] Configure branch protection on `main` (require PR, no direct push)
- [x] Create a `dev` branch as the primary working branch

---

**Story 1.2 — Configure local development environment**
_As a developer, I want consistent local dev tooling so that linting and formatting are enforced from day one._

Tasks:

- [x] Add `pyproject.toml` for backend and ingestion with `black`, `flake8`, and `isort` config
- [x] Add `.pre-commit-config.yaml` for pre-commit hooks (format + lint on commit)
- [x] Add `package.json` ESLint + Prettier config for frontend
- [x] Add a root-level `Makefile` with common commands (`make dev`, `make test`, `make lint`)
- [x] Document local setup steps in README

---

### EPIC 2 — Infrastructure (Terraform)

**Goal:** Provision all AWS resources via code so the environment is reproducible, auditable, and demonstrates IaC competency.

---

**Story 2.1 — Terraform project structure and remote state**
_As a developer, I want Terraform state stored remotely so that infrastructure changes are tracked and safe._

Tasks:

- [x] Initialize Terraform project under `/infra` with `modules/` and `environments/dev/` structure
- [x] Manually create an S3 bucket and DynamoDB table for Terraform remote state (one-time bootstrap)
- [x] Configure `backend.tf` in `environments/dev/` to use the remote state bucket
- [x] Define `variables.tf` and `outputs.tf` conventions for all modules
- [x] Add `terraform fmt` and `terraform validate` to CI pipeline (later epic)

---

**Story 2.2 — Provision database infrastructure**
_As a developer, I want an RDS PostgreSQL instance provisioned via Terraform so the database is reproducible and secured._

Tasks:

- [x] Write Terraform `rds` module: `db.t3.micro`, PostgreSQL 15, free tier settings
- [x] Place RDS in a private subnet (no public access)
- [x] Create a VPC, public/private subnets, and security groups to allow Lambda → RDS access
- [x] Store DB credentials in AWS Secrets Manager via Terraform
- [x] Output RDS endpoint for use in other modules

---

**Story 2.3 — Provision compute and API infrastructure**
_As a developer, I want Lambda functions and API Gateway provisioned via Terraform so the backend is deployable without manual console work._

Tasks:

- [x] Write Terraform `lambda` module for the backend API function (Python 3.12 runtime)
- ~~[x] Write Terraform `lambda` module for the ingestion function (separate function)~~ _(superseded by [ADR-005] — ingestion runs locally)_
- [x] Write Terraform for API Gateway (HTTP API) wired to the backend Lambda
- ~~[x] Write Terraform for EventBridge rule (nightly cron) triggering the ingestion Lambda~~ _(superseded by [ADR-005] — local cron replaces EventBridge)_
- [x] Configure IAM roles: Lambda execution role with RDS access and Secrets Manager read
- [x] Configure Lambda VPC settings so it can reach RDS in the private subnet
- ~~[ ] Provision a Secrets Manager entry for the api-sports.io API key~~ _(superseded by [ADR-002] — no third-party API key required)_
- [ ] Write Terraform for Loader Lambda (VPC-attached, S3-triggered or manually invoked) [ADR-005]
- [ ] Write Terraform for S3 bucket for data exports [ADR-005]
- [ ] Write Terraform for S3 VPC Gateway Endpoint [ADR-005]

---

**Story 2.4 — Provision frontend hosting infrastructure**
_As a developer, I want the frontend hosted on S3 + CloudFront so it is publicly accessible and delivered via CDN._

Tasks:

- [x] Write Terraform for S3 bucket (static website hosting, public read policy)
- [x] Write Terraform for CloudFront distribution pointing to the S3 bucket
- [x] Configure CloudFront to handle SPA routing (redirect 404s to `index.html`)
- [x] Output CloudFront domain URL

---

### EPIC 3 — Database Schema & Migrations

**Goal:** Design and implement the database schema with a proper migration workflow, building familiarity with relational design.

---

**Story 3.1 — Set up Alembic migration framework**
_As a developer, I want a migration framework in place so that database schema changes are versioned and repeatable._

Tasks:

- [x] Install and initialize Alembic in the `/backend` project
- [x] Configure Alembic to connect to the RDS instance via environment variable
- [x] Document how to run migrations (`alembic upgrade head`) in the README
- [x] Set up `alembic upgrade head` as a step in the deployment pipeline (later epic)

---

**Story 3.2 — Implement core schema migrations**
_As a developer, I want the full database schema created via migrations so that the data layer is ready for the ingestion pipeline._

Tasks:

- [x] Write migration: `teams` table
- [x] Write migration: `seasons` table
- [x] Write migration: `players` table (FK to teams)
- [x] Write migration: `games` table (FK to teams and seasons)
- [x] Write migration: `player_game_stats` table (FK to players and games)
- [x] Write migration: `player_season_averages` table (FK to players and seasons)
- [x] Write migration: `injuries` table (FK to players)
- [x] Write migration: `users` table
- [x] Add appropriate indexes: `player_id`, `game_id`, `team_id`, `date` columns

---

**Story 3.3 — Seed reference data**
_As a developer, I want static reference data (teams, current season) pre-loaded so the ingestion pipeline has the context it needs._

Tasks:

- [x] Write a one-time seed script for all 30 NBA teams
- [x] Write a one-time seed script for the current season record
- [x] Document how to run seed scripts in the README

---

### EPIC 4 — Data Ingestion Pipeline

**Goal:** ~~Build a nightly Lambda function that pulls data from api-sports.io and populates the database efficiently within the 100 calls/day limit.~~ [ADR-002] Build a nightly Lambda function that pulls current season data from NBA.com via the `nba_api` package and populates the database.

---

**Story 4.1 — ~~API client and rate limit management~~ [ADR-002] `nba_api` client and request throttling**

~~_As a developer, I want a well-designed API client so that all calls to api-sports.io are tracked, logged, and never wasted._~~

[ADR-002] _As a developer, I want a well-designed `nba_api` wrapper so that all requests are throttled, logged, and resilient to transient failures._

Tasks:

- ~~[ ] Read and document the api-sports.io NBA endpoint reference — identify the minimum set of endpoints needed for all stat views~~
- ~~[ ] Implement a Python API client class wrapping `httpx` with: API key injection from Secrets Manager, response logging, error handling, and retry logic~~
- ~~[ ] Implement a call counter utility that logs each API call to a DynamoDB table (or CloudWatch metric) so daily usage is trackable~~
- [x] Identify and document the `nba_api` endpoints needed for all stat views (game logs, player stats, rosters, injuries) [ADR-002]
- [x] Implement a lightweight `nba_api` wrapper with: request throttling (polite delays between calls), structured logging, error handling, and retry logic [ADR-002]
- [x] Write unit tests for the API client (mocked responses)

---

**Story 4.2 — Roster and reference data ingestion**
_As a developer, I want team rosters kept up to date so the database always reflects the current league._

Tasks:

- [x] Implement ingestion function: fetch all players for each team and upsert into `players` table
- [x] Schedule this function to run **bi-weekly** (not nightly) ~~to conserve API calls~~ [ADR-002] to avoid unnecessary load on NBA.com
- [x] Implement idempotent upsert logic (insert if not exists, update if changed)

---

**Story 4.3 — Game and player stats ingestion**
_As a developer, I want last night's game stats automatically ingested so the database stays current without manual intervention._

Tasks:

- [x] Implement nightly ingestion function: fetch all games played in the last 24 hours
- [x] For each completed game, fetch player stats and upsert into `player_game_stats`
- [x] Derive and upsert updated `player_season_averages` from the raw game stats (compute locally)
- [x] Write integration tests against a local Postgres instance using Docker

---

**Story 4.4 — ~~Lambda packaging and deployment~~ Loader Lambda and S3 sync infrastructure [ADR-005]**
~~_As a developer, I want the ingestion Lambda packaged and deployable via CI so it runs reliably in AWS._~~

_As a developer, I want a Loader Lambda that syncs data from S3 to RDS, with supporting export scripts for local-to-cloud data transfer._ [ADR-005]

~~Tasks (superseded by [ADR-005]):~~

- ~~[ ] Configure Lambda handler entry point~~
- ~~[ ] Set up dependency packaging (Lambda layer or bundled zip)~~
- ~~[ ] Ensure `/shared` is bundled as part of the ingestion Lambda deployment zip [ADR-001]~~
- ~~[ ] Verify Lambda can connect to RDS inside the VPC~~
- ~~[ ] Add CloudWatch log group and structured logging~~
- ~~[ ] Manually trigger and verify a successful run end-to-end before automating~~

Tasks [ADR-005]:

- [x] Create JSON export script (`scripts/export_to_json.py`)
- [x] Create S3 upload script (`scripts/upload_to_s3.py`)
- [x] Create Loader Lambda handler (`loader/main.py`)
- [x] Package Loader Lambda with `/shared` dependency [ADR-001]
- [x] Update `shared/session.py` to support Lambda environment (assemble `DATABASE_URL` from env vars)
- [x] Verify Loader Lambda connects to RDS and loads data correctly
- [x] Add CloudWatch log group and structured logging for Loader Lambda
- [x] Document local cron setup for ingestion + export
- [x] Document manual sync workflow (export → upload → verify)

---

### EPIC 5 — Backend API (FastAPI)

**Goal:** Build a well-structured REST API that serves all stat views to the frontend, with authentication and auto-generated documentation.

---

**Story 5.1 — Project structure and database connectivity**
_As a developer, I want a clean FastAPI project wired up to PostgreSQL so I have a solid foundation for building endpoints._

_Prerequisite: `shared/session.py` Lambda environment support (Story 4.4) [ADR-005]_

Tasks:

- [x] Initialize FastAPI project under `/backend`
- [x] Install `/shared` as a local dependency in the `/backend` package and import models and session initializer from it [ADR-001]
- [x] Configure SQLAlchemy async engine with connection pooling
- [x] Set up dependency injection pattern for DB sessions
- [x] Configure Mangum handler to run FastAPI inside AWS Lambda
- [x] Add health check endpoint (`GET /health`)
- [x] Add CORS middleware configured for the CloudFront frontend domain

---

~~**Story 5.2 — Authentication**~~
~~_As a user, I want to register and log in with email and password so my session is secure._~~

Tasks:

- [ ] ~~Implement `POST /auth/register` — hash password with bcrypt, insert user, return JWT~~
- [ ] ~~Implement `POST /auth/login` — verify password, return JWT~~
- [ ] ~~Implement JWT middleware for protected routes~~
- [ ] ~~Write unit tests for auth endpoints~~

**\*_user authentication shelved in ADR-003, will be considered as an added feature later on_**

**Story 5.3 — Player and team endpoints**
_As a user, I want to search for players and browse teams so I can navigate to the stats I need._

Tasks:

- [x] Implement `GET /teams` — return all teams
- [x] Implement `GET /teams/{team_id}/roster` — return players on a team
- [x] Implement `GET /players/search?q=` — search players by name
- [x] Implement `GET /players/{player_id}` — return player profile (trimmed to `base + team` only) [ADR-006]
- [x] Implement `GET /teams/{team_id}` — return team detail [ADR-006]
- [x] Implement `GET /teams/{team_id}/games` — games for a team with nested `team_game_stats` (null for unplayed games); current season [ADR-006]

---

**Story 5.4 — Stats endpoints**
_As a user, I want to view a variety of stat views for any player so I can assess their likely performance._

Tasks:

- [x] Implement `GET /players/{player_id}/season-averages` — current season averages [ADR-006]
- [x] Implement `GET /players/{player_id}/last-5-games` — last 5 game logs (response includes `game_date` + `opponent_team_id`) [ADR-006]
- [x] Implement `GET /players/{player_id}/vs-opponent?team_id=` — stats vs a specific team, current season only [ADR-006]
- ~~[ ] Implement `GET /players/{player_id}/vs-matchup?position=` — historical stats vs a positional matchup~~ _(removed from scope [ADR-006])_
- ~~[ ] Implement `GET /players/{player_id}/injuries` — current injury status~~ _(removed from scope — no ingestion pipeline for injuries [ADR-006])_
- ~~[ ] Implement `GET /players/compare?ids=` — side-by-side stat comparison for 2+ players~~ _(removed from scope alongside Story 6.5 [ADR-006])_
- [x] Implement `GET /players/top/preview` — top 3 players per stat category (points, rebounds, assists, steals, blocks) with early-season floor handling [ADR-006]
- [x] Implement `GET /games/{game_id}` — discriminated union (`GamePreview` for upcoming / `GameResult` for completed) [ADR-006]
- [x] Implement `GET /games/{game_id}/playerstats` — player box scores for both teams [ADR-006]
- [x] Implement `GET /games/h2h?team_a=&team_b=` — head-to-head games; symmetric query params; current season [ADR-006]
- [x] Implement `GET /standings` — all 30 teams, current season [ADR-006]
- [x] Implement `GET /standings/preview` — top 10 by `win_pct` crossing both conferences [ADR-006]
- [x] Write unit tests for all stat endpoints (happy path + 404 / empty cases against real AsyncSession) [ADR-006]

---

### EPIC 6 — Frontend (React + TypeScript)

**Goal:** Build a clean, functional multi-view UI that lets users navigate the app, view all stat types, and compare players.

---

**Story 6.1 — Project setup and routing**
_As a developer, I want the frontend scaffolded with routing and a global state foundation before building any views._

Tasks:

- [x] Initialize Vite + React + TypeScript project under `/frontend`
- [x] Install and configure React Router (v6) for multi-view navigation
- [x] Install and configure React Query for server state management
- [x] Install a UI component library (Tailwind CSS recommended for portfolio visibility)
- [x] Set up an Axios API client with JWT injection from local storage
- [x] Configure environment variables for API base URL (dev vs prod)

---

~~**Story 6.2 — Authentication views**~~
~~_As a user, I want to register and log in so I can access the app._~~

Tasks:

- [ ] ~~Build `/login` page — form, API call, store JWT, redirect on success~~
- [ ] ~~Build `/register` page — form, API call, redirect to login on success~~
- [ ] ~~Implement auth context (global user/token state)~~
- [ ] ~~Implement protected route wrapper — redirect to login if unauthenticated~~
- [ ] ~~Implement logout~~

**\*_user authentication shelved in ADR-003, will be considered as an added feature later on_**

**Story 6.3 — Team browser and player navigation**
_As a user, I want to browse teams and drill into their rosters so I can find the player I'm looking for._

Tasks:

- [x] Build `/teams` page — grid of all 30 teams with logos/names
- [x] Build `/teams/{id}` page — team detail with roster list
- [x] Build global player search bar in the nav — autocomplete calling `/players/search`
- [x] Wire all player cards/names to navigate to the player detail page

---

**Story 6.4 — Player detail and stat views**
_As a user, I want a rich player detail page where I can toggle between different stat views._

Tasks:

- [x] Build `/players/{id}` page — player header (name, team, position~~, injury badge~~ [ADR-006])
- [x] Build tabbed stat view component with tabs for: Season Averages, Last 5 Games, vs Opponent ~~, vs Matchup~~ [ADR-006]
- [x] Build season averages stat card
- [x] Build last 5 games log table
- [x] Build vs-opponent stat view (with team selector dropdown)
- ~~[ ] Build vs-matchup stat view (with position selector)~~ _(removed from scope [ADR-006])_
- [x] Add loading skeletons and error states to all data views

---

~~**Story 6.5 — Player comparison view**~~ _(removed from scope [ADR-006])_
~~_As a user, I want to compare two or more players side-by-side so I can evaluate relative performance._~~

Tasks:

- ~~[ ] Build `/compare` page — player selector (add up to 4 players)~~
- ~~[ ] Build side-by-side stat comparison table~~
- ~~[ ] Highlight best value per stat row~~

---

**Story 6.6 — Front Page** ~~Dashboard~~ [ADR-006, ADR-007]
_As a user, I want a home landing page surfacing today's games (upcoming, live, and recently completed), top players, top recent performances, and standings at a glance._ [ADR-006]

Tasks:

- [x] Build `/` front page — games widget backed by `GET /games/live/today` [ADR-007]; render a combined slate of upcoming (pre-tip), in-progress (with live score/clock), and recently completed (final score, not-yet-ingested) games using the three-state routing rule (`status`, `tipoff_at`, `now`) defined in FEATURE-006
- [x] Build "top players" widget backed by `GET /players/top/preview` (5 stat categories, top 3 each) [ADR-006]
- [x] Build "recent top performances" widget — 3 slots surfacing standout individual game performances from recently completed games
- [x] Build "standings preview" widget backed by `GET /standings/preview` (top 10 cross-conference) [ADR-006]

---

**Story 6.7 — Standings Page** [ADR-006]
_As a user, I want to view the full league standings grouped by conference._

Tasks:

- [x] Build `/standings` page — full standings table backed by `GET /standings` [ADR-006]
- [x] Group rows by `conference`; order within each group by `conference_rank` [ADR-006]
- [x] Display wins, losses, win_pct, games_behind, streak, points_pg, opp_points_pg columns [ADR-006]

---

**Story 6.8 — Game Page** [ADR-006]
_As a user, I want a game detail page that adapts to whether the game has been played._

Tasks:

- [x] Build `/games/{id}` page — consume `GET /games/{game_id}` discriminated union and branch on `kind` [ADR-006]
- [x] Preview branch: render both teams' standings + season averages (data embedded in `GamePreview`); fetch `GET /games/h2h?team_a=&team_b=` for head-to-head history [ADR-006]
- [x] Result branch: render both teams' box-score totals from `GameResult`; fetch `GET /games/{game_id}/playerstats` for per-player box scores, fetch `GET /games/h2h?team_a=&team_b=` for head-to-head history [ADR-006]
- [x] Handle 409 ("Game not yet played") gracefully when a past-status game has no team_stats [ADR-006]

---

### EPIC 7 — CI/CD Pipeline (GitHub Actions)

**Goal:** Automate testing, building, and deploying every layer of the stack so that a push to `main` results in a live `dev` environment, with `prod` promotion gated behind manual approval. Deployment model reflects [ADR-005] (local-cron ingestion + Loader Lambda owns RDS schema), [ADR-007] (live game cache adds `nba_api.live` runtime dep), and [FEATURE-007] (schema amendment choreography).

**Environments:** `dev` auto-deploys on merge to `main`; `prod` deploys via `workflow_dispatch` with GitHub Environment approval.

---

**Story 7.1 — AWS authentication via OIDC**
_As a developer, I want GitHub Actions to authenticate with AWS without storing long-lived credentials so the pipeline is secure._

Tasks:

- [ ] Create an OIDC identity provider in AWS IAM for GitHub Actions
- [ ] Create separate IAM roles for `dev` and `prod`, with trust policies scoped to this repository and (for prod) the `main` ref
- [ ] Role permissions: `lambda:UpdateFunctionCode`, `lambda:UpdateFunctionConfiguration`, `lambda:InvokeFunction`, S3 sync (frontend + loader-input buckets), CloudFront invalidation, `secretsmanager:GetSecretValue`, `secretsmanager:DescribeSecret`, `rds:DescribeDBInstances`, `logs:*`
- [ ] Add `AWS_ROLE_ARN_DEV` and `AWS_ROLE_ARN_PROD` as GitHub Actions secrets
- [ ] Verify OIDC auth works against each env with a no-op test workflow

---

**Story 7.2 — Terraform CI workflow**
_As a developer, I want Terraform plan run on every PR and apply run on merge to main so infrastructure changes are reviewed before applying, with prod gated manually._

Tasks:

- [ ] Create `.github/workflows/terraform.yml`
- [ ] On PR: run `terraform fmt -check`, `terraform validate`, `terraform plan` against `environments/dev` — post plan output as PR comment
- [ ] On merge to `main`: run `terraform apply -auto-approve` against `environments/dev`
- [ ] Add a `workflow_dispatch` job for `environments/prod` apply, requiring GitHub Environment approval
- [ ] Store Terraform state bucket, region, and lock table name as GitHub Actions secrets

---

**Story 7.3 — Backend API Lambda CI/CD workflow**
_As a developer, I want the backend Lambda automatically tested and deployed to dev on every merge to main, with prod promotion gated manually._

Tasks:

- [ ] Create `.github/workflows/backend.yml`
- [ ] On PR: run `flake8`, `black --check`, and `pytest backend/`
- [ ] Verify the backend Lambda zip bundles `/shared` [ADR-001] and the `nba_api` runtime dependency [ADR-007]
- [ ] On merge to `main`: package backend Lambda zip, deploy to dev Lambda via `aws lambda update-function-code`, then run smoke test (`curl $DEV_API/health`, fail if non-200)
- [ ] Add a `workflow_dispatch` job that promotes the same zip to the prod Lambda alias (manual gate)
- [ ] Store dev and prod backend Lambda function names as GitHub Actions secrets
- [ ] Note: schema migrations are owned by the Loader Lambda (Story 7.4); backend CI must NOT run `alembic upgrade head` [ADR-005]

---

**Story 7.4 — Loader Lambda CI/CD workflow**
_As a developer, I want the Loader Lambda automatically deployed and its `migrate` action invoked as the schema-deploy step, gated per environment._

Tasks:

- [ ] Create `.github/workflows/loader.yml`
- [ ] On PR: lint + unit-test `loader/`, run the schema-amendment lint (Story 7.5)
- [ ] On merge to `main`, against dev:
  - [ ] Build Loader zip via `scripts/package_loader.sh` (bundles `/shared`, Alembic, migrations) [ADR-005]
  - [ ] Deploy via `aws lambda update-function-code` to the dev Loader Lambda
  - [ ] Pre-flight: `aws rds describe-db-instances` to confirm reachability
  - [ ] Invoke Loader with `{"action":"migrate"}`; fail the workflow if the Lambda returns non-200 or surfaces a migration error
- [ ] Add a `workflow_dispatch` job that repeats the above sequence for prod (manual gate)
- [ ] Store dev and prod Loader Lambda function names as GitHub Actions secrets

---

**Story 7.5 — Schema amendment lint**
_As a developer, I want CI to fail fast when a migration omits any [FEATURE-007] touch-point so deploy choreography stays safe._

Tasks:

- [ ] Add `scripts/lint_schema_amendments.py`
- [ ] On PR diffs touching `alembic/versions/`, fail if a new `NOT NULL` column lacks a `server_default` in the upgrade op
- [ ] Fail if a new column on a model isn't reflected in the relevant parser map in `shared/utils.py`
- [ ] Fail if a new date/datetime column isn't added to `loader/main.py` `DATE_COLUMNS`
- [ ] Fail if upsert `set_={}` clauses aren't updated for new columns
- [ ] Wire the lint into the PR jobs for `loader.yml` and `backend.yml`

---

**Story 7.6 — Frontend CI/CD workflow**
_As a developer, I want the frontend automatically built and deployed to S3/CloudFront for dev on every merge to main, with prod promotion gated manually._

Tasks:

- [ ] Create `.github/workflows/frontend.yml`
- [ ] On PR: run `eslint`, `tsc --noEmit`, and `npm run build`
- [ ] On merge to `main`: build with `VITE_API_BASE_URL=$DEV_API_URL`, sync dist output to the dev S3 bucket, create a CloudFront invalidation (`/*`), poll until status is `Completed`, then smoke-test (`curl $DEV_FRONTEND_URL/` for 200)
- [ ] Add a `workflow_dispatch` job that repeats the build/sync/invalidate against prod with the prod API URL (manual gate)
- [ ] Store dev and prod S3 bucket names, CloudFront distribution IDs, and API base URLs as GitHub Actions secrets

---

**Story 7.7 — Integration E2E test in CI**
_As a developer, I want CI to exercise the full loader → backend path on dev before any prod promotion can run._

Tasks:

- [ ] Add a post-deploy job in `loader.yml` (dev only) that:
  - [ ] Uploads a known fixture JSON to the dev S3 loader-input bucket
  - [ ] Invokes the Loader Lambda with `{"action":"load"}`
  - [ ] Calls backend endpoints (`/teams`, `/games/{id}`) and asserts expected fixture data
  - [ ] Tears down the test fixture
- [ ] Block the prod promotion `workflow_dispatch` jobs (Stories 7.3, 7.4, 7.6) unless this E2E job has passed on the same commit

---

**Story 7.8 — Observability provisioning**
_As a developer, I want CloudWatch log groups, alarms, and a dashboard provisioned by Terraform so production issues are visible._

Tasks (deployed via Story 7.2's Terraform workflow):

- [ ] CloudWatch log groups for backend Lambda and Loader Lambda, with retention policies
- [ ] CloudWatch alarms: backend Lambda error rate, backend Lambda duration p99, Loader Lambda failure, RDS connection count
- [ ] SNS topic for alarm notifications, with an email subscription (address provided as a Terraform variable / GH secret)
- [ ] Dashboard panels: backend latency, Loader last-success timestamp, CloudFront 5xx rate

---

**Story 7.9 — Local cron ingestion heartbeat**
_As a developer, I want a heartbeat from the local-cron ingestion job so silent failures are alerted on. Closes the observability gap in [LOCAL_OPERATIONS.md]._

Tasks:

- [ ] On successful local-cron ingestion run, publish a `IngestionHeartbeat` custom metric via `aws cloudwatch put-metric-data`
- [ ] Provision a CloudWatch alarm that fires if no heartbeat is observed within (ingestion frequency + buffer) hours
- [ ] Create a dedicated IAM user for the heartbeat with narrow scope (`cloudwatch:PutMetricData` only); store credentials on the local box
- [ ] Document setup steps in `LOCAL_OPERATIONS.md`

---

### EPIC 8 — Integration, Hardening & Launch

**Goal:** Verify the full data flow end-to-end, harden the app for public access, and produce final documentation.

---

**Story 8.1 — End-to-end verification**
_As a developer, I want to verify that data flows correctly from the API through the database to the frontend before calling the app done._

Tasks:

- ~~[ ] Trigger ingestion Lambda manually and verify data lands in RDS~~ _(superseded by [ADR-005])_
- [ ] Run local ingestion → export JSON → upload to S3 → trigger Loader Lambda → verify data lands in RDS [ADR-005]
- [ ] Call each backend API endpoint via the deployed API Gateway URL and verify correct responses
- [ ] Open the deployed frontend and exercise every view end-to-end
- [ ] Verify auth flow (register → login → protected route → logout)

---

**Story 8.2 — Security hardening**
_As a developer, I want the application secured against basic threats before making it public._

Tasks:

- [ ] Ensure no secrets are hardcoded — all credentials via Secrets Manager or environment variables
- [ ] Add rate limiting to the FastAPI backend (via `slowapi`)
- [ ] Confirm RDS has no public inbound access (VPC only)
- [ ] Set appropriate JWT expiry (e.g. 24 hours) and handle expired token errors gracefully on frontend
- [ ] Review S3 bucket policy — ensure only CloudFront can read objects (Origin Access Control)

---

**Story 8.3 — Final documentation**
_As a developer, I want comprehensive documentation so that anyone viewing the repository understands the project immediately._

Tasks:

- [ ] Write final `README.md` with: project summary, architecture diagram, full tech stack table, local dev setup guide, deployment guide, and API endpoint reference
- [ ] Add architecture diagram (draw.io or Excalidraw — export as PNG, commit to repo)
- [ ] Add screenshots of the running frontend to the README
- [ ] Add inline code comments to complex sections (ingestion strategy, schema design decisions)
- [ ] Document hybrid local-cloud architecture with updated diagram [ADR-005]
- [ ] Document local cron setup for ingestion scheduling [ADR-005]
- [ ] Document manual sync workflow (export → upload → invoke) [ADR-005]
- [ ] Document data recovery procedures using S3 JSON backups [ADR-005]

---

## Suggested Sprint Breakdown (1–3 Month Pace)

| Sprint   | Duration   | Focus                                                      |
| -------- | ---------- | ---------------------------------------------------------- |
| Sprint 1 | Week 1–2   | Epic 1 (Foundation) + Epic 2 (Terraform infrastructure)    |
| Sprint 2 | Week 3–4   | Epic 3 (Schema + Migrations) + Epic 4 (Ingestion pipeline) |
| Sprint 3 | Week 5–6   | Epic 5 (Backend API — auth + all endpoints)                |
| Sprint 4 | Week 7–9   | Epic 6 (Frontend — all views)                              |
| Sprint 5 | Week 10–11 | Epic 7 (CI/CD pipeline)                                    |
| Sprint 6 | Week 12    | Epic 8 (Integration, hardening, documentation)             |

---

## Key Technical Decisions Log

| Decision              | Choice                                                          | Rationale                                                                                                                                                             |
| --------------------- | --------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Frontend framework    | React + TypeScript                                              | Most employer-recognizable; TypeScript signals maturity                                                                                                               |
| Backend language      | Python + FastAPI                                                | Shared with ingestion; modern, fast, auto-docs                                                                                                                        |
| Database              | PostgreSQL (RDS)                                                | Relational model fits domain; industry standard                                                                                                                       |
| ORM                   | SQLAlchemy + Alembic                                            | Python standard; migration workflow is a portfolio skill                                                                                                              |
| Auth                  | JWT (custom)                                                    | No external dependency; demonstrates understanding of auth fundamentals                                                                                               |
| API compute           | Lambda + API Gateway                                            | Free tier; serverless pattern worth knowing                                                                                                                           |
| Frontend hosting      | S3 + CloudFront                                                 | Effectively free; standard static hosting pattern                                                                                                                     |
| IaC                   | Terraform                                                       | Cloud-agnostic; widely recognized across employers                                                                                                                    |
| CI/CD                 | GitHub Actions                                                  | Lives in repo; OIDC AWS auth; highly visible to employers                                                                                                             |
| Repo structure        | Monorepo                                                        | Solo project; reduces friction; unified CI/CD                                                                                                                         |
| Data freshness        | ~~Nightly Lambda (EventBridge)~~ Local cron + S3 sync [ADR-005] | ~~Fits API call budget; serverless; clean pattern~~ Cost-optimized hybrid local-cloud; zero incremental AWS cost [ADR-005]                                            |
| Shared code (ADR-001) | `/shared` package                                               | Eliminates model duplication between `/backend` and `/ingestion`; single source of truth for schema                                                                   |
| Data source (ADR-002) | `nba_api` Python package                                        | Free tier of api-sports.io excluded current season data; `nba_api` provides current season data directly from NBA.com at no cost                                      |
| API design (ADR-006)  | ENDPOINTS.md-driven surface                                     | Endpoints derived from planned frontend pages rather than speculation; discriminated union for `/games/{id}`; removed speculative `vs-matchup`, `injuries`, `compare` |
