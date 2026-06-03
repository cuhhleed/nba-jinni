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
| `playoff-schedule` | `poetry run python cli.py playoff-schedule` | Refresh the playoff schedule |
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

### `run_ingestion.sh` vs `run_cron_sync.sh`

`run_ingestion.sh` **only writes to the local database** — useful for manual testing or debugging a single ingestion step without touching cloud resources.

`run_cron_sync.sh` runs the **full pipeline**: ingest → export to JSON → upload to S3 → invoke the Loader Lambda asynchronously → emit an `IngestionHeartbeat` metric to CloudWatch. This is the script used by cron. The heartbeat is emitted last so its presence signals that every preceding step completed successfully. The `first-start` job is intentionally excluded from `run_cron_sync.sh` because it is a one-time cold-start operation; run it manually via `run_ingestion.sh`.

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
AWS_PROFILE=nbajinni-dev-cron
PATH=/usr/local/bin:/usr/bin:/bin

# Nightly stats — hourly within NBA game window (16:00 UTC noon ET tip → 07:00 UTC ~2 AM ET cushion)
0 16-23,0-7 * * * /path/to/nba-jinni/scripts/run_cron_sync.sh nightly      >> /var/log/nba-jinni/nightly.log 2>&1

# Roster refresh weekly (Sunday 06:00 UTC). Cadence dictated by the 7-day max alarm window in CloudWatch.
0 6 * * 0 /path/to/nba-jinni/scripts/run_cron_sync.sh roster >> /var/log/nba-jinni/roster.log 2>&1

# Schedule refresh weekly (Sunday 07:00 UTC)
0 7 * * 0 /path/to/nba-jinni/scripts/run_cron_sync.sh schedule >> /var/log/nba-jinni/schedule.log 2>&1

# Playoff schedule refresh weekly (Sunday 08:00 UTC)
0 8 * * 0 /path/to/nba-jinni/scripts/run_cron_sync.sh playoff-schedule >> /var/log/nba-jinni/playoff-schedule.log 2>&1
```

> **Cadence — schedule on a fixed weekday, not on days of the month.** The `roster`, `schedule`, and `playoff-schedule` jobs run weekly on a fixed weekday (Sunday) by design. Avoid day-of-month patterns such as `0 8 1,15 * *`: they produce uneven 14–17 day gaps, and they carry a start-up gotcha — if you install the crontab *after* the 1st has passed, the first run slips to the 15th. During the playoffs that gap can drop a freshly-decided series from the schedule for up to two weeks: this is exactly how the 2025-26 Finals matchup went un-ingested until the gap was noticed. A fixed-weekday cron keeps a consistent 7-day cadence, which is also the maximum window the heartbeat alarms can cover (see [Per-job alarms](#per-job-alarms)).

### Logging cron output

Log files are written to `/var/log/nba-jinni/<job>.log` as shown in the crontab block above.

Create the log directory beforehand:

```bash
sudo mkdir -p /var/log/nba-jinni
sudo chown $USER /var/log/nba-jinni
```

---

## Full Sync Workflow

Running a job locally only writes to the local database. To propagate data to the cloud, the full pipeline is:

1. **Ingest** — Fetches from the NBA API and writes rows into local PostgreSQL.
2. **Export** — Reads from PostgreSQL and writes JSON files to a local staging area.
3. **Upload** — The JSON files are synced to the S3 bucket (see ADR-005 for the versioning and path conventions).
4. **Load** — The Lambda loader detects the new S3 objects and imports them into the cloud DuckDB instance.

Steps 2–4 are now performed automatically by `run_cron_sync.sh` after the ingestion step. Use `run_ingestion.sh` only when you want to run the ingest step in isolation (local DB only, no cloud propagation).

---

## Cron heartbeat & alerting

### IAM user

Every cron run publishes an `IngestionHeartbeat` metric to CloudWatch. This requires a dedicated IAM user (`nbajinni-dev-cron-runner`) with narrow permissions:

- `cloudwatch:PutMetricData` (restricted to namespace `NBAJinni/Ingestion`)
- `s3:PutObject` on the data-exports bucket under `exports/*`
- `lambda:InvokeFunction` on the Loader Lambda

The user and its access key are provisioned by Terraform (`aws_iam_user.cron_runner` in `infra/environments/dev/main.tf`). After running `terraform apply`, retrieve the credentials with:

```bash
terraform output -raw cron_runner_access_key_id
terraform output -raw cron_runner_secret_access_key
```

### AWS profile setup (one-time)

Configure a named profile on the local machine using the credentials above:

```bash
aws configure --profile nbajinni-dev-cron
```

Set the region to `us-east-1`. This profile name matches the `AWS_PROFILE=nbajinni-dev-cron` header in the crontab block and the default in `run_cron_sync.sh`.

### Metric & dimensions

| Field | Value |
|-------|-------|
| Namespace | `NBAJinni/Ingestion` |
| Metric name | `IngestionHeartbeat` |
| Dimension | `JobName=<job>` |
| Value | `1` (Count) |

The metric is published at the end of `run_cron_sync.sh`, so its presence confirms that every step in the pipeline completed without error.

### Per-job alarms

| Job | Cron expression | Alarm window |
|-----|-----------------|--------------|
| `nightly` | `0 16-23,0-7 * * *` | 3h consecutive miss (hourly during 16:00-07:00 UTC game window) |
| `roster` | `0 6 * * 0` | 7 daily periods (CloudWatch max; ≈1-day buffer past weekly cadence) |
| `schedule` | `0 7 * * 0` | 7 daily periods (CloudWatch max; ≈1-day buffer past weekly cadence) |
| `playoff-schedule` | `0 8 * * 0` | 7 daily periods (CloudWatch max; ≈1-day buffer past weekly cadence) |

The `roster`, `schedule`, and `playoff-schedule` alarms use `treat_missing_data = "breaching"` and fire via the existing SNS alerts topic when no heartbeat is observed within the window. The 7-day window is the CloudWatch hard limit for alarms with `period >= 3600s` (EvaluationPeriods × Period must be ≤ 604,800s), which is why these jobs are weekly rather than biweekly. Alarms are provisioned by Terraform in `infra/modules/observability/main.tf`.

The `nightly` alarm uses `treat_missing_data = "missing"` (vs. `"breaching"` for the biweekly alarms). During the daytime gap (07:00–16:00 UTC) the cron does not fire, so no datapoints arrive; CloudWatch treats those hours as INSUFFICIENT_DATA rather than as alarm-triggering missed runs. Only 3 consecutive **in-window** misses trip the alarm.

### Bootstrap order

1. Run `terraform apply` in `infra/environments/dev/` to provision the IAM user and alarms.
2. Retrieve credentials and run `aws configure --profile nbajinni-dev-cron` on the local machine.
3. Run `chmod +x scripts/run_cron_sync.sh` once after cloning.
4. Add the crontab entries (see [Crontab Setup](#crontab-setup) above).
5. Create the log directory (`sudo mkdir -p /var/log/nba-jinni && sudo chown $USER /var/log/nba-jinni`).
6. Confirm the first heartbeat appears in the CloudWatch console under `NBAJinni/Ingestion`.
