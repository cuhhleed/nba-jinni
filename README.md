# NBA-Jinni

The only NBA stats and performance tool you'll wish for.

## Local Development Workflow

This project uses a hybrid local-cloud architecture. Data ingestion runs locally and syncs to AWS via S3.

### 1. Start Local Database

Spin up PostgreSQL using Docker Compose:

```bash
docker-compose up -d
```

### 2. Apply Schema Migrations

From the `backend/` directory, apply Alembic migrations to the local database:

```bash
cd backend
poetry run alembic upgrade head
```

### 3. Seed and Ingest Data

From the `ingestion/` directory:

```bash
cd ingestion
poetry install

# Seed reference data (seasons, teams, players)
poetry run python seeds/run_seeds.py

# Run ingestion jobs
poetry run python cli.py nightly      # Last night's game stats
poetry run python cli.py roster       # Refresh team rosters
poetry run python cli.py schedule     # Refresh game schedule
poetry run python cli.py first-start  # Full historical backfill
```

See [docs/LOCAL_OPERATIONS.md](docs/LOCAL_OPERATIONS.md) for cron setup.

### 4. Export to S3

Export local database to Parquet files and sync to the S3 export bucket:

```bash
# Export and upload (from project root)
poetry run python -m backend.export
aws s3 sync exports/ s3://<export-bucket>/
```

### 5. Load into Cloud Database

Trigger the Lambda to apply migrations and load exported data into RDS:

```bash
aws lambda invoke --function-name nbajinni-loader /dev/null
```

The loader Lambda:
- Applies any pending Alembic migrations to RDS
- Imports new Parquet files from S3 into the cloud database

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

## Database Seeding

Seed scripts bootstrap the database with reference data required before the ingestion pipeline can run. Scripts live in `ingestion/seeds/`.

### Prerequisites

- Docker running with the local PostgreSQL container active
- `DATABASE_URL` set in `ingestion/.env`
- All Alembic migrations applied (`poetry run alembic upgrade head` from `backend/`)

### Usage

Run all seed scripts in the correct dependency order from the `ingestion/` directory:

```bash
poetry run python seeds/run_seeds.py
```

Individual scripts can also be run independently if needed:

```bash
poetry run python seeds/seed_seasons.py  # Seeds all NBA seasons from 1946 to present
poetry run python seeds/seed_teams.py    # Seeds all 30 NBA teams with conference data
poetry run python seeds/seed_players.py  # Seeds all active NBA players for the current season
```

### Notes

- All seed scripts are idempotent — safe to run multiple times without creating duplicates
- `seed_players.py` skips free agents (players with no current team)
- Player `birth_date` and Team `logo` are not seeded and will be populated in a future enrichment step
