import asyncio
from datetime import datetime
from nbajinni_shared.models.seasons import Season
from nbajinni_shared.session import get_session_factory
from sqlalchemy.dialects.postgresql import insert


async def main(env="dev"):
    inserted = 0
    skipped = 0
    AsyncSessionLocal = get_session_factory(env)
    async with AsyncSessionLocal() as session:
        async with session.begin():
            for year_i in range(1946, datetime.now().year + 1):
                season_str = f"{year_i}-{str(year_i + 1)[2:]}"
                stmt = insert(Season).values(season=season_str).on_conflict_do_nothing()
                result = await session.execute(stmt)
                if result.rowcount == 1:
                    inserted += 1
                else:
                    skipped += 1

    print(
        f"Seasons Seeding Completed. Seasons seeded: {inserted} inserted, "
        f"{skipped} already existed"
    )


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--env")
    args = parser.parse_args()
    asyncio.run(main(env=args.env))
