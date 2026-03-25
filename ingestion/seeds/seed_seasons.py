from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent.parent / ".env")

from nbajinni_shared.session import AsyncSessionLocal
from nbajinni_shared.models.seasons import Season
from sqlalchemy.dialects.postgresql import insert
import asyncio
from datetime import datetime


async def main():
    inserted = 0
    skipped = 0
    async with AsyncSessionLocal() as session:
        async with session.begin():
            for year_i in range(1946, datetime.now().year + 1):
                stmt = insert(Season).values(year=year_i).on_conflict_do_nothing()
                result = await session.execute(stmt)
                if result.rowcount == 1:
                    inserted += 1
                else:
                    skipped += 1
        # commits automatically when the block exits
    
    print(f"Seasons Seeding Completed. Seasons seeded: {inserted} inserted, {skipped} already existed")

if __name__ == "__main__":
    asyncio.run(main())