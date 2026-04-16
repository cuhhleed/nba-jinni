import asyncio
from datetime import datetime
from nbajinni_shared.models.seasons import Season
from nbajinni_shared.session import get_session_factory
from nbajinni_shared.logging import configure_logging, get_logger
from sqlalchemy.dialects.postgresql import insert

configure_logging()
logger = get_logger("seasons_seeding")

async def main(env="dev"):
    logger.info("seeding_seasons", environment=env)

    inserted = 0
    skipped = 0
    AsyncSessionLocal = get_session_factory(env)
    async with AsyncSessionLocal() as session:
        async with session.begin():
            for year_i in range(1946, datetime.now().year + 1):
                season_str = f"{year_i}-{str(year_i + 1)[2:]}"
                stmt = insert(Season).values(season=season_str).on_conflict_do_nothing()

                try:
                    result = await session.execute(stmt)
                except Exception as e:
                    logger.error("season_insert_failed",
                                    season=season_str,
                                    environment=env,
                                    error=str(e))
                    raise

                if result.rowcount == 1:
                    inserted += 1
                else:
                    skipped += 1
    
    logger.info("seasons_seeding_completed", 
                message=f"Seasons Seeding Completed. Seasons seeded: {inserted} inserted, {skipped} already existed")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--env")
    args = parser.parse_args()
    asyncio.run(main(env=args.env))
