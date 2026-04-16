import asyncio

from nbajinni_shared.models.players import Player
from nbajinni_shared.session import get_session_factory
from nbajinni_shared.logging import configure_logging, get_logger
from nbajinni_shared.utils import get_all_players, get_current_season
from sqlalchemy.dialects.postgresql import insert

configure_logging()
logger = get_logger("players_seeding")

async def main(env="dev"):
    logger.info("seeding_players", environment=env)
    current_season = get_current_season()
    try:
        players = await get_all_players(current_season)
    except Exception as e:
        logger.error("players_fetch_failed", error=str(e))
        raise
    await upsert_players(players, env)


async def upsert_players(players, env):
    inserted = 0
    skipped = 0

    AsyncSessionLocal = get_session_factory(env)
    async with AsyncSessionLocal() as session:
        async with session.begin():
            for _, player in players.iterrows():
                if player["TEAM_ID"] == 0:
                    skipped += 1
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

                try:
                    result = await session.execute(stmt)
                except Exception as e:
                    logger.error("player_insert_failed",
                                    player_id=player["PERSON_ID"],
                                    player_name=player["DISPLAY_FIRST_LAST"], 
                                    environment=env,
                                    error=str(e))
                    raise
                if result.rowcount == 1:
                    inserted += 1
                else:
                    skipped += 1


    logger.info("player_seeding_complete",
                message=f"Players Seeding Completed. Players seeded: {inserted} inserted, {skipped} already existed")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--env")
    args = parser.parse_args()
    asyncio.run(main(env=args.env))
