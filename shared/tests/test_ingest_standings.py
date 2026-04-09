import pandas as pd
from unittest.mock import patch
from sqlalchemy import select

from nbajinni_shared.utils import ingest_standings
from nbajinni_shared.models.standings import Standing


def make_standings_df(rows):
    return pd.DataFrame([
        {
            "TeamID": r["team_id"],
            "Conference": r["conference"],
            "PlayoffRank": r["rank"],
            "WINS": r["wins"],
            "LOSSES": r["losses"],
            "WinPCT": r["win_pct"],
            "ConferenceGamesBack": r["gb"],
            "HOME": r["home"],
            "ROAD": r["road"],
            "L10": r["l10"],
            "CurrentStreak": r["streak"],
            "PointsPG": r["ppg"],
            "OppPointsPG": r["opp_ppg"],
        }
        for r in rows
    ])


async def test_ingest_standings_inserts_rows(session, test_standing, test_away_standing):
    mock_df = make_standings_df([
        {
            "team_id": test_standing.team_id,
            "conference": test_standing.conference,
            "rank": test_standing.conference_rank,
            "wins": test_standing.wins,
            "losses": test_standing.losses,
            "win_pct": float(test_standing.win_pct),
            "gb": float(test_standing.games_behind),
            "home": f"{test_standing.wins_home}-{test_standing.losses_home}",
            "road": f"{test_standing.wins_away}-{test_standing.losses_away}",
            "l10": f"{test_standing.win_L10}-{test_standing.loss_L10}",
            "streak": test_standing.streak,
            "ppg": float(test_standing.points_pg),
            "opp_ppg": float(test_standing.opp_points_pg),
        },
        {
            "team_id": test_away_standing.team_id,
            "conference": test_away_standing.conference,
            "rank": test_away_standing.conference_rank,
            "wins": test_away_standing.wins,
            "losses": test_away_standing.losses,
            "win_pct": float(test_away_standing.win_pct),
            "gb": float(test_away_standing.games_behind),
            "home": f"{test_away_standing.wins_home}-{test_away_standing.losses_home}",
            "road": f"{test_away_standing.wins_away}-{test_away_standing.losses_away}",
            "l10": f"{test_away_standing.win_L10}-{test_away_standing.loss_L10}",
            "streak": test_away_standing.streak,
            "ppg": float(test_away_standing.points_pg),
            "opp_ppg": float(test_away_standing.opp_points_pg),
        },
    ])

    with patch("nbajinni_shared.utils.wrapper.call", return_value=[mock_df]):
        processed = await ingest_standings(session, test_standing.season)

    assert processed == 2

    rows = (await session.execute(
        select(Standing).where(Standing.season == test_standing.season)
    )).scalars().all()
    assert len(rows) == 2

    await session.refresh(test_standing)
    home = next(s for s in rows if s.team_id == test_standing.team_id)
    assert home.conference == test_standing.conference
    assert home.conference_rank == test_standing.conference_rank
    assert home.wins == test_standing.wins
    assert home.wins_home == test_standing.wins_home
    assert home.wins_away == test_standing.wins_away
    assert home.losses == test_standing.losses
    assert home.losses_home == test_standing.losses_home
    assert home.losses_away == test_standing.losses_away
    assert home.win_L10 == test_standing.win_L10
    assert home.loss_L10 == test_standing.loss_L10
    assert home.streak == test_standing.streak


async def test_ingest_standings_upserts_existing_row(session, test_standing):
    mock_df = make_standings_df([
        {
            "team_id": test_standing.team_id,
            "conference": test_standing.conference,
            "rank": test_standing.conference_rank,
            "wins": 41,
            "losses": test_standing.losses,
            "win_pct": float(test_standing.win_pct),
            "gb": float(test_standing.games_behind),
            "home": "23-4",
            "road": f"{test_standing.wins_away}-{test_standing.losses_away}",
            "l10": "9-1",
            "streak": 6,
            "ppg": float(test_standing.points_pg),
            "opp_ppg": float(test_standing.opp_points_pg),
        },
    ])

    with patch("nbajinni_shared.utils.wrapper.call", return_value=[mock_df]):
        processed = await ingest_standings(session, test_standing.season)

    assert processed == 1

    rows = (await session.execute(
        select(Standing).where(Standing.season == test_standing.season)
    )).scalars().all()
    assert len(rows) == 1

    await session.refresh(test_standing)
    home = next(s for s in rows if s.team_id == test_standing.team_id)

    assert home.wins == 41
    assert home.wins_home == 23
    assert home.win_L10 == 9
    assert home.loss_L10 == 1
    assert home.streak == 6
