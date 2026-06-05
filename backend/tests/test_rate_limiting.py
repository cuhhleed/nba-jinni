"""
Rate limiting tests using slowapi.

Verifies the 100/minute default limit enforced by SlowAPIMiddleware. The root
endpoint `/` is used deliberately: it returns a static payload with no DB
dependency, so the only behaviour under test is the limiter itself. The autouse
`reset_rate_limiter` fixture (conftest.py) clears the counter before each test.
"""

import pytest


@pytest.mark.asyncio
async def test_request_under_limit(client):
    """The first 100 requests in a window all return 200."""
    for _ in range(100):
        response = await client.get("/")
        assert response.status_code == 200, "Expected 200 under rate limit"


@pytest.mark.asyncio
async def test_request_exceeds_limit(client):
    """The 101st request in a window returns 429."""
    for _ in range(100):
        response = await client.get("/")
        assert response.status_code == 200, "First 100 requests should return 200"

    response = await client.get("/")
    assert response.status_code == 429, "Request 101 should return 429 (rate limited)"
