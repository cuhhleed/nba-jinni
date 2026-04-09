import pandas as pd
from unittest.mock import patch, AsyncMock
from sqlalchemy import select

from nbajinni_shared.utils import ingest_games
from nbajinni_shared.models.player_game_stats import PlayerGameStat
from nbajinni_shared.models.team_game_stats import TeamGameStat


def make_player_stats_df(rows):
    return pd.DataFrame([
        {
            "personId": r["person_id"],
            "teamId": r["team_id"],
            "position": r["position"],
            "minutes": r["minutes"],
            "points": r["points"],
            "fieldGoalsMade": r["fgm"],
            "fieldGoalsAttempted": r["fga"],
            "fieldGoalsPercentage": r["fgp"],
            "freeThrowsMade": r["ftm"],
            "freeThrowsAttempted": r["fta"],
            "freeThrowsPercentage": r["ftp"],
            "threePointersMade": r["tpm"],
            "threePointersAttempted": r["tpa"],
            "threePointersPercentage": r["tpp"],
            "reboundsOffensive": r["off_reb"],
            "reboundsDefensive": r["def_reb"],
            "reboundsTotal": r["tot_reb"],
            "assists": r["assists"],
            "steals": r["steals"],
            "blocks": r["blocks"],
            "turnovers": r["turnovers"],
            "foulsPersonal": r["fouls"],
            "plusMinusPoints": r["plus_minus"],
        }
        for r in rows
    ])


def make_team_stats_df(rows):
    return pd.DataFrame([
        {
            "gameId": r["game_id"],
            "teamId": r["team_id"],
            "points": r["points"],
            "reboundsTotal": r["rebounds"],
            "assists": r["assists"],
            "steals": r["steals"],
            "blocks": r["blocks"],
            "turnovers": r["turnovers"],
            "fieldGoalsPercentage": r["fg_pct"],
            "threePointersPercentage": r["three_pct"],
            "freeThrowsPercentage": r["ft_pct"],
        }
        for r in rows
    ])


async def test_ingest_games_inserts_stats(session, test_season, test_home_team, test_away_team, test_player, test_game):
    player_df = make_player_stats_df([{
        "person_id": test_player.id, "team_id": test_player.team_id,
        "position": "F", "minutes": "30:00", "points": 20,
        "fgm": 8, "fga": 15, "fgp": 0.53,
        "ftm": 3, "fta": 4, "ftp": 0.75,
        "tpm": 1, "tpa": 3, "tpp": 0.333,
        "off_reb": 2, "def_reb": 5, "tot_reb": 7,
        "assists": 5, "steals": 1, "blocks": 1,
        "turnovers": 3, "fouls": 2, "plus_minus": 10,
    }])
    team_df = make_team_stats_df([
        {
            "game_id": test_game.id, "team_id": test_home_team.id,
            "points": 110, "rebounds": 42, "assists": 25,
            "steals": 8, "blocks": 5, "turnovers": 12,
            "fg_pct": 0.470, "three_pct": 0.380, "ft_pct": 0.820,
        },
        {
            "game_id": test_game.id, "team_id": test_away_team.id,
            "points": 105, "rebounds": 38, "assists": 22,
            "steals": 6, "blocks": 3, "turnovers": 14,
            "fg_pct": 0.440, "three_pct": 0.340, "ft_pct": 0.780,
        },
    ])

    with patch("nbajinni_shared.utils.get_game_stats", new_callable=AsyncMock, return_value=(player_df, team_df)):
        result = await ingest_games([test_game], session)

    assert result == (1, 1, 2)

    player_stats = (await session.execute(select(PlayerGameStat))).scalars().all()
    assert len(player_stats) == 1
    assert player_stats[0].player_id == test_player.id
    assert player_stats[0].game_id == test_game.id
    assert player_stats[0].points == 20
    assert player_stats[0].min == 30

    team_stats = (await session.execute(select(TeamGameStat))).scalars().all()
    assert len(team_stats) == 2

    await session.refresh(test_game)
    assert test_game.status == 3


