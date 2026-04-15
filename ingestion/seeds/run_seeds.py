import asyncio

from dotenv import load_dotenv

load_dotenv()  # Searches upward from CWD for .env

from seed_players import main as seed_players
from seed_seasons import main as seed_seasons
from seed_teams import main as seed_teams


async def main(env="dev"):
    print("==> Seeding seasons...")
    await seed_seasons(env=env)

    print("==> Seeding teams...")
    await seed_teams(env=env)

    print("==> Seeding players...")
    await seed_players(env=env)

    print("==> All seeds completed.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--env")
    args = parser.parse_args()
    asyncio.run(main(env=args.env))
