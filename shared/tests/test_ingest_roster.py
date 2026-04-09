import pandas as pd
from unittest.mock import patch
from sqlalchemy import select

from nbajinni_shared.utils import ingest_roster
from nbajinni_shared.models.players import Player


def make_roster_df(rows):
    return pd.DataFrame([
        {
            "PERSON_ID": r["person_id"],
            "DISPLAY_FIRST_LAST": r["display_name"],
            "TEAM_ID": r["team_id"],
        }
        for r in rows
    ])


async def test_ingest_roster_inserts_new_players(session, test_season, test_home_team, test_away_team):
    mock_df = make_roster_df([
        {"person_id": 9001, "display_name": "Anthony Davis", "team_id": test_home_team.id},
        {"person_id": 9002, "display_name": "Jayson Tatum", "team_id": test_away_team.id},
    ])

    with patch("nbajinni_shared.utils.wrapper.call", return_value=[mock_df]):
        processed = await ingest_roster(session, test_season.season)

    assert processed == 2

    rows = (await session.execute(select(Player))).scalars().all()
    assert len(rows) == 2

    davis = next(p for p in rows if p.id == 9001)
    assert davis.first_name == "Anthony"
    assert davis.last_name == "Davis"
    assert davis.team_id == test_home_team.id
    assert davis.active is True

    tatum = next(p for p in rows if p.id == 9002)
    assert tatum.first_name == "Jayson"
    assert tatum.last_name == "Tatum"
    assert tatum.team_id == test_away_team.id
    assert tatum.active is True


async def test_ingest_roster_upserts_existing_player(session, test_season, test_home_team, test_away_team, test_player):
    mock_df = make_roster_df([
        {"person_id": test_player.id, "display_name": test_player.first_name + " " + test_player.last_name, "team_id": test_away_team.id},
    ])

    with patch("nbajinni_shared.utils.wrapper.call", return_value=[mock_df]):
        processed = await ingest_roster(session, test_season.season)

    assert processed == 1

    await session.refresh(test_player)
    assert test_player.team_id == test_away_team.id
    assert test_player.active is True


async def test_ingest_roster_deactivates_missing_players(session, test_season, test_home_team, test_player):
    mock_df = make_roster_df([
        {"person_id": 9001, "display_name": "Anthony Davis", "team_id": test_home_team.id},
    ])

    with patch("nbajinni_shared.utils.wrapper.call", return_value=[mock_df]):
        processed = await ingest_roster(session, test_season.season)

    assert processed == 1

    await session.refresh(test_player)
    assert test_player.active is False

    new_player = (await session.execute(
        select(Player).where(Player.id == 9001)
    )).scalar_one()
    assert new_player.active is True


async def test_ingest_roster_keeps_active_players_active(session, test_season, test_home_team, test_player):
    mock_df = make_roster_df([
        {"person_id": test_player.id, "display_name": test_player.first_name + " " + test_player.last_name, "team_id": test_player.team_id},
    ])

    with patch("nbajinni_shared.utils.wrapper.call", return_value=[mock_df]):
        processed = await ingest_roster(session, test_season.season)

    assert processed == 1

    await session.refresh(test_player)
    assert test_player.active is True


async def test_ingest_roster_skips_teamless_players(session, test_season, test_home_team):
    mock_df = make_roster_df([
        {"person_id": 9001, "display_name": "Anthony Davis", "team_id": test_home_team.id},
        {"person_id": 9002, "display_name": "Free Agent", "team_id": 0},
    ])

    with patch("nbajinni_shared.utils.wrapper.call", return_value=[mock_df]):
        processed = await ingest_roster(session, test_season.season)

    assert processed == 1

    rows = (await session.execute(select(Player))).scalars().all()
    assert len(rows) == 1
    assert rows[0].id == 9001


async def test_ingest_roster_handles_multi_word_last_name(session, test_season, test_home_team):
    mock_df = make_roster_df([
        {"person_id": 9001, "display_name": "Shai Gilgeous-Alexander", "team_id": test_home_team.id},
        {"person_id": 9002, "display_name": "Kentavious Caldwell-Pope Jr", "team_id": test_home_team.id},
    ])

    with patch("nbajinni_shared.utils.wrapper.call", return_value=[mock_df]):
        processed = await ingest_roster(session, test_season.season)

    assert processed == 2

    shai = (await session.execute(
        select(Player).where(Player.id == 9001)
    )).scalar_one()
    assert shai.first_name == "Shai"
    assert shai.last_name == "Gilgeous-Alexander"

    kcp = (await session.execute(
        select(Player).where(Player.id == 9002)
    )).scalar_one()
    assert kcp.first_name == "Kentavious"
    assert kcp.last_name == "Caldwell-Pope Jr"