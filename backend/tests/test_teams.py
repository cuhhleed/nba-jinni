"""
Happy-path tests for GET /teams/{team_id}/games.
"""
import pytest


@pytest.mark.asyncio
async def test_get_team_games(
    client,
    test_game,
    test_home_team,
    test_home_team_game_stat,
    test_away_team_game_stat,
    test_home_standing,
):
    response = await client.get(f"/teams/{test_home_team.id}/games")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == test_game.id
    # Home team stat should be populated
    assert data[0]["home_team_stat"]["team_id"] == test_home_team.id


@pytest.mark.asyncio
async def test_get_team_games_unplayed(
    client,
    test_upcoming_game,
    test_home_team,
    test_home_standing,
):
    """Upcoming game has no team_stats → both stat fields null."""
    response = await client.get(f"/teams/{test_home_team.id}/games")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["home_team_stat"] is None
    assert data[0]["away_team_stat"] is None


@pytest.mark.asyncio
async def test_get_team_games_not_found(client, test_home_standing):
    response = await client.get("/teams/9999999/games")
    assert response.status_code == 404
