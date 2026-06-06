# Architecture Overview

NBAJinni uses a hybrid local-cloud architecture. Data ingestion runs locally on a cron schedule and syncs to AWS via S3; the frontend and API are fully serverless.

---

## System Diagram

<img width="824" height="566" alt="NBAJINNI_ARCHITECTURE" src="https://github.com/user-attachments/assets/6de9c5df-1f79-4ee6-ac36-710c149cc586" />
---

## Components

### Data Ingestion (local)

The ingestion pipeline runs on the developer's machine via cron. It fetches from the NBA API (`nba_api`) and writes into a local PostgreSQL instance running in Docker. No always-on AWS infrastructure is required for ingestion — this eliminates the ~$32/month NAT Gateway cost that a VPC-attached ingestion Lambda would require.

See [`docs/LOCAL_OPERATIONS.md`](LOCAL_OPERATIONS.md) for cron setup, scheduling, and the heartbeat monitoring setup.

### S3 Data Exports

After each ingestion run, the local database is exported to JSON files and uploaded to a versioned S3 bucket. One file per table. This bucket acts as both the sync medium and as daily point-in-time backups.

See [`docs/LOCAL_OPERATIONS.md`](LOCAL_OPERATIONS.md#data-recovery) for the recovery procedure.

### Loader Lambda

A Lambda function that runs inside the VPC and has access to both S3 (via a free S3 Gateway VPC Endpoint — no NAT required) and RDS. It supports two actions via the event payload:

- `{"action": "migrate"}` — runs Alembic migrations against RDS
- `{"action": "load"}` — truncates all tables (in reverse FK order) and bulk-inserts from S3 JSON exports (in FK-safe order)

### RDS PostgreSQL

PostgreSQL 15 on `db.t3.micro` in a private subnet. No public inbound access — reachable only from within the VPC. Credentials are stored in AWS Secrets Manager and injected at Lambda startup.

### Backend Lambda

FastAPI application served via [Mangum](https://github.com/jordaneremieff/mangum), which adapts the ASGI interface to the Lambda event/context model. Runs in the private VPC subnet alongside RDS.

Two endpoint groups have a different data path:

- **Standard endpoints** — read from RDS via SQLAlchemy async sessions.
- **Live endpoints** (`/games/live/today`, `/games/live/{game_id}`) — proxy `nba_api.live` at request time via `asyncio.to_thread`, with a variable-TTL in-process `StaleCache` (30s if any game is live, 5 min if all final, 30 min pre-game). Live data is never written to RDS.

The backend Lambda requires outbound internet access (for live endpoints) and is connected to the internet via a NAT Gateway. See [ADR-008](ARCHITECTURE_DECISIONS.md) for the interim NAT Gateway decision and the planned split-Lambda migration that would eliminate it.

### API Gateway

AWS HTTP API routes all requests to the backend Lambda. CORS is configured to allow requests from the CloudFront distribution domain.

### Frontend

React 19 + TypeScript SPA built with Vite, hosted on S3, served via CloudFront with Origin Access Control (only CloudFront can read from the bucket). The SPA uses React Router 7 for client-side routing; 404 errors are redirected to `index.html` at the CloudFront level to support deep linking.

---

## Data Flow Summary

| Flow | Path |
|---|---|
| User views frontend | Browser → CloudFront → S3 (static assets) |
| User calls API | Browser → API Gateway → Backend Lambda → RDS |
| Live scores | Browser → API Gateway → Backend Lambda → NBA CDN (via NAT) → StaleCache |
| Nightly data sync | Local cron → nba_api → local PostgreSQL → JSON export → S3 → Loader Lambda → RDS |

---

## Infrastructure as Code

All AWS infrastructure is defined in Terraform under `infra/`. The project uses a modular structure:

```
infra/
├── environments/
│   ├── dev/        — primary deployed environment
│   └── shared/     — account-wide CI bootstrap (OIDC provider, IAM roles, GitHub environments)
└── modules/
    ├── vpc/        — VPC, subnets, NAT Gateway, S3 VPC endpoint
    ├── rds/        — PostgreSQL instance, Secrets Manager
    ├── lambda/     — Lambda function + IAM role
    ├── api_gateway/— HTTP API + routes
    ├── cloudfront/ — CDN distribution + Origin Access Control
    ├── s3/         — S3 buckets (frontend, data exports, Lambda artifacts)
    ├── observability/ — CloudWatch alarms, SNS topic, dashboard
    ├── security_groups/ — Lambda and RDS security groups
    └── github_actions_oidc/ — OIDC provider + per-env IAM roles
```

CI/CD uses GitHub OIDC authentication — no long-lived credentials. See [ADR-010](ARCHITECTURE_DECISIONS.md) for details.

---

## Key Design Decisions

See [`docs/ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md) for the full record of all 10 ADRs, including:

- **ADR-002** — Why `nba_api` replaced api-sports.io (cost + current-season access)
- **ADR-005** — Why ingestion runs locally instead of in Lambda (cost: eliminates NAT Gateway)
- **ADR-007** — How live game data is served without writing to RDS (in-process cache + NBA CDN)
- **ADR-008** — NAT Gateway as interim solution; planned split-Lambda migration to eliminate it
- **ADR-009** — How playoff data is stored alongside regular season data (unified tables with `game_type` discriminator)
- **ADR-010** — GitHub OIDC for zero-credential CI/CD
