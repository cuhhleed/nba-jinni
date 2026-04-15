# Local Operations Guide

This document covers how to run ingestion jobs locally, set up the helper script, and configure cron for automated execution.

---

## CLI Usage

All commands are run from the `ingestion/` directory using Poetry.

### Available Jobs

| Job | Command | Description |
|-----|---------|-------------|
| `nightly` | `poetry run python cli.py nightly` | Fetch and store last night's game stats |
| `roster` | `poetry run python cli.py roster` | Refresh all team rosters |
| `schedule` | `poetry run python cli.py schedule` | Refresh the game schedule |
| `first-start` | `poetry run python cli.py first-start` | Full historical backfill for cold start |

### Script Entry Point

If the `ingest` script entry is registered (via `pyproject.toml`), you can also invoke jobs as:

```bash
poetry run ingest <job>
```

For example:

```bash
poetry run ingest nightly
poetry run ingest roster
```

---

## Helper Script

`scripts/run_ingestion.sh` wraps the CLI so it can be called from any working directory.

### What it does

- Resolves the project root relative to the script's own location — no hardcoded paths required.
- Sources `.env` from the project root if the file exists, exporting all variables into the environment before running.
- Changes into `ingestion/` and delegates to `poetry run python cli.py <job>`.

### Make it executable

Run this once after cloning the repo:

```bash
chmod +x scripts/run_ingestion.sh
```

### Manual invocation

```bash
/path/to/nba-jinni/scripts/run_ingestion.sh nightly
/path/to/nba-jinni/scripts/run_ingestion.sh roster
```

---

## Crontab Setup

Use `crontab -e` to open your crontab. Replace `/path/to/nba-jinni` with the absolute path to your local clone.

```cron
# Nightly game stats at 9 AM UTC
0 9 * * * /path/to/nba-jinni/scripts/run_ingestion.sh nightly

# Roster refresh semi-monthly (1st and 15th)
0 6 1,15 * * /path/to/nba-jinni/scripts/run_ingestion.sh roster

# Schedule refresh semi-monthly (1st and 15th)
0 7 1,15 * * /path/to/nba-jinni/scripts/run_ingestion.sh schedule
```

### Logging cron output

Redirect output to a log file to capture errors from unattended runs:

```cron
0 9 * * * /path/to/nba-jinni/scripts/run_ingestion.sh nightly >> /var/log/nba-jinni/nightly.log 2>&1
```

Create the log directory beforehand:

```bash
sudo mkdir -p /var/log/nba-jinni
sudo chown $USER /var/log/nba-jinni
```

---

## Full Sync Workflow

Running a job locally only writes to the local database. To propagate data to the cloud, the full pipeline is:

1. **Ingest** — `run_ingestion.sh <job>` fetches from the NBA API and writes rows into local PostgreSQL.
2. **Export** — An export step reads from PostgreSQL and writes Parquet files to a local staging area.
3. **Upload** — The Parquet files are synced to the S3 bucket (see ADR-005 for the versioning and path conventions).
4. **Load** — The Lambda loader detects the new S3 objects and imports them into the cloud DuckDB instance.

Steps 2–4 are not triggered by `run_ingestion.sh` and must be run separately or scheduled independently.
