"""
Tests for GET /teams/{team_id}/games and GET /teams/{team_id}/season-average.
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
    assert len(data["recent"]) == 1
    assert data["recent"][0]["id"] == test_game.id
    assert data["recent"][0]["home_team_stat"]["team_id"] == test_home_team.id


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
    assert len(data["upcoming"]) == 1
    assert data["upcoming"][0]["id"] == test_upcoming_game.id


@pytest.mark.asyncio
async def test_get_team_games_not_found(client, test_home_standing):
    response = await client.get("/teams/9999999/games")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_team_games_includes_game_type(
    client,
    test_game,
    test_upcoming_game,
    test_home_team,
    test_home_team_game_stat,
    test_away_team_game_stat,
    test_home_standing,
):
    """Both recent and upcoming game entries include game_type field."""
    response = await client.get(f"/teams/{test_home_team.id}/games")
    assert response.status_code == 200
    data = response.json()
    for game in data["recent"]:
        assert "game_type" in game
    for game in data["upcoming"]:
        assert "game_type" in game


@pytest.mark.asyncio
async def test_get_team_season_average_regular(
    client, test_home_team, test_home_team_season_average
):
    """Regular season average present → 200 with matching team_id and season."""
    response = await client.get(f"/teams/{test_home_team.id}/season-average")
    assert response.status_code == 200
    data = response.json()
    assert data["team_id"] == test_home_team.id
    assert data["season"] == test_home_team_season_average.season


@pytest.mark.asyncio
async def test_get_team_season_average_playoff(
    client, test_home_team, test_home_team_playoff_season_average
):
    """Playoff average present → 200 with matching team_id and season."""
    response = await client.get(
        f"/teams/{test_home_team.id}/season-average?type=playoff"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["team_id"] == test_home_team.id
    assert data["season"] == test_home_team_playoff_season_average.season


@pytest.mark.asyncio
async def test_get_team_season_average_playoff_missing(client, test_home_team):
    """Team exists but has no playoff row → 200 with null body."""
    response = await client.get(
        f"/teams/{test_home_team.id}/season-average?type=playoff"
    )
    assert response.status_code == 200
    assert response.json() is None


@pytest.mark.asyncio
async def test_get_team_season_average_not_found(client):
    """Team does not exist → 404."""
    response = await client.get("/teams/9999999/season-average")
    assert response.status_code == 404
