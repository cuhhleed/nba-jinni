import asyncio
from nba_api.stats.endpoints import LeagueStandingsV3
from nba_api.stats.static import teams as nba_teams
from nbajinni_shared.models.teams import Team
from nbajinni_shared.session import get_session_factory
from sqlalchemy.dialects.postgresql import insert


async def main(env="dev"):
    teams = get_teams()
    conferences = await get_conference_map()
    await upsert_teams(teams, conferences, env)


def get_teams():
    return nba_teams.get_teams()


async def get_conference_map():
    standings = await asyncio.to_thread(LeagueStandingsV3)
    df = standings.get_data_frames()[0]
    return dict(zip(df["TeamID"], df["Conference"]))


async def upsert_teams(teams, conference_map, env):
    inserted = 0
    skipped = 0

    AsyncSessionLocal = get_session_factory(env)
    async with AsyncSessionLocal() as session:
        async with session.begin():
            for team in teams:
                stmt = (
                    insert(Team)
                    .values(
                        id=team["id"],
                        name=team["full_name"],
                        nickname=team["nickname"],
                        code=team["abbreviation"],
                        conference=conference_map.get(team["id"]),
                        logo=None,
                    )
                    .on_conflict_do_update(
                        index_elements=["id"],
                        set_={
                            "name": team["full_name"],
                            "nickname": team["nickname"],
                            "code": team["abbreviation"],
                            "conference": conference_map.get(team["id"]),
                            "logo": None,
                        },
                    )
                )
                result = await session.execute(stmt)
                if result.rowcount == 1:
                    inserted += 1
                else:
                    skipped += 1

    print(
        f"Teams Seeding Completed. Teams seeded: {inserted} inserted, "
        f"{skipped} already existed"
    )


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--env")
    args = parser.parse_args()
    asyncio.run(main(env=args.env))