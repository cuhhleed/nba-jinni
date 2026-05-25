"""
Loader Lambda test configuration.

Fixtures are the source of truth for shared test infrastructure — no setup
logic duplicated across test modules.

All mock fixtures are function-scoped so each test gets a clean slate.
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def lambda_env(monkeypatch):
    """Inject the minimum environment variables the handler requires."""
    monkeypatch.setenv("DATA_BUCKET_NAME", "test-bucket")


# ---------------------------------------------------------------------------
# S3
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_s3_client():
    """Bare S3 MagicMock. Tests configure get_object as needed."""
    return MagicMock()


@pytest.fixture
def s3_client_with_rows(mock_s3_client):
    """
    Factory fixture: call it with a payload list to get an S3 client whose
    get_object returns that payload serialised as JSON.

        def test_something(s3_client_with_rows):
            s3 = s3_client_with_rows([{"id": 1}])
    """

    def _make(payload: list[dict]):
        body = MagicMock()
        body.read.return_value = json.dumps(payload).encode()
        mock_s3_client.get_object.return_value = {"Body": body}
        return mock_s3_client

    return _make


# ---------------------------------------------------------------------------
# Database session
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.execute = AsyncMock()

    begin_cm = MagicMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=False)
    session.begin = MagicMock(return_value=begin_cm)

    return session


@pytest.fixture
def session_factory(mock_session):
    # Mirrors what get_session_factory() returns: a sessionmaker callable
    # whose __call__ produces an async context manager.
    #
    # load() does:
    #   AsyncSessionLocal = get_session_factory()   ← patched to return session_factory
    #   async with AsyncSessionLocal() as session:  ← session_factory() must be an async
    #   CM
    #
    # So session_factory itself must be the thing load() calls directly.
    # get_session_factory is patched with return_value=session_factory, meaning
    # get_session_factory() → session_factory, then load() calls session_factory().

    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=mock_session)
    cm.__aexit__ = AsyncMock(return_value=False)

    return MagicMock(return_value=cm)


# ---------------------------------------------------------------------------
# Common data
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_rows():
    """Minimal single-row payload reused across load() tests."""
    return [{"id": 1, "season": "2024-25"}]
