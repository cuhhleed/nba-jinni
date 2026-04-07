import asyncio
from pathlib import Path

from dotenv import load_dotenv
from datetime import datetime, date
from nba_api.stats.endpoints import ScheduleLeagueV2
from nbajinni_shared.logging import configure_logging, get_logger
from nbajinni_shared.models.players import Player
from nbajinni_shared.models.player_game_stats import PlayerGameStat
from nbajinni_shared.models.team_game_stats import TeamGameStat
from nbajinni_shared.models.games import Game
from nbajinni_shared.nba_api_wrapper import NbaApiWrapper
from nbajinni_shared.session import AsyncSessionLocal
from nbajinni_shared.utils import get_all_players, get_all_games, get_current_season, get_game_stats, ingest_games, compute_player_averages, compute_team_averages, ingest_standings
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select

load_dotenv(Path(__file__).parent / ".env")
configure_logging()
logger = get_logger("ingestion")
wrapper = NbaApiWrapper()


def handler(event, context):
    job = event.get("job")

    try:
        if job == "games_stats_nightly":
            asyncio.run(run_nightly())
        elif job == "roster_biweekly":
            asyncio.run(run_roster_biweekly())
        elif job == "schedule_biweekly":
            asyncio.run(run_schedule_biweekly())
        elif job == "backfill":
            run_backfill()
        else:
            logger.error("unknown_job", job=job)
    except Exception as e:
        logger.error("job_failed", job=job, error=str(e))


async def run_nightly():

    async with AsyncSessionLocal() as session:
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

            player_averages_processed =  await compute_player_averages(get_current_season(), session)
            logger.info(
                "player_averages_computation_complete",
                message=f"Player Averages Calculated Successfully. {player_averages_processed} player averages updated.",
            )

            team_averages_processed =  await compute_team_averages(get_current_season(), session)
            logger.info(
                "team_averages_computation_complete",
                message=f"Team Averages Calculated Successfully. {team_averages_processed} team averages updated.",
            )

            standings_processed = await ingest_standings(session, get_current_season())
            logger.info(
                "standings_refresh_complete",
                message=f"Team Standings Updated Successfully. {standings_processed} standings updated.",
            )


async def run_roster_biweekly():

    players = await get_all_players()
    processed = 0

    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(update(Player).values(active=False))

            for _, player in players.iterrows():
                if player["TEAM_ID"] == 0:
                    continue

                full_name_split = player["DISPLAY_FIRST_LAST"].split(" ")
                first_name = full_name_split[0]
                last_name = " ".join(full_name_split[1:])
                stmt = (
                    insert(Player)
                    .values(
                        id=player["PERSON_ID"],
                        first_name=first_name,
                        last_name=last_name,
                        team_id=player["TEAM_ID"],
                        birth_date=None,
                    )
                    .on_conflict_do_update(
                        index_elements=["id"],
                        set_={
                            "first_name": first_name,
                            "last_name": last_name,
                            "team_id": player["TEAM_ID"],
                            "birth_date": None,
                            "active": True,
                        },
                    )
                )
                result = await session.execute(stmt)
                if result.rowcount == 1:
                    processed += 1

    logger.info(
        "player_refresh_complete",
        message=f"Players Refresh Completed. Players refreshed: {processed} processed.",
    )


async def run_schedule_biweekly():
    games = await get_all_games()
    processed = 0

    async with AsyncSessionLocal() as session:
        async with session.begin():

            for _, game in games.iterrows():
                if game["gameLabel"]:
                    continue
                
                game_date = datetime.strptime(game["gameDate"], "%m/%d/%Y %H:%M:%S").date()

                stmt = (
                    insert(Game)
                    .values(
                        id=game["gameId"],
                        home_team_id=game["homeTeam_teamId"],
                        away_team_id=game["awayTeam_teamId"],
                        game_date=game_date,
                        season=get_current_season(),
                        status=game["gameStatus"]
                    )
                    .on_conflict_do_update(
                        index_elements=["id"],
                        set_={
                            "home_team_id": game["homeTeam_teamId"],
                            "away_team_id": game["awayTeam_teamId"],
                            "game_date": game_date
                        },
                    )
                )
                result = await session.execute(stmt)
                if result.rowcount == 1:
                    processed += 1

    logger.info(
        "schedule_refresh_complete",
        message=f"Schedule Refresh Completed. Games refreshed: {processed} processed.",
    )




def run_backfill():
    pass


if __name__ == "__main__":
    asyncio.run(run_nightly())