import asyncio
from seed_players import main as seed_players
from seed_seasons import main as seed_seasons
from seed_teams import main as seed_teams
from nbajinni_shared.logging import configure_logging, get_logger

configure_logging()
logger = get_logger("pre_ingestion_seeding")

async def main(env="dev"):
    logger.info("seeding_started", environment=env)
    await seed_seasons(env=env)
    await seed_teams(env=env)
    await seed_players(env=env)

    logger.info("seeding_complete", environment=env)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", default="dev")
    args = parser.parse_args()
    asyncio.run(main(env=args.env))
