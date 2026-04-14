"""Loader Lambda — downloads JSON exports from S3 and loads them into RDS.

Environment variables (injected by Terraform):
    DB_HOST (endpoint with port), DB_NAME, DB_USER, DB_PASSWORD
    DATA_BUCKET_NAME
"""
import asyncio
import json
import os
from datetime import date, datetime
from alembic.config import Config
from alembic import command

import boto3
from sqlalchemy import text

from nbajinni_shared.logging import configure_logging, get_logger
from nbajinni_shared.session import AsyncSessionLocal

configure_logging()
logger = get_logger("loader")

S3_PREFIX = "exports"

# FK-safe insertion order (parents before children)
TABLE_ORDER = [
    "seasons",
    "teams",
    "users",
    "players",
    "games",
    "standings",
    "player_game_stats",
    "team_game_stats",
    "player_season_averages",
    "team_season_averages",
]

# Columns that must be cast back to Python date/datetime objects
DATE_COLUMNS: dict[str, set[str]] = {
    "games": {"game_date"},
    "players": {"birth_date"},
    "standings": {"updated_at"},
    "users": {"created_at"},
}


def _parse_row(table: str, row: dict) -> dict:
    date_cols = DATE_COLUMNS.get(table, set())
    result = {}
    for k, v in row.items():
        if k in date_cols and isinstance(v, str):
            try:
                result[k] = datetime.fromisoformat(v)
            except ValueError:
                result[k] = date.fromisoformat(v)
        else:
            result[k] = v
    return result


def _fetch_json(s3_client, bucket: str, table: str) -> list[dict]:
    key = f"{S3_PREFIX}/{table}.json"
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        return json.loads(response["Body"].read())
    except Exception as e:
        logger.error("s3_fetch_failed", table=table, key=key, bucket=bucket, error=str(e))
        raise


async def load(bucket: str):
    s3 = boto3.client("s3")

    async with AsyncSessionLocal() as session:
        async with session.begin():
            # Truncate in reverse FK order
            logger.info("truncating_tables")
            for table in reversed(TABLE_ORDER):
                try:
                    await session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
                except Exception as e:
                    logger.error("truncate_failed", table=table, error=str(e))
                    raise

            # Insert in FK-safe order
            for table in TABLE_ORDER:
                rows = _fetch_json(s3, bucket, table)
                if not rows:
                    logger.info("table_empty", table=table)
                    continue

                columns = list(rows[0].keys())
                placeholders = ", ".join(f":{col}" for col in columns)
                col_list = ", ".join(f'"{col}"' for col in columns)
                stmt = text(
                    f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"
                )
                parsed = [_parse_row(table, row) for row in rows]

                try:
                    await session.execute(stmt, parsed)
                except Exception as e:
                    logger.error("insert_failed", table=table, rows=len(rows), error=str(e))
                    raise

                logger.info("table_loaded", table=table, rows=len(rows))

def migrate():
    try:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        logger.info("migration_complete", tables=len(TABLE_ORDER))
    except Exception as e:
        logger.error("migration_failed", error=str(e))
        raise

def handler(event, context):
    action = event.get("action")
    bucket = os.environ["DATA_BUCKET_NAME"]

    body_message = "Load complete."

    if action == "migrate":
        migrate()
        body_message = "Migration and load complete."
    elif action != "load":
        return {"statusCode": 500, "body": "Invalid action given."}
    
    try:
        asyncio.run(load(bucket))
        logger.info("load_complete", tables=len(TABLE_ORDER))
        return {"statusCode": 200, "body": body_message}
    except Exception as e:
        logger.error("load_failed", error=str(e))
        raise
