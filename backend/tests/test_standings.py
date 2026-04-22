"""
Happy-path tests for /standings and /standings/preview.
One 404/empty case per endpoint per MEMORY.md guidance.
Edge cases (e.g. tie-breaking, multi-season coexistence) to be discussed before expanding.
"""
import pytest


@pytest.mark.asyncio
async def test_get_standings_returns_current_season(
    client, test_home_standing, test_away_standing
):
    response = await client.get("/standings")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # Ordered by conference then conference_rank
    conferences = [row["conference"] for row in data]
    assert conferences == sorted(conferences)


@pytest.mark.asyncio
async def test_get_standings_empty_when_no_data(client):
    # No standings fixtures — get_current_season raises HTTP 503 when
    # max(season) is NULL (no rows loaded yet).
    response = await client.get("/standings")
    assert response.status_code == 503


@pytest.mark.asyncio
async def test_get_standings_preview_returns_top_10(
    client, test_home_standing, test_away_standing
):
    response = await client.get("/standings/preview")
    assert response.status_code == 200
    data = response.json()
    # Only 2 teams in fixture — both should appear, ordered by win_pct desc
    assert len(data) == 2
    assert data[0]["win_pct"] >= data[1]["win_pct"]
