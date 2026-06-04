# Stats Jinni

> The only NBA stats and performance tool you'll wish for.

Stats Jinni is a full-stack web application for exploring NBA stats, live scores, standings, and player/team performance. It showcases a hybrid local-cloud architecture where data ingestion runs locally on a cron schedule and syncs to AWS via S3, while the frontend and API are fully serverless.

---

## Architecture

**Key design decisions:**

- **Zero-incremental-cost ingestion** — data pipelines run locally and push JSON snapshots to S3; no always-on ingestion infrastructure.
- **Loader Lambda** — a single Lambda applies Alembic migrations and bulk-loads S3 exports into RDS on demand.
- **Live game data** — the backend Lambda proxies `nba_api.live` at request time with a variable-TTL in-memory cache (30s live, 5 min all-final, 30 min pre-game).
- **Serverless backend** — FastAPI served via Mangum on AWS Lambda, accessed through API Gateway.

See [`docs/ARCHITECTURE_DECISIONS.md`](docs/ARCHITECTURE_DECISIONS.md) for all 10 ADRs with full rationale.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 19, TypeScript 5, Vite 7, React Router 7, TanStack Query 5 |
| **Styling** | Tailwind CSS 3, Material Tailwind, Headless UI |
| **Backend** | Python 3.12, FastAPI 0.111, SQLAlchemy 2.0 (async), asyncpg |
| **Data source** | [`nba_api`](https://github.com/swar/nba_api) — direct NBA.com API access, no key required |
| **Database** | PostgreSQL 15 (local Docker for dev, AWS RDS `db.t3.micro` in cloud) |
| **Migrations** | Alembic |
| **Lambda adapter** | Mangum |
| **Rate limiting** | slowapi |
| **Infrastructure** | Terraform 1.8, AWS (Lambda, API Gateway, RDS, S3, CloudFront, VPC, Secrets Manager) |
| **CI/CD** | GitHub Actions with OIDC authentication (no long-lived credentials) |
| **Logging** | structlog (structured JSON logs → CloudWatch) |
| **Observability** | CloudWatch alarms, SNS alerts, single-pane dashboard |

---

## Local Development

### Prerequisites

- Docker (for local PostgreSQL)
- Python 3.12 + [Poetry](https://python-poetry.org/)
- Node.js 20+ + npm
- AWS CLI configured (for S3 sync and Lambda invocation)

### 1. Start Local Database

```bash
docker-compose up -d
```

### 2. Install Dependencies

```bash
# Backend
cd backend && poetry install && cd ..

# Shared package (models, utilities)
cd shared && poetry install && cd ..

# Ingestion pipeline
cd ingestion && poetry install && cd ..

# Frontend
cd frontend && npm install && cd ..
```

### 3. Apply Schema Migrations

```bash
cd backend
poetry run alembic upgrade head
```

### 4. Seed Reference Data

Seeds bootstrap teams, players, and seasons — required before ingestion can run.

```bash
cd ingestion
poetry run python seeds/run_seeds.py
```

Individual seed scripts can be run independently:

```bash
poetry run python seeds/seed_seasons.py  # All NBA seasons from 1946 to present
poetry run python seeds/seed_teams.py    # All 30 teams with conference data
poetry run python seeds/seed_players.py  # Active players for current season
```

All seed scripts are idempotent — safe to re-run.

### 5. Run Ingestion

```bash
cd scripts
./run_ingestion.sh
```

See [`docs/LOCAL_OPERATIONS.md`](docs/LOCAL_OPERATIONS.md) for cron configuration and scheduling.

### 6. Configure Environment variables as shown in .env.example
### 7. Deploy both the frontend and backend locally
```bash
cd scripts
./dev_launch
```

## Cloud Deployment

### Infrastructure

Infrastructure is managed with Terraform. The `dev` environment is the primary deployed environment.

```bash
cd infra/environments/dev
terraform init
terraform plan
terraform apply
```

Terraform provisions: VPC, RDS (private subnet), Lambda (backend + loader), API Gateway, S3 (frontend, data exports, artifacts), CloudFront, CloudWatch observability, IAM roles, and Secrets Manager.

### CI/CD

GitHub Actions workflows run on every push to `main`:

| Workflow | Trigger | Action |
|---|---|---|
| `terraform.yml` | PR / merge to `main` | Plan on PR, apply on merge |
| `backend.yml` | PR / merge to `main` | Lint + test on PR, deploy Lambda on merge |
| `loader.yml` | PR / merge to `main` | Lint + test on PR, deploy Lambda on merge |

All workflows authenticate to AWS via GitHub OIDC — no long-lived credentials stored anywhere.

### Manual Sync Workflow

After local ingestion, push data to the cloud:

```bash
cd scripts/

./package_backend.sh
./package_loader.sh

./deploy_backend.sh
./deploy_loader.sh
./deploy_frontend.sh

./invoke_loader migrate
```

See [`docs/LOCAL_OPERATIONS.md`](docs/LOCAL_OPERATIONS.md) for the full sync runbook, including heartbeat monitoring and alert configuration.

---

## Data Recovery

S3 data exports are versioned with 30-day retention on old versions. To recover from a bad load:

1. Identify the last-known-good JSON export in the S3 data exports bucket (check S3 object versions).
2. Re-invoke the Loader Lambda with `{"action":"load"}` — the loader truncates and reloads from whatever is currently in S3.
3. If the schema is corrupted, invoke with `{"action":"migrate"}` first to replay Alembic migrations.

---
## Project Structure

```
nba-jinni/
├── frontend/          # React + TypeScript SPA
├── backend/           # FastAPI application (deployed as Lambda)
├── ingestion/         # Local data ingestion pipeline (cron-driven)
├── loader/            # S3-to-RDS Loader Lambda (migrate + load)
├── shared/            # Shared SQLAlchemy models and utilities
├── scripts/           # Export, upload, and utility scripts
├── infra/             # Terraform (modules/ + environments/dev/)
├── docs/              # Architecture decisions, operations runbooks, API docs
└── .github/workflows/ # CI/CD pipelines
```

---

## Dev Utilities

### Teardown (dev environment)

Destroys all dev infrastructure except the VPC (which is expensive to recreate):

```bash
./scripts/teardown.sh
```

Builds a `-target` list dynamically from Terraform state, excludes `module.vpc`, runs a destroy plan with a confirmation prompt, and force-deletes Secrets Manager secrets to allow a clean re-apply.

### Database Seeding Notes

- `seed_players.py` skips free agents (no current team)
- `birth_date` and team `logo` fields are not seeded — populated by future enrichment
- All scripts are idempotent

---

## Documentation

| Document | Purpose |
|---|---|
| [`docs/ARCHITECTURE_DECISIONS.md`](docs/ARCHITECTURE_DECISIONS.md) | All 10 ADRs with context and rationale |
| [`docs/LOCAL_OPERATIONS.md`](docs/LOCAL_OPERATIONS.md) | Cron setup, sync workflow, heartbeat monitoring |
| [`docs/backend/ENDPOINTS.md`](docs/backend/ENDPOINTS.md) | Endpoint-to-frontend-page mapping |
| [`docs/SCHEMA_AMENDMENTS.md`](docs/SCHEMA_AMENDMENTS.md) | Alembic pattern for amending populated tables |
| [`docs/PENDING_FEATURES.md`](docs/PENDING_FEATURES.md) | Feature backlog and deferred work |
