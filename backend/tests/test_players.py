"""
Happy-path tests for new player endpoints:
  GET /players/top/preview
  GET /players/{player_id}/season-averages
  GET /players/{player_id}/last-5-games
  GET /players/{player_id}/vs-opponent
"""
import pytest


@pytest.mark.asyncio
async def test_get_player_season_averages(
    client, test_player, test_player_season_average
):
    response = await client.get(f"/players/{test_player.id}/season-averages")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["player_id"] == test_player.id
    assert data[0]["season"] == test_player_season_average.season


@pytest.mark.asyncio
async def test_get_player_season_averages_not_found(client):
    response = await client.get("/players/9999999/season-averages")
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
