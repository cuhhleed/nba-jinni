from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent / ".env")

import asyncio
from nbajinni_shared.session import AsyncSessionLocal
from nbajinni_shared.logging import get_logger
from nbajinni_shared.logging import configure_logging
from nbajinni_shared.nba_api_wrapper import NbaApiWrapper
from nbajinni_shared.models.players import Player
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import update
from nbajinni_shared.utils import get_all_players

configure_logging()
logger = get_logger("ingestion")
wrapper = NbaApiWrapper()


def handler(event, context):
    job = event.get("job")
    
    try:
        if job == "nightly":
            run_nightly()
        elif job == "biweekly":
            asyncio.run(run_biweekly())
        elif job == "backfill":
            run_backfill()
        else:
            logger.error("unknown_job", job=job)
    except Exception as e:
        logger.error("job_failed", job=job, error=str(e))
    

def run_nightly():
    pass

async def run_biweekly():

    players = await get_all_players()
    processed = 0

    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(update(Player).values(active=False))

            for _, player in players.iterrows():
                if player["TEAM_ID"] == 0:
                    continue

                full_name_split = player["DISPLAY_FIRST_LAST"].split(' ')
                first_name = full_name_split[0]
                last_name = ' '.join(full_name_split[1:])
                stmt = insert(Player).values(
                    id=player["PERSON_ID"],
                    first_name=first_name,
                    last_name=last_name,
                    team_id=player["TEAM_ID"],
                    birth_date=None
                ).on_conflict_do_update(
                    index_elements=["id"],
                    set_={
                        "first_name": first_name,
                        "last_name": last_name,
                        "team_id": player["TEAM_ID"],
                        "birth_date": None,
                        "active": True
                    }
                )
                result = await session.execute(stmt)
                if result.rowcount == 1:
                    processed += 1

    logger.info("player_refresh_complete", message=f"Players Refresh Completed. Players refreshed: {processed} processed.")

def run_backfill():
    pass