async def test_ingest_games_multiple_games(session, test_season, test_home_team, test_away_team, test_player, test_game, test_second_game):
    player_df_1 = make_player_stats_df([{
        "person_id": test_player.id, "team_id": test_player.team_id,
        "position": "F", "minutes": "28:00", "points": 18,
        "fgm": 7, "fga": 14, "fgp": 0.50,
        "ftm": 2, "fta": 3, "ftp": 0.67,
        "tpm": 2, "tpa": 5, "tpp": 0.400,
        "off_reb": 1, "def_reb": 4, "tot_reb": 5,
        "assists": 6, "steals": 2, "blocks": 0,
        "turnovers": 2, "fouls": 3, "plus_minus": 5,
    }])
    team_df_1 = make_team_stats_df([
        {
            "game_id": test_game.id, "team_id": test_home_team.id,
            "points": 108, "rebounds": 40, "assists": 24,
            "steals": 7, "blocks": 4, "turnovers": 11,
            "fg_pct": 0.460, "three_pct": 0.370, "ft_pct": 0.810,
        },
        {
            "game_id": test_game.id, "team_id": test_away_team.id,
            "points": 102, "rebounds": 36, "assists": 20,
            "steals": 5, "blocks": 2, "turnovers": 15,
            "fg_pct": 0.430, "three_pct": 0.320, "ft_pct": 0.770,
        },
    ])

    player_df_2 = make_player_stats_df([{
        "person_id": test_player.id, "team_id": test_player.team_id,
        "position": "F", "minutes": "32:00", "points": 25,
        "fgm": 10, "fga": 18, "fgp": 0.56,
        "ftm": 4, "fta": 5, "ftp": 0.80,
        "tpm": 1, "tpa": 4, "tpp": 0.250,
        "off_reb": 3, "def_reb": 6, "tot_reb": 9,
        "assists": 4, "steals": 1, "blocks": 2,
        "turnovers": 4, "fouls": 1, "plus_minus": 15,
    }])
    team_df_2 = make_team_stats_df([
        {
            "game_id": test_second_game.id, "team_id": test_home_team.id,
            "points": 115, "rebounds": 44, "assists": 28,
            "steals": 9, "blocks": 6, "turnovers": 10,
            "fg_pct": 0.490, "three_pct": 0.400, "ft_pct": 0.850,
        },
        {
            "game_id": test_second_game.id, "team_id": test_away_team.id,
            "points": 99, "rebounds": 35, "assists": 19,
            "steals": 4, "blocks": 1, "turnovers": 16,
            "fg_pct": 0.410, "three_pct": 0.300, "ft_pct": 0.750,
        },
    ])

    with patch("nbajinni_shared.utils.get_game_stats", new_callable=AsyncMock, side_effect=[
        (player_df_1, team_df_1),
        (player_df_2, team_df_2),
    ]):
        result = await ingest_games([test_game, test_second_game], session)

    assert result == (2, 2, 4)

    await session.refresh(test_game)
    await session.refresh(test_second_game)
    assert test_game.status == 3
    assert test_second_game.status == 3


async def test_ingest_games_skips_when_api_returns_none(session, test_season, test_home_team, test_away_team, test_game):
    with patch("nbajinni_shared.utils.get_game_stats", new_callable=AsyncMock, return_value=(None, None)):
        result = await ingest_games([test_game], session)

    assert result == (0, 0, 0)

    await session.refresh(test_game)
    assert test_game.status == 1

    player_stats = (await session.execute(select(PlayerGameStat))).scalars().all()
    assert len(player_stats) == 0

    team_stats = (await session.execute(select(TeamGameStat))).scalars().all()
    assert len(team_stats) == 0


async def test_ingest_games_skips_unknown_player(session, test_season, test_home_team, test_away_team, test_player, test_game):
    player_df = make_player_stats_df([
        {
            "person_id": test_player.id, "team_id": test_player.team_id,
            "position": "F", "minutes": "30:00", "points": 20,
            "fgm": 8, "fga": 15, "fgp": 0.53,
            "ftm": 3, "fta": 4, "ftp": 0.75,
            "tpm": 1, "tpa": 3, "tpp": 0.333,
            "off_reb": 2, "def_reb": 5, "tot_reb": 7,
            "assists": 5, "steals": 1, "blocks": 1,
            "turnovers": 3, "fouls": 2, "plus_minus": 10,
        },
        {
            "person_id": 99999, "team_id": test_home_team.id,
            "position": "G", "minutes": "25:00", "points": 15,
            "fgm": 6, "fga": 12, "fgp": 0.50,
            "ftm": 2, "fta": 2, "ftp": 1.00,
            "tpm": 1, "tpa": 4, "tpp": 0.250,
            "off_reb": 0, "def_reb": 3, "tot_reb": 3,
            "assists": 8, "steals": 2, "blocks": 0,
            "turnovers": 4, "fouls": 3, "plus_minus": -2,
        },
    ])
    team_df = make_team_stats_df([
        {
            "game_id": test_game.id, "team_id": test_home_team.id,
            "points": 110, "rebounds": 42, "assists": 25,
            "steals": 8, "blocks": 5, "turnovers": 12,
            "fg_pct": 0.470, "three_pct": 0.380, "ft_pct": 0.820,
        },
        {
            "game_id": test_game.id, "team_id": test_away_team.id,
            "points": 105, "rebounds": 38, "assists": 22,
            "steals": 6, "blocks": 3, "turnovers": 14,
            "fg_pct": 0.440, "three_pct": 0.340, "ft_pct": 0.780,
        },
    ])

    with patch("nbajinni_shared.utils.get_game_stats", new_callable=AsyncMock, return_value=(player_df, team_df)):
        result = await ingest_games([test_game], session)

    assert result[1] == 1

    player_stats = (await session.execute(select(PlayerGameStat))).scalars().all()
    assert len(player_stats) == 1
    assert player_stats[0].player_id == test_player.id


