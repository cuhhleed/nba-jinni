import asyncio
from pathlib import Path

from dotenv import load_dotenv
from nbajinni_shared.models.players import Player
from nbajinni_shared.session import AsyncSessionLocal
from nbajinni_shared.utils import get_all_players, get_current_season
from sqlalchemy.dialects.postgresql import insert

load_dotenv(Path(__file__).parent.parent / ".env")


async def main():
    current_season = get_current_season()
    players = await get_all_players(current_season)
    await upsert_players(players)


async def upsert_players(players):
    inserted = 0
    skipped = 0

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
                result = await session.execute(stmt)
                if result.rowcount == 1:
                    inserted += 1
                else:
                    skipped += 1

    print(
        f"Players Seeding Completed. Players seeded: {inserted} inserted, "
        f"{skipped} already existed"
    )


if __name__ == "__main__":
    asyncio.run(main())
