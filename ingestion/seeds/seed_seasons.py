from db.session import AsyncSessionLocal
from nbajinni_shared.models.seasons import Season
import asyncio
from datetime import datetime


async def main():
    async with AsyncSessionLocal() as session:
        async with session.begin():
            for year_i in range(1946, datetime.now().year + 1):
                session.add(Season(year=year_i))
        # commits automatically when the block exits

asyncio.run(main())