async def test_ingest_games_handles_empty_minutes(session, test_season, test_home_team, test_away_team, test_player, test_game):
    player_df = make_player_stats_df([{
        "person_id": test_player.id, "team_id": test_player.team_id,
        "position": "F", "minutes": "", "points": 0,
        "fgm": 0, "fga": 1, "fgp": 0.00,
        "ftm": 0, "fta": 0, "ftp": 0.00,
        "tpm": 0, "tpa": 1, "tpp": 0.000,
        "off_reb": 0, "def_reb": 0, "tot_reb": 0,
        "assists": 0, "steals": 0, "blocks": 0,
        "turnovers": 0, "fouls": 1, "plus_minus": -3,
    }])
    team_df = make_team_stats_df([
        {
            "game_id": test_game.id, "team_id": test_home_team.id,
            "points": 95, "rebounds": 38, "assists": 20,
            "steals": 5, "blocks": 3, "turnovers": 15,
            "fg_pct": 0.400, "three_pct": 0.300, "ft_pct": 0.700,
        },
        {
            "game_id": test_game.id, "team_id": test_away_team.id,
            "points": 100, "rebounds": 42, "assists": 24,
            "steals": 7, "blocks": 4, "turnovers": 11,
            "fg_pct": 0.450, "three_pct": 0.350, "ft_pct": 0.800,
        },
    ])

    with patch("nbajinni_shared.utils.get_game_stats", new_callable=AsyncMock, return_value=(player_df, team_df)):
        await ingest_games([test_game], session)

    player_stat = (await session.execute(select(PlayerGameStat))).scalar_one()
    assert player_stat.min == 0


async def test_ingest_games_opponent_points_cross_reference(session, test_season, test_home_team, test_away_team, test_player, test_game):
    player_df = make_player_stats_df([{
        "person_id": test_player.id, "team_id": test_player.team_id,
        "position": "F", "minutes": "30:00", "points": 20,
        "fgm": 8, "fga": 15, "fgp": 0.53,
        "ftm": 3, "fta": 4, "ftp": 0.75,
        "tpm": 1, "tpa": 3, "tpp": 0.333,
        "off_reb": 2, "def_reb": 5, "tot_reb": 7,
        "assists": 5, "steals": 1, "blocks": 1,
        "turnovers": 3, "fouls": 2, "plus_minus": 10,
    }])
    team_df = make_team_stats_df([
        {
            "game_id": test_game.id, "team_id": test_home_team.id,
            "points": 110, "rebounds": 42, "assists": 25,
            "steals": 8, "blocks": 5, "turnovers": 12,
            "fg_pct": 0.470, "three_pct": 0.380, "ft_pct": 0.820,
        },
        {
            "game_id": test_game.id, "team_id": test_away_team.id,
            "points": 105, "rebounds": 38, "assists": 22,
            "steals": 6, "blocks": 3, "turnovers": 14,
            "fg_pct": 0.440, "three_pct": 0.340, "ft_pct": 0.780,
        },
    ])

    with patch("nbajinni_shared.utils.get_game_stats", new_callable=AsyncMock, return_value=(player_df, team_df)):
        await ingest_games([test_game], session)

    team_stats = (await session.execute(select(TeamGameStat))).scalars().all()

    home_stat = next(s for s in team_stats if s.team_id == test_home_team.id)
    assert home_stat.points == 110
    assert home_stat.opponent_points == 105

    away_stat = next(s for s in team_stats if s.team_id == test_away_team.id)
    assert away_stat.points == 105
    assert away_stat.opponent_points == 110
