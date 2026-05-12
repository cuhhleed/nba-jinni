"""
Happy-path tests for new player endpoints:
  GET /players/top/preview
  GET /players/{player_id}/season-averages
  GET /players/{player_id}/last-5-games
  GET /players/{player_id}/vs-opponent
  GET /players/top/recent-performances
"""
import pytest
import pytest_asyncio
from datetime import date, datetime

from nbajinni_shared.models.players import Player
from nbajinni_shared.models.games import Game
from nbajinni_shared.models.player_game_stats import PlayerGameStat


# ---------------------------------------------------------------------------
# Fixtures for recent-performances tests
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def rp_player_a(session, test_home_team):
    """Player A — on home team."""
    p = Player(id=9001, first_name="Alpha", last_name="One", team_id=test_home_team.id)
    session.add(p)
    await session.flush()
    return p


@pytest_asyncio.fixture
async def rp_player_b(session, test_away_team):
    """Player B — on away team."""
    p = Player(id=9002, first_name="Beta", last_name="Two", team_id=test_away_team.id)
    session.add(p)
    await session.flush()
    return p


@pytest_asyncio.fixture
async def rp_player_c(session, test_home_team):
    """Player C — on home team."""
    p = Player(id=9003, first_name="Gamma", last_name="Three", team_id=test_home_team.id)
    session.add(p)
    await session.flush()
    return p


@pytest_asyncio.fixture
async def rp_player_d(session, test_away_team):
    """Player D — on away team."""
    p = Player(id=9004, first_name="Delta", last_name="Four", team_id=test_away_team.id)
    session.add(p)
    await session.flush()
    return p


@pytest_asyncio.fixture
async def rp_game_recent(session, test_season, test_home_team, test_away_team):
    """Game on the most-recent game-day (2025-01-10)."""
    g = Game(
        id="RP0001",
        home_team_id=test_home_team.id,
        away_team_id=test_away_team.id,
        game_date=date(2025, 1, 10),
        tipoff_at=datetime(2025, 1, 10, 20, 0),
        season=test_season.season,
        status=3,
    )
    session.add(g)
    await session.flush()
    return g


@pytest_asyncio.fixture
async def rp_game_prior(session, test_season, test_home_team, test_away_team):
    """Game on the prior game-day (2025-01-09)."""
    g = Game(
        id="RP0002",
        home_team_id=test_home_team.id,
        away_team_id=test_away_team.id,
        game_date=date(2025, 1, 9),
        tipoff_at=datetime(2025, 1, 9, 20, 0),
        season=test_season.season,
        status=3,
    )
    session.add(g)
    await session.flush()
    return g


def _make_stat(session, player, game, season, **kwargs):
    defaults = dict(
        pos="SF", min=36,
        fgm=10, fga=20, ftm=5, fta=7, tpm=2, tpa=5,
        off_reb=2, def_reb=8, tos=3, pfs=2,
        fgp=50.0, ftp=71.4, tpp=40.0, plus_minus=0,
        points=0, tot_reb=0, asts=0, stls=0, blks=0,
    )
    defaults.update(kwargs)
    stat = PlayerGameStat(
        game_id=game.id,
        player_id=player.id,
        season=season,
        team_id=player.team_id,
        **defaults,
    )
    session.add(stat)
    return stat


@pytest.mark.asyncio
async def test_get_player_season_averages(
    client, test_player, test_player_season_average
):
    response = await client.get(f"/players/{test_player.id}/season-average")
    assert response.status_code == 200
    data = response.json()
    assert data["player_id"] == test_player.id
    assert data["season"] == test_player_season_average.season


@pytest.mark.asyncio
async def test_get_player_season_averages_not_found(client):
    response = await client.get("/players/9999999/season-average")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_player_last_5_games(
    client, test_player, test_player_game_stat, test_game
):
    response = await client.get(f"/players/{test_player.id}/last-5-games")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["player_id"] == test_player.id
    assert data[0]["game_date"] == str(test_game.game_date)
    # Player is on home team → opponent is away team
    assert data[0]["opponent_team_id"] == test_game.away_team_id


@pytest.mark.asyncio
async def test_get_player_last_5_games_not_found(client):
    response = await client.get("/players/9999999/last-5-games")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_player_vs_opponent(
    client,
    test_player,
    test_player_game_stat,
    test_game,
    test_away_team,
    test_home_standing,
):
    response = await client.get(
        f"/players/{test_player.id}/vs-opponent?team_id={test_away_team.id}"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["player_id"] == test_player.id


@pytest.mark.asyncio
async def test_get_player_vs_opponent_not_found(client, test_home_standing):
    response = await client.get("/players/9999999/vs-opponent?team_id=1")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_top_players_preview(
    client, test_player_season_average, test_player, test_home_standing
):
    """Top players preview returns all 5 stat categories."""
    response = await client.get("/players/top/preview")
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"points", "rebounds", "assists", "steals", "blocks"}
    # Our fixture has games_played=15 so floor applies; player should appear in all categories
    assert len(data["points"]) == 1
    assert data["points"][0]["player_id"] == test_player.id


