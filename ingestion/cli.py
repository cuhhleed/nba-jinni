#!/usr/bin/env python
"""CLI for local ingestion jobs.

Usage:
    cd ingestion
    poetry run python cli.py nightly
    poetry run python cli.py roster
    poetry run python cli.py schedule
    poetry run python cli.py first-start
"""
import argparse
import asyncio

from dotenv import load_dotenv
load_dotenv()

from main import run_nightly, run_roster_biweekly, run_schedule_biweekly, run_first_start
from nbajinni_shared.logging import configure_logging, get_logger

configure_logging()
logger = get_logger("cli")

JOBS = {
    "nightly": run_nightly,
    "roster": run_roster_biweekly,
    "schedule": run_schedule_biweekly,
    "first-start": run_first_start,
}

def main():
    parser = argparse.ArgumentParser(description="Run ingestion jobs locally")
    parser.add_argument("job", choices=JOBS.keys(), help="Job to run")
    args = parser.parse_args()

    logger.info("job_starting", job=args.job)
    try:
        asyncio.run(JOBS[args.job]())
        logger.info("job_completed", job=args.job)
    except Exception as e:
        logger.error("job_failed", job=args.job, error=str(e))
        raise

if __name__ == "__main__":
    main()
