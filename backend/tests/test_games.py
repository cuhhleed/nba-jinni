"""
Happy-path tests for game endpoints:
  GET /games/{game_id}          — discriminated union (preview / result)
  GET /games/{game_id}/playerstats
  GET /games/h2h
  GET /games/live/today         — bulk live scoreboard
  GET /games/live/{game_id}     — per-game live box score
"""
import time
import pytest
from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch


@pytest.mark.asyncio
async def test_get_game_result(
    client,
    test_game,
    test_home_team_game_stat,
    test_away_team_game_stat,
):
    """Completed game (status=3) with team stats → GameResult response."""
    response = await client.get(f"/games/{test_game.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "result"
    assert data["id"] == test_game.id
    assert data["home_team_stat"]["team_id"] == test_game.home_team_id
    assert data["away_team_stat"]["team_id"] == test_game.away_team_id


@pytest.mark.asyncio
async def test_get_game_result_missing_stats_returns_409(
    client, test_game
):
    """Completed game with no team_stats rows → 409."""
    response = await client.get(f"/games/{test_game.id}")
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_game_preview(
    client,
    test_upcoming_game,
    test_home_standing,
    test_away_standing,
    test_home_team_season_average,
    test_away_team_season_average,
):
    """Upcoming game (status=1) → GamePreview response with team context."""
    response = await client.get(f"/games/{test_upcoming_game.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "preview"
    assert data["id"] == test_upcoming_game.id
    assert "home_team" in data
    assert "away_team" in data


@pytest.mark.asyncio
async def test_get_game_not_found(client):
    response = await client.get("/games/NONEXISTENT")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_game_player_stats(
    client, test_game, test_player_game_stat
):
    response = await client.get(f"/games/{test_game.id}/playerstats")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["game_id"] == test_game.id
    assert data[0]["player_id"] == test_player_game_stat.player_id


@pytest.mark.asyncio
async def test_get_game_player_stats_not_found(client):
    response = await client.get("/games/NONEXISTENT/playerstats")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_h2h_games(
    client,
    test_game,
    test_home_team,
    test_away_team,
    test_home_team_game_stat,
    test_away_team_game_stat,
    test_home_standing,
):
    response = await client.get(
        f"/games/h2h?team_a={test_home_team.id}&team_b={test_away_team.id}"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == test_game.id


@pytest.mark.asyncio
async def test_get_h2h_empty_when_no_games(
    client, test_home_standing, test_away_standing, test_home_team, test_away_team
):
    """Teams with no h2h games this season → empty list, not 404."""
    response = await client.get(
        f"/games/h2h?team_a={test_home_team.id}&team_b={test_away_team.id}"
    )
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_h2h_symmetric(
    client,
    session,
    test_game,
    test_home_team,
    test_away_team,
    test_home_standing,
    test_home_team_game_stat,
    test_away_team_game_stat,
):
    """
    h2h is symmetric: both (team_a=LAL, team_b=BOS) and (team_a=BOS, team_b=LAL)
    return the same game. A second game with reversed home/away also appears in both
    orderings.
    """
    from datetime import date, datetime, timezone
    from nbajinni_shared.models.games import Game

    # Add a reversed fixture — BOS home, LAL away — in the same season
    reversed_game = Game(
        id="0022300002",
        home_team_id=test_away_team.id,
        away_team_id=test_home_team.id,
        game_date=date(2024, 11, 1),
        tipoff_at=datetime(2024, 11, 1, 19, 0),
        season=test_game.season,
        status=3,
    )
    session.add(reversed_game)
    await session.flush()

    # Original ordering
    resp_ab = await client.get(
        f"/games/h2h?team_a={test_home_team.id}&team_b={test_away_team.id}"
    )
    assert resp_ab.status_code == 200
    ids_ab = {g["id"] for g in resp_ab.json()}

    # Reversed ordering
    resp_ba = await client.get(
        f"/games/h2h?team_a={test_away_team.id}&team_b={test_home_team.id}"
    )
    assert resp_ba.status_code == 200
    ids_ba = {g["id"] for g in resp_ba.json()}

    # Both orderings must return the same set of games
    assert ids_ab == ids_ba
    assert test_game.id in ids_ab
    assert reversed_game.id in ids_ab


# ---------------------------------------------------------------------------
# Helpers for live endpoint tests
# ---------------------------------------------------------------------------

def _make_scoreboard_mock(game_status: int = 2) -> MagicMock:
    """Build a ScoreBoard mock whose .games.get_dict() returns one game entry."""
    game_entry = {
        "gameId": "0022300001",
        "gameStatus": game_status,
        "gameStatusText": "Q3 5:30" if game_status == 2 else "Final" if game_status == 3 else "7:30 pm ET",
        "gameTimeUTC": "2024-10-01T23:30:00Z",
        "period": 3 if game_status == 2 else 4 if game_status == 3 else 0,
        "gameClock": "PT05M30.00S" if game_status == 2 else "",
        "homeTeam": {"teamId": 1610612747, "score": 88 if game_status != 1 else 0},
        "awayTeam": {"teamId": 1610612738, "score": 82 if game_status != 1 else 0},
    }
    games_obj = MagicMock()
    games_obj.get_dict.return_value = [game_entry]
    mock = MagicMock()
    mock.games = games_obj
    return mock


def _make_player_entry(person_id: int, first: str, last: str) -> dict:
    return {
        "personId": person_id,
        "firstName": first,
        "familyName": last,
        "statistics": {
            "points": 20,
            "reboundsTotal": 5,
            "assists": 3,
            "steals": 1,
            "blocks": 0,
            "turnovers": 2,
            "fieldGoalsMade": 8,
            "fieldGoalsAttempted": 15,
            "threePointersMade": 2,
            "threePointersAttempted": 5,
            "freeThrowsMade": 2,
            "freeThrowsAttempted": 2,
            "minutes": "PT30M00.00S",
        },
    }


def _make_boxscore_mock(game_id: str, game_status: int = 2) -> MagicMock:
    """Build a BoxScore mock with game info and one player per side."""
    game_obj = MagicMock()
    game_obj.get_dict.return_value = {
        "gameId": game_id,
        "gameStatus": game_status,
        "gameStatusText": "Q3 5:30" if game_status == 2 else "Final",
        "period": 3 if game_status == 2 else 4,
        "gameClock": "PT05M30.00S" if game_status == 2 else "",
    }
    home_team_obj = MagicMock()
    home_team_obj.get_dict.return_value = {"score": 88}
    away_team_obj = MagicMock()
    away_team_obj.get_dict.return_value = {"score": 82}
    home_players_obj = MagicMock()
    home_players_obj.get_dict.return_value = [_make_player_entry(2544, "LeBron", "James")]
    away_players_obj = MagicMock()
    away_players_obj.get_dict.return_value = [_make_player_entry(1629029, "Jayson", "Tatum")]

    mock = MagicMock()
    mock.game = game_obj
    mock.home_team = home_team_obj
    mock.away_team = away_team_obj
    mock.home_team_player_stats = home_players_obj
    mock.away_team_player_stats = away_players_obj
    return mock


# ---------------------------------------------------------------------------
# Bulk live scoreboard: GET /games/live/today
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_live_scoreboard_cache_miss_success(client):
    """Cache miss + upstream success → 200, is_stale=False, last_updated_at recent."""
    mock_sb = _make_scoreboard_mock(game_status=2)
    with patch("app.routers.games.ScoreBoard", return_value=mock_sb):
        response = await client.get("/games/live/today")

    assert response.status_code == 200
    data = response.json()
    assert data["is_stale"] is False
    assert len(data["games"]) == 1
    assert data["games"][0]["state"] == "live"
    last_updated = datetime.fromisoformat(data["last_updated_at"])
    assert (datetime.now(timezone.utc) - last_updated).total_seconds() < 5


@pytest.mark.asyncio
async def test_live_scoreboard_cache_hit(client):
    """Second call within TTL hits cache; upstream is not called again."""
    mock_sb = _make_scoreboard_mock(game_status=2)
    with patch("app.routers.games.ScoreBoard", return_value=mock_sb) as patched:
        await client.get("/games/live/today")
        call_count_after_first = patched.call_count

        response = await client.get("/games/live/today")
        assert patched.call_count == call_count_after_first

    assert response.status_code == 200
    assert response.json()["is_stale"] is False


@pytest.mark.asyncio
async def test_live_scoreboard_stale_fallback(client):
    """Expired cache + upstream failure → 200 with is_stale=True."""
    from app.routers.games import _live_cache

    mock_sb = _make_scoreboard_mock(game_status=2)
    with patch("app.routers.games.ScoreBoard", return_value=mock_sb):
        await client.get("/games/live/today")

    # Manually expire the cache entry
    with _live_cache._lock:
        key = "today"
        value, _, last_updated_at = _live_cache._store[key]
        _live_cache._store[key] = (value, time.time() - 1, last_updated_at)

    with patch("app.routers.games.ScoreBoard", side_effect=RuntimeError("upstream down")):
        response = await client.get("/games/live/today")

    assert response.status_code == 200
    assert response.json()["is_stale"] is True


@pytest.mark.asyncio
async def test_live_scoreboard_no_cache_upstream_failure(client):
    """No cache + upstream failure → 503."""
    with patch("app.routers.games.ScoreBoard", side_effect=RuntimeError("upstream down")):
        response = await client.get("/games/live/today")

    assert response.status_code == 503


# ---------------------------------------------------------------------------
# Per-game live endpoint: GET /games/live/{game_id}
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_live_game_final_returns_409(client, test_game):
    """Game with status=3 (final) → 409 mentioning 'final'."""
    response = await client.get(f"/games/live/{test_game.id}")
    assert response.status_code == 409
    assert "final" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_live_game_pre_tipoff_returns_409(client, test_upcoming_game):
    """Game with status=1 and tipoff_at in the future → 409 mentioning 'not started'."""
    response = await client.get(f"/games/live/{test_upcoming_game.id}")
    assert response.status_code == 409
    assert "not started" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_live_game_not_found(client):
    """Non-existent game_id → 404."""
    response = await client.get("/games/live/NONEXISTENT")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_live_game_live_success(
    client,
    session,
    test_season,
    test_home_team,
    test_away_team,
    test_home_standing,
    test_away_standing,
):
    """Live game (status=1, tipoff_at in the past) → 200 with player stats."""
    from nbajinni_shared.models.games import Game

    live_game = Game(
        id="0022399001",
        home_team_id=test_home_team.id,
        away_team_id=test_away_team.id,
        game_date=date(2024, 10, 1),
        tipoff_at=datetime(2024, 10, 1, 19, 0),
        season=test_season.season,
        status=1,
    )
    session.add(live_game)
    await session.flush()

    mock_box = _make_boxscore_mock(live_game.id, game_status=2)
    with patch("app.routers.games.BoxScore", return_value=mock_box):
        response = await client.get(f"/games/live/{live_game.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == live_game.id
    assert data["is_stale"] is False
    assert len(data["home_player_stats"]) == 1
    assert len(data["away_player_stats"]) == 1
    assert data["home_player_stats"][0]["player_id"] == 2544
