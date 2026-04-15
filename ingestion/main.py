import asyncio
from datetime import date

from dotenv import load_dotenv
from sqlalchemy import select

load_dotenv()  # Searches upward from CWD for .env

from nbajinni_shared.logging import configure_logging, get_logger
from nbajinni_shared.models.games import Game
from nbajinni_shared.session import AsyncSessionLocal
from nbajinni_shared.utils import get_current_season, ingest_games, compute_player_averages, compute_team_averages, ingest_standings, ingest_roster, ingest_schedule
from nbajinni_shared.utils import wrapper

configure_logging()
logger = get_logger("ingestion")


def handler(event, context):
    job = event.get("job")

    try:
        if job == "games_stats_nightly":
            asyncio.run(run_nightly())
        elif job == "roster_biweekly":
            asyncio.run(run_roster_biweekly())
        elif job == "schedule_biweekly":
            asyncio.run(run_schedule_biweekly())
        elif job == "first_start":
            asyncio.run(run_first_start())
        else:
            logger.error("unknown_job", job=job)
    except Exception as e:
        logger.error("job_failed", job=job, error=str(e))


async def _run_ingestion_pipeline(session):
    async with session.begin():
        result = await session.execute(
            select(Game).where(Game.status == 1, Game.game_date < date.today())
        )
        games = result.scalars().all()

    processed_games, processed_player_stats, processed_team_stats = await ingest_games(games, session)
    logger.info(
        "game_stat_ingestion_complete",
        message=f"Games Ingested Successfully. {processed_games} games were processed, {processed_player_stats} player stats and {processed_team_stats} team stats added.",
    )

    async with session.begin():
        player_averages_processed = await compute_player_averages(get_current_season(), session)
        logger.info(
            "player_averages_computation_complete",
            message=f"Player Averages Calculated Successfully. {player_averages_processed} player averages updated.",
        )

        team_averages_processed = await compute_team_averages(get_current_season(), session)
        logger.info(
            "team_averages_computation_complete",
            message=f"Team Averages Calculated Successfully. {team_averages_processed} team averages updated.",
        )

        standings_processed = await ingest_standings(session, get_current_season())
        logger.info(
            "standings_refresh_complete",
            message=f"Team Standings Updated Successfully. {standings_processed} standings updated.",
        )


async def run_nightly():
    async with AsyncSessionLocal() as session:
        await _run_ingestion_pipeline(session)


async def run_roster_biweekly():
    async with AsyncSessionLocal() as session:
        async with session.begin():
            processed = await ingest_roster(session, get_current_season())

    logger.info(
        "player_refresh_complete",
        message=f"Players Refresh Completed. Players refreshed: {processed} processed.",
    )


async def run_schedule_biweekly():
    async with AsyncSessionLocal() as session:
        async with session.begin():
            processed = await ingest_schedule(session, get_current_season())

    logger.info(
        "schedule_refresh_complete",
        message=f"Schedule Refresh Completed. Games refreshed: {processed} processed.",
    )




async def run_first_start():
    # reconfigure throttling to accommodate large cold start
    wrapper.reconfigure(back_off_throttle=30.0, call_count_throttle=3.0)
    async with AsyncSessionLocal() as session:
        await _run_ingestion_pipeline(session)


if __name__ == "__main__":
    print("Use: poetry run python cli.py <job>")
    print("Jobs: nightly, roster, schedule, first-start")