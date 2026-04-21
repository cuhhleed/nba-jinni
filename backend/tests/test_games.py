"""
Happy-path tests for game endpoints:
  GET /games/{game_id}          — discriminated union (preview / result)
  GET /games/{game_id}/playerstats
  GET /games/h2h
"""
import pytest


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
    from datetime import date
    from nbajinni_shared.models.games import Game

    # Add a reversed fixture — BOS home, LAL away — in the same season
    reversed_game = Game(
        id="0022300002",
        home_team_id=test_away_team.id,
        away_team_id=test_home_team.id,
        game_date=date(2024, 11, 1),
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
