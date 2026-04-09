import pandas as pd
from datetime import date
from unittest.mock import patch
from sqlalchemy import select

from nbajinni_shared.utils import ingest_schedule
from nbajinni_shared.models.games import Game


def make_schedule_df(rows):
    return pd.DataFrame([
        {
            "gameId": r["game_id"],
            "homeTeam_teamId": r["home_team_id"],
            "awayTeam_teamId": r["away_team_id"],
            "gameDate": r["game_date"],
            "gameStatus": r["game_status"],
            "gameLabel": r["game_label"],
        }
        for r in rows
    ])


async def test_ingest_schedule_inserts_new_games(session, test_season, test_home_team, test_away_team):
    mock_df = make_schedule_df([
        {
            "game_id": "0022400001",
            "home_team_id": test_home_team.id,
            "away_team_id": test_away_team.id,
            "game_date": "10/22/2024 12:00:00",
            "game_status": 3,
            "game_label": "",
        },
        {
            "game_id": "0022400002",
            "home_team_id": test_away_team.id,
            "away_team_id": test_home_team.id,
            "game_date": "10/25/2024 12:00:00",
            "game_status": 1,
            "game_label": "",
        },
    ])

    with patch("nbajinni_shared.utils.wrapper.call", return_value=[mock_df]):
        processed = await ingest_schedule(session, test_season.season)

    assert processed == 2

    rows = (await session.execute(select(Game))).scalars().all()
    assert len(rows) == 2

    game1 = next(g for g in rows if g.id == "0022400001")
    assert game1.home_team_id == test_home_team.id
    assert game1.away_team_id == test_away_team.id
    assert game1.game_date == date(2024, 10, 22)
    assert game1.status == 3

    game2 = next(g for g in rows if g.id == "0022400002")
    assert game2.home_team_id == test_away_team.id
    assert game2.away_team_id == test_home_team.id
    assert game2.game_date == date(2024, 10, 25)
    assert game2.status == 1


async def test_ingest_schedule_upserts_existing_game(session, test_season, test_home_team, test_away_team, test_game):
    mock_df = make_schedule_df([
        {
            "game_id": test_game.id,
            "home_team_id": test_game.home_team_id,
            "away_team_id": test_game.away_team_id,
            "game_date": "11/01/2024 12:00:00",
            "game_status": test_game.status,
            "game_label": "",
        },
    ])

    with patch("nbajinni_shared.utils.wrapper.call", return_value=[mock_df]):
        processed = await ingest_schedule(session, test_season.season)

    assert processed == 1

    await session.refresh(test_game)
    assert test_game.game_date == date(2024, 11, 1)


async def test_ingest_schedule_skips_labeled_games(session, test_season, test_home_team, test_away_team):
    mock_df = make_schedule_df([
        {
            "game_id": "0022400001",
            "home_team_id": test_home_team.id,
            "away_team_id": test_away_team.id,
            "game_date": "10/22/2024 12:00:00",
            "game_status": 3,
            "game_label": "",
        },
        {
            "game_id": "0022400002",
            "home_team_id": test_home_team.id,
            "away_team_id": test_away_team.id,
            "game_date": "02/16/2025 12:00:00",
            "game_status": 1,
            "game_label": "All-Star",
        },
    ])

    with patch("nbajinni_shared.utils.wrapper.call", return_value=[mock_df]):
        processed = await ingest_schedule(session, test_season.season)

    assert processed == 1

    rows = (await session.execute(select(Game))).scalars().all()
    assert len(rows) == 1
    assert rows[0].id == "0022400001"
