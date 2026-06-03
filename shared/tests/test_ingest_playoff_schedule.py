import pandas as pd
from datetime import date
from unittest.mock import patch
from sqlalchemy import select

from nbajinni_shared.utils import ingest_playoff_schedule
from nbajinni_shared.models.games import Game
from nbajinni_shared.models.playoff_game_metadata import PlayoffGameMetadata


def make_playoff_schedule_df(rows):
    return pd.DataFrame([
        {
            "gameId": r["game_id"],
            "homeTeam_teamId": r["home_team_id"],
            "awayTeam_teamId": r["away_team_id"],
            "gameDateTimeUTC": r["game_datetime_utc"],
            "gameStatus": r["game_status"],
            "gameLabel": r["game_label"],
            "seriesGameNumber": r["series_game_number"],
            "seriesText": r["series_text"],
        }
        for r in rows
    ])


async def test_ingest_playoff_schedule_inserts_games_with_playoff_type(
    session, test_season, test_home_team, test_away_team
):
    mock_df = make_playoff_schedule_df([
        {
            "game_id": "0042400001",
            "home_team_id": test_home_team.id,
            "away_team_id": test_away_team.id,
            "game_datetime_utc": "2025-04-20T20:00:00Z",
            "game_status": 3,
            "game_label": "1st Round",
            "series_game_number": "Game 1",
            "series_text": "LAL leads 1-0",
        },
    ])

    with patch("nbajinni_shared.utils.wrapper.call", return_value=[mock_df]):
        processed = await ingest_playoff_schedule(session, test_season.season)

    assert processed == 1

    rows = (await session.execute(select(Game))).scalars().all()
    assert len(rows) == 1
    assert rows[0].id == "0042400001"
    assert rows[0].game_type == "playoff"
    assert rows[0].status == 1


async def test_ingest_playoff_schedule_inserts_metadata(
    session, test_season, test_home_team, test_away_team
):
    mock_df = make_playoff_schedule_df([
        {
            "game_id": "0042400002",
            "home_team_id": test_home_team.id,
            "away_team_id": test_away_team.id,
            "game_datetime_utc": "2025-05-05T20:00:00Z",
            "game_status": 3,
            "game_label": "Conf. Semifinals",
            "series_game_number": "Game 3",
            "series_text": "BOS leads 2-1",
        },
    ])

    with patch("nbajinni_shared.utils.wrapper.call", return_value=[mock_df]):
        await ingest_playoff_schedule(session, test_season.season)

    metadata_rows = (await session.execute(select(PlayoffGameMetadata))).scalars().all()
    assert len(metadata_rows) == 1

    meta = metadata_rows[0]
    assert meta.game_id == "0042400002"
    assert meta.round_label == "Conf. Semifinals"
    assert meta.series_game_number == 3
    assert meta.series_record == "BOS leads 2-1"


async def test_ingest_playoff_schedule_upserts_existing_metadata(
    session, test_season, test_home_team, test_away_team
):
    initial_df = make_playoff_schedule_df([
        {
            "game_id": "0042400003",
            "home_team_id": test_home_team.id,
            "away_team_id": test_away_team.id,
            "game_datetime_utc": "2025-05-15T20:00:00Z",
            "game_status": 3,
            "game_label": "Conf. Finals",
            "series_game_number": "Game 2",
            "series_text": "LAL leads 2-0",
        },
    ])
    updated_df = make_playoff_schedule_df([
        {
            "game_id": "0042400003",
            "home_team_id": test_home_team.id,
            "away_team_id": test_away_team.id,
            "game_datetime_utc": "2025-05-15T20:00:00Z",
            "game_status": 3,
            "game_label": "Conf. Finals",
            "series_game_number": "Game 2",
            "series_text": "BOS leads 2-1",
        },
    ])

    with patch("nbajinni_shared.utils.wrapper.call", return_value=[initial_df]):
        await ingest_playoff_schedule(session, test_season.season)

    with patch("nbajinni_shared.utils.wrapper.call", return_value=[updated_df]):
        await ingest_playoff_schedule(session, test_season.season)

    metadata_rows = (await session.execute(select(PlayoffGameMetadata))).scalars().all()
    assert len(metadata_rows) == 1
    assert metadata_rows[0].series_record == "BOS leads 2-1"


