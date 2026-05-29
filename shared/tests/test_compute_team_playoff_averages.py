from sqlalchemy import select, func

from nbajinni_shared.utils import compute_team_playoff_averages
from nbajinni_shared.models.team_playoff_season_averages import TeamPlayoffSeasonAverage
from nbajinni_shared.models.team_game_stats import TeamGameStat
from nbajinni_shared.models.games import Game
from datetime import date, datetime


async def _expected_team_averages(session, season, team_id):
    result = await session.execute(
        select(
            func.count(TeamGameStat.game_id).label("games_played"),
            func.round(func.avg(TeamGameStat.points), 1).label("points"),
            func.round(func.avg(TeamGameStat.opponent_points), 1).label("opponent_points"),
            func.round(func.avg(TeamGameStat.rebounds), 1).label("rebounds"),
            func.round(func.avg(TeamGameStat.assists), 1).label("assists"),
            func.round(func.avg(TeamGameStat.steals), 1).label("steals"),
            func.round(func.avg(TeamGameStat.blocks), 1).label("blocks"),
            func.round(func.avg(TeamGameStat.turnovers), 1).label("turnovers"),
            func.round(func.avg(TeamGameStat.fg_pct), 3).label("fg_pct"),
            func.round(func.avg(TeamGameStat.three_pct), 3).label("three_pct"),
            func.round(func.avg(TeamGameStat.ft_pct), 3).label("ft_pct"),
        )
        .where(
            TeamGameStat.season == season,
            TeamGameStat.team_id == team_id,
            TeamGameStat.game_type == "playoff",
        )
    )
    return result.one()


async def test_first_time_insert(
    session, test_season, test_home_team, test_away_team, test_playoff_game
):
    stat = TeamGameStat(
        game_id=test_playoff_game.id,
        team_id=test_home_team.id,
        season=test_season.season,
        points=115,
        opponent_points=108,
        rebounds=48,
        assists=28,
        steals=9,
        blocks=6,
        turnovers=10,
        fg_pct=0.480,
        three_pct=0.390,
        ft_pct=0.830,
        game_type="playoff",
    )
    session.add(stat)
    await session.flush()

    result = await compute_team_playoff_averages(test_season.season, session)

    assert result == 1

    rows = (await session.execute(select(TeamPlayoffSeasonAverage))).scalars().all()
    assert len(rows) == 1

    avg = rows[0]
    expected = await _expected_team_averages(session, test_season.season, test_home_team.id)

    assert avg.team_id == test_home_team.id
    assert avg.season == test_season.season
    assert avg.games_played == expected.games_played
    assert avg.points == expected.points
    assert avg.opponent_points == expected.opponent_points
    assert avg.rebounds == expected.rebounds
    assert avg.assists == expected.assists
    assert avg.steals == expected.steals
    assert avg.blocks == expected.blocks
    assert avg.turnovers == expected.turnovers
    assert avg.fg_pct == expected.fg_pct
    assert avg.three_pct == expected.three_pct
    assert avg.ft_pct == expected.ft_pct


async def test_upsert_existing(
    session, test_team_playoff_season_average, test_season, test_home_team,
    test_away_team, test_playoff_game
):
    stat = TeamGameStat(
        game_id=test_playoff_game.id,
        team_id=test_home_team.id,
        season=test_season.season,
        points=115,
        opponent_points=108,
        rebounds=48,
        assists=28,
        steals=9,
        blocks=6,
        turnovers=10,
        fg_pct=0.480,
        three_pct=0.390,
        ft_pct=0.830,
        game_type="playoff",
    )
    session.add(stat)
    await session.flush()

    stale_points = test_team_playoff_season_average.points

    result = await compute_team_playoff_averages(test_season.season, session)

    assert result == 1

    rows = (await session.execute(select(TeamPlayoffSeasonAverage))).scalars().all()
    assert len(rows) == 1

    await session.refresh(test_team_playoff_season_average)
    avg = rows[0]
    expected = await _expected_team_averages(session, test_season.season, test_home_team.id)

    assert avg.games_played == expected.games_played
    assert avg.points == expected.points
    assert avg.points != stale_points


async def test_excludes_regular_games(
    session, test_season, test_home_team, test_away_team, test_game, test_playoff_game
):
    regular_stat = TeamGameStat(
        game_id=test_game.id,
        team_id=test_home_team.id,
        season=test_season.season,
        points=110,
        opponent_points=102,
        rebounds=45,
        assists=25,
        steals=8,
        blocks=5,
        turnovers=12,
        fg_pct=0.465,
        three_pct=0.380,
        ft_pct=0.810,
        game_type="regular",
    )
    playoff_stat = TeamGameStat(
        game_id=test_playoff_game.id,
        team_id=test_home_team.id,
        season=test_season.season,
        points=120,
        opponent_points=95,
        rebounds=50,
        assists=30,
        steals=10,
        blocks=7,
        turnovers=9,
        fg_pct=0.500,
        three_pct=0.410,
        ft_pct=0.860,
        game_type="playoff",
    )
    session.add_all([regular_stat, playoff_stat])
    await session.flush()

    result = await compute_team_playoff_averages(test_season.season, session)

    assert result == 1

    rows = (await session.execute(select(TeamPlayoffSeasonAverage))).scalars().all()
    assert len(rows) == 1

    avg = rows[0]
    assert avg.games_played == 1
    assert avg.points == 120


async def test_season_filtering(
    session, test_season, test_second_season, test_home_team, test_away_team, test_playoff_game
):
    other_playoff_game = Game(
        id="0042200001",
        home_team_id=test_home_team.id,
        away_team_id=test_away_team.id,
        game_date=date(2022, 4, 20),
        tipoff_at=datetime(2022, 4, 20, 20, 0),
        season="2023-24",
        status=3,
        game_type="playoff",
    )
    session.add(other_playoff_game)
    await session.flush()

    current_stat = TeamGameStat(
        game_id=test_playoff_game.id,
        team_id=test_home_team.id,
        season=test_season.season,
        points=115,
        opponent_points=108,
        rebounds=48,
        assists=28,
        steals=9,
        blocks=6,
        turnovers=10,
        fg_pct=0.480,
        three_pct=0.390,
        ft_pct=0.830,
        game_type="playoff",
    )
    other_stat = TeamGameStat(
        game_id=other_playoff_game.id,
        team_id=test_home_team.id,
        season="2023-24",
        points=130,
        opponent_points=90,
        rebounds=55,
        assists=35,
        steals=12,
        blocks=8,
        turnovers=8,
        fg_pct=0.550,
        three_pct=0.450,
        ft_pct=0.900,
        game_type="playoff",
    )
    session.add_all([current_stat, other_stat])
    await session.flush()

    result = await compute_team_playoff_averages(test_season.season, session)

    assert result == 1

    rows = (await session.execute(select(TeamPlayoffSeasonAverage))).scalars().all()
    assert len(rows) == 1

    avg = rows[0]
    assert avg.season == test_season.season
    assert avg.games_played == 1
    assert avg.points == 115


async def test_empty_season(session, test_season):
    result = await compute_team_playoff_averages("2024-25", session)

    assert result == 0

    rows = (await session.execute(select(TeamPlayoffSeasonAverage))).scalars().all()
    assert len(rows) == 0