# ---------------------------------------------------------------------------
# GET /players/top/recent-performances
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_recent_performances_happy_path(
    client, session, test_season,
    rp_player_a, rp_player_b, rp_player_c, rp_player_d,
    rp_game_recent, rp_game_prior,
):
    """4 qualifying performances across 2 game-days → returns exactly 3, ordered correctly.

    Player A (recent, base=38): ranked 1st (38+5=43).
    Player B (recent, base=36): ranked 2nd (36+5=41).
    Player C (prior, base=40): ranked 3rd (40+0=40).
    Player D (prior, base=37): 4th — excluded from top 3.
    """
    _make_stat(session, rp_player_a, rp_game_recent, test_season.season,
               points=20, tot_reb=10, asts=5, stls=2, blks=1)  # base=38
    _make_stat(session, rp_player_b, rp_game_recent, test_season.season,
               points=18, tot_reb=10, asts=5, stls=2, blks=1)  # base=36
    _make_stat(session, rp_player_c, rp_game_prior, test_season.season,
               points=22, tot_reb=10, asts=5, stls=2, blks=1)  # base=40
    _make_stat(session, rp_player_d, rp_game_prior, test_season.season,
               points=20, tot_reb=10, asts=4, stls=2, blks=1)  # base=37
    await session.flush()

    response = await client.get("/players/top/recent-performances")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["player_id"] == rp_player_a.id   # 43
    assert data[1]["player_id"] == rp_player_b.id   # 41
    assert data[2]["player_id"] == rp_player_c.id   # 40


@pytest.mark.asyncio
async def test_recent_performances_threshold_filter(
    client, session, test_season,
    rp_player_a, rp_player_b,
    rp_game_recent,
):
    """34-pt line excluded; 35-pt line included."""
    _make_stat(session, rp_player_a, rp_game_recent, test_season.season,
               points=34, tot_reb=0, asts=0, stls=0, blks=0)  # base=34 → excluded
    _make_stat(session, rp_player_b, rp_game_recent, test_season.season,
               points=35, tot_reb=0, asts=0, stls=0, blks=0)  # base=35 → included
    await session.flush()

    response = await client.get("/players/top/recent-performances")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["player_id"] == rp_player_b.id


@pytest.mark.asyncio
async def test_recent_performances_bonus_tiebreaker(
    client, session, test_season,
    rp_player_a, rp_player_b,
    rp_game_recent, rp_game_prior,
):
    """base=40 from most-recent (score=45) outranks base=44 from prior day (score=44)."""
    _make_stat(session, rp_player_a, rp_game_recent, test_season.season,
               points=20, tot_reb=10, asts=5, stls=3, blks=2)  # base=40, score=45
    _make_stat(session, rp_player_b, rp_game_prior, test_season.season,
               points=22, tot_reb=12, asts=5, stls=3, blks=2)  # base=44, score=44
    await session.flush()

    response = await client.get("/players/top/recent-performances")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["player_id"] == rp_player_a.id
    assert data[1]["player_id"] == rp_player_b.id


@pytest.mark.asyncio
async def test_recent_performances_sparse_data(client):
    """No rows at all → returns empty list."""
    response = await client.get("/players/top/recent-performances")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_recent_performances_sparse_two_qualifying(
    client, session, test_season,
    rp_player_a, rp_player_b,
    rp_game_recent,
):
    """2 qualifying rows → returns 2 (not padded to 3)."""
    _make_stat(session, rp_player_a, rp_game_recent, test_season.season,
               points=20, tot_reb=8, asts=5, stls=1, blks=1)  # base=35
    _make_stat(session, rp_player_b, rp_game_recent, test_season.season,
               points=18, tot_reb=10, asts=5, stls=2, blks=2)  # base=37
    await session.flush()

    response = await client.get("/players/top/recent-performances")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_recent_performances_one_day_only(
    client, session, test_season,
    rp_player_a, rp_player_b, rp_player_c,
    rp_game_recent,
):
    """Only the most-recent day has games — bonus applied equally to all; top by base."""
    _make_stat(session, rp_player_a, rp_game_recent, test_season.season,
               points=22, tot_reb=10, asts=5, stls=2, blks=2)  # base=41
    _make_stat(session, rp_player_b, rp_game_recent, test_season.season,
               points=20, tot_reb=10, asts=5, stls=2, blks=1)  # base=38
    _make_stat(session, rp_player_c, rp_game_recent, test_season.season,
               points=18, tot_reb=10, asts=5, stls=1, blks=1)  # base=35
    await session.flush()

    response = await client.get("/players/top/recent-performances")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["player_id"] == rp_player_a.id
    assert data[1]["player_id"] == rp_player_b.id
    assert data[2]["player_id"] == rp_player_c.id
