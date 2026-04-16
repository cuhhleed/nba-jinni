"""Export all database tables to JSON files under data/exports/.

Run from scripts/:
    poetry install
    poetry run python export_to_json.py

Requires DATABASE_URL in root .env.
"""
import asyncio
import json
import shutil
import tempfile
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from sqlalchemy import text

from nbajinni_shared.logging import configure_logging, get_logger
from nbajinni_shared.session import get_session_factory

configure_logging()
logger = get_logger("export")

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

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "exports"


def _serialize(value):
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (str, int, float, bool, list, dict)):
        return value
    raise TypeError(f"Cannot serialize type {type(value).__name__}")


async def export_table(session, table_name: str) -> list[dict]:
    try:
        result = await session.execute(text(f"SELECT * FROM {table_name}"))
    except Exception as e:
        raise RuntimeError(f"Failed to query table '{table_name}': {e}") from e

    rows = result.mappings().all()
    try:
        return [{k: _serialize(v) for k, v in row.items()} for row in rows]
    except TypeError as e:
        raise RuntimeError(f"Failed to serialize table '{table_name}': {e}") from e


async def main():
    temp_dir = Path(tempfile.mkdtemp(prefix="export_"))
    AsyncSessionLocal = get_session_factory()

    try:
        async with AsyncSessionLocal() as session:
            for table in TABLE_ORDER:
                rows = await export_table(session, table)
                out_path = temp_dir / f"{table}.json"
                out_path.write_text(json.dumps(rows, indent=2))
                logger.info("table_exported", table=table, rows=len(rows))

        # All exports succeeded — move to final destination
        if OUTPUT_DIR.exists():
            shutil.rmtree(OUTPUT_DIR)

        shutil.move(str(temp_dir), str(OUTPUT_DIR))
        logger.info("export_complete", tables=len(TABLE_ORDER), path=str(OUTPUT_DIR))

    except RuntimeError as e:
        logger.error("export_failed", error=str(e))
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
