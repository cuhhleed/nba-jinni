import asyncio
from pathlib import Path

from dotenv import load_dotenv
from seed_players import main as seed_players
from seed_seasons import main as seed_seasons
from seed_teams import main as seed_teams

load_dotenv(Path(__file__).parent.parent / ".env")


async def main():
    print("==> Seeding seasons...")
    await seed_seasons()

    print("==> Seeding teams...")
    await seed_teams()

    print("==> Seeding players...")
    await seed_players()

    print("==> All seeds completed.")


if __name__ == "__main__":
    asyncio.run(main())
