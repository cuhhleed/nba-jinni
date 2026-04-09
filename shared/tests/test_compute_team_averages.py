from sqlalchemy import select, func

from nbajinni_shared.utils import compute_team_averages
from nbajinni_shared.models.team_season_averages import TeamSeasonAverage
from nbajinni_shared.models.team_game_stats import TeamGameStat
from nbajinni_shared.models.games import Game
from datetime import date

async def _expected_team_averages(session, season, team_id):
    """Query the expected averages directly using func.avg rounded to match
    the Numeric precision of TeamSeasonAverage (1dp for stats, 3dp for percentages)."""
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
        .where(TeamGameStat.season == season, TeamGameStat.team_id == team_id)
    )
    return result.one()


async def test_first_time_insert(
    session, test_home_team_game_stat, test_home_team_second_game_stat
):
    result = await compute_team_averages("2024-25", session)

    assert result == 1

    rows = (await session.execute(select(TeamSeasonAverage))).scalars().all()
    assert len(rows) == 1

    avg = rows[0]
    expected = await _expected_team_averages(session, "2024-25", test_home_team_game_stat.team_id)

    assert avg.team_id == test_home_team_game_stat.team_id
    assert avg.season == "2024-25"
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
    session, test_team_season_average, test_home_team_game_stat, test_home_team_second_game_stat
):
    stale_points = test_team_season_average.points

    result = await compute_team_averages("2024-25", session)

    assert result == 1

    rows = (await session.execute(select(TeamSeasonAverage))).scalars().all()
    assert len(rows) == 1

    await session.refresh(test_team_season_average)
    avg = rows[0]
    expected = await _expected_team_averages(session, "2024-25", test_home_team_game_stat.team_id)

    assert avg.games_played == expected.games_played
    assert avg.points == expected.points
    assert avg.points != stale_points


async def test_excludes_other_season(
    session, test_season, test_second_season, test_home_team, test_away_team,
    test_home_team_game_stat, test_home_team_second_game_stat
):
    other_game = Game(
        id="0022200001",
        home_team_id=test_home_team.id,
        away_team_id=test_away_team.id,
        game_date=date(2023, 10, 1),
        season="2023-24",
        status=3,
    )
    session.add(other_game)
    await session.flush()

    other_stat = TeamGameStat(
        game_id=other_game.id,
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
    )
    session.add(other_stat)
    await session.flush()

    result = await compute_team_averages("2024-25", session)

    assert result == 1

    rows = (await session.execute(select(TeamSeasonAverage))).scalars().all()
    assert len(rows) == 1

    avg = rows[0]
    expected = await _expected_team_averages(session, "2024-25", test_home_team.id)

    assert avg.season == "2024-25"
    assert avg.games_played == expected.games_played
    assert avg.points == expected.points


async def test_empty_season(session, test_season):
    result = await compute_team_averages("2024-25", session)

    assert result == 0

    rows = (await session.execute(select(TeamSeasonAverage))).scalars().all()
    assert len(rows) == 0


async def test_multiple_teams(
    session, test_home_team_game_stat, test_home_team_second_game_stat,
    test_away_team_game_stat
):
    result = await compute_team_averages("2024-25", session)

    assert result == 2

    rows = (await session.execute(
        select(TeamSeasonAverage).order_by(TeamSeasonAverage.team_id)
    )).scalars().all()
    assert len(rows) == 2

    away_expected = await _expected_team_averages(session, "2024-25", test_away_team_game_stat.team_id)
    home_expected = await _expected_team_averages(session, "2024-25", test_home_team_game_stat.team_id)

    away_avg = next(r for r in rows if r.team_id == test_away_team_game_stat.team_id)
    assert away_avg.games_played == away_expected.games_played
    assert away_avg.points == away_expected.points

    home_avg = next(r for r in rows if r.team_id == test_home_team_game_stat.team_id)
    assert home_avg.games_played == home_expected.games_played
    assert home_avg.points == home_expected.points