async def test_ingest_playoff_schedule_skips_tbd_placeholder_teams(
    session, test_season, test_home_team, test_away_team
):
    mock_df = make_playoff_schedule_df([
        {
            "game_id": "0042400401",
            "home_team_id": 0,
            "away_team_id": test_away_team.id,
            "game_datetime_utc": "2025-06-04T00:30:00Z",
            "game_status": 1,
            "game_label": "NBA Finals",
            "series_game_number": "Game 1",
            "series_text": "",
        },
        {
            "game_id": "0042400402",
            "home_team_id": test_home_team.id,
            "away_team_id": 0,
            "game_datetime_utc": "2025-06-07T00:30:00Z",
            "game_status": 1,
            "game_label": "NBA Finals",
            "series_game_number": "Game 2",
            "series_text": "",
        },
        {
            "game_id": "0042400099",
            "home_team_id": test_home_team.id,
            "away_team_id": test_away_team.id,
            "game_datetime_utc": "2025-04-20T20:00:00Z",
            "game_status": 3,
            "game_label": "1st Round",
            "series_game_number": "Game 1",
            "series_text": "LAL leads 1-0",
        },
    ])

    with patch("nbajinni_shared.utils.wrapper.call", return_value=[mock_df]):
        processed = await ingest_playoff_schedule(session, test_season.season)

    assert processed == 1
    rows = (await session.execute(select(Game))).scalars().all()
    assert len(rows) == 1
    assert rows[0].id == "0042400099"


async def test_ingest_playoff_schedule_skips_non_playoff_ids(
    session, test_season, test_home_team, test_away_team
):
    mock_df = make_playoff_schedule_df([
        {
            "game_id": "0022400010",
            "home_team_id": test_home_team.id,
            "away_team_id": test_away_team.id,
            "game_datetime_utc": "2025-01-10T20:00:00Z",
            "game_status": 3,
            "game_label": "",
            "series_game_number": 0,
            "series_text": "",
        },
        {
            "game_id": "0042400010",
            "home_team_id": test_home_team.id,
            "away_team_id": test_away_team.id,
            "game_datetime_utc": "2025-04-20T20:00:00Z",
            "game_status": 3,
            "game_label": "1st Round",
            "series_game_number": "Game 1",
            "series_text": "LAL leads 1-0",
        },
    ])

    with patch("nbajinni_shared.utils.wrapper.call", return_value=[mock_df]):
        processed = await ingest_playoff_schedule(session, test_season.season)

    assert processed == 1

    rows = (await session.execute(select(Game))).scalars().all()
    assert len(rows) == 1
    assert rows[0].id == "0042400010"


async def test_ingest_playoff_schedule_game_date_is_et_calendar_day(
    session, test_season, test_home_team, test_away_team
):
    """A 00:30 UTC tipoff on 2025-06-04 is still June 3 in Eastern Time."""
    mock_df = make_playoff_schedule_df([
        {
            "game_id": "0042400501",
            "home_team_id": test_home_team.id,
            "away_team_id": test_away_team.id,
            "game_datetime_utc": "2025-06-04T00:30:00Z",
            "game_status": 3,
            "game_label": "NBA Finals",
            "series_game_number": "Game 1",
            "series_text": "Series tied 0-0",
        },
    ])

    with patch("nbajinni_shared.utils.wrapper.call", return_value=[mock_df]):
        processed = await ingest_playoff_schedule(session, test_season.season)

    assert processed == 1

    rows = (await session.execute(select(Game))).scalars().all()
    assert len(rows) == 1
    assert rows[0].game_date == date(2025, 6, 3)
