"""Tests for the Loader Lambda.

Covers:
    - _parse_row: date/datetime coercion
    - _fetch_json: S3 fetch success and failure
    - load: full async orchestration with mocked S3 + DB session
    - handler: Lambda entrypoint routing logic
"""

from datetime import date, datetime
from unittest.mock import patch

import pytest

from main import TABLE_ORDER, _fetch_json, _parse_row, handler, load

# ---------------------------------------------------------------------------
# _parse_row
# ---------------------------------------------------------------------------


class TestParseRow:
    def test_non_date_columns_pass_through(self):
        row = {"id": 1, "name": "Lakers", "wins": 40}
        assert _parse_row("teams", row) == row

    def test_datetime_string_is_coerced(self):
        row = {"game_date": "2024-10-01", "tipoff_at": "2024-10-01T19:00:00"}
        result = _parse_row("games", row)
        assert result["game_date"] == datetime(2024, 10, 1)
        assert result["tipoff_at"] == datetime(2024, 10, 1, 19, 0)

    def test_date_only_string_falls_back_to_date(self):
        # fromisoformat succeeds for "YYYY-MM-DD" as a datetime with no time,
        # so birth_date will be a datetime — just confirm it parses without
        # error and holds the right year/month/day.
        row = {"birth_date": "1984-12-30"}
        result = _parse_row("players", row)
        dt = result["birth_date"]
        assert dt.year == 1984
        assert dt.month == 12
        assert dt.day == 30

    def test_non_string_date_value_passes_through(self):
        # Already a date object — leave it alone.
        today = date.today()
        row = {"birth_date": today}
        result = _parse_row("players", row)
        assert result["birth_date"] is today

    def test_unknown_table_returns_row_unchanged(self):
        row = {"foo": "bar", "baz": 42}
        assert _parse_row("nonexistent_table", row) == row


# ---------------------------------------------------------------------------
# _fetch_json
# ---------------------------------------------------------------------------


class TestFetchJson:
    def test_returns_parsed_json(self, s3_client_with_rows, sample_rows):
        s3 = s3_client_with_rows(sample_rows)
        result = _fetch_json(s3, "my-bucket", "seasons")
        assert result == sample_rows
        s3.get_object.assert_called_once_with(
            Bucket="my-bucket", Key="exports/seasons.json"
        )

    def test_raises_on_s3_error(self, mock_s3_client):
        mock_s3_client.get_object.side_effect = Exception("NoSuchKey")
        with pytest.raises(Exception, match="NoSuchKey"):
            _fetch_json(mock_s3_client, "my-bucket", "seasons")


# ---------------------------------------------------------------------------
# load (async)
# ---------------------------------------------------------------------------


async def test_load_truncates_and_inserts(mock_session, session_factory, sample_rows):
    """load() should truncate every table then insert rows for each table."""
    with (
        patch("main.boto3.client"),
        patch("main.get_session_factory", return_value=session_factory),
        patch("main._fetch_json", return_value=sample_rows),
    ):
        await load("test-bucket")

    truncate_calls = [
        c for c in mock_session.execute.call_args_list if "TRUNCATE" in str(c.args[0])
    ]
    assert len(truncate_calls) == len(TABLE_ORDER)

    insert_calls = [
        c for c in mock_session.execute.call_args_list if "INSERT" in str(c.args[0])
    ]
    assert len(insert_calls) == len(TABLE_ORDER)


async def test_load_skips_empty_tables(mock_session, session_factory):
    """load() should not execute INSERT for tables with no rows."""
    with (
        patch("main.boto3.client"),
        patch("main.get_session_factory", return_value=session_factory),
        patch("main._fetch_json", return_value=[]),
    ):
        await load("test-bucket")

    insert_calls = [
        c for c in mock_session.execute.call_args_list if "INSERT" in str(c)
    ]
    assert insert_calls == []


async def test_load_raises_on_insert_failure(
    mock_session, session_factory, sample_rows
):
    """load() should propagate exceptions raised during INSERT."""

    async def bad_execute(stmt, *args, **kwargs):
        if "INSERT" in str(stmt):
            raise RuntimeError("insert boom")

    mock_session.execute = bad_execute

    with (
        patch("main.boto3.client"),
        patch("main.get_session_factory", return_value=session_factory),
        patch("main._fetch_json", return_value=sample_rows),
        pytest.raises(RuntimeError, match="insert boom"),
    ):
        await load("test-bucket")


# ---------------------------------------------------------------------------
# handler
# ---------------------------------------------------------------------------


class TestHandler:
    def _event(self, action):
        return {"action": action}

    def test_load_action_returns_200(self):
        with patch("main.asyncio.run", lambda coro: coro.close()):
            response = handler(self._event("load"), {})
        assert response["statusCode"] == 200
        assert response["body"] == "Load complete."

    def test_migrate_action_calls_migrate_and_returns_200(self):
        with (
            patch("main.migrate") as mock_migrate,
            patch("main.asyncio.run", lambda coro: coro.close()),
        ):
            response = handler(self._event("migrate"), {})
        mock_migrate.assert_called_once()
        assert response["statusCode"] == 200
        assert "Migration" in response["body"]

    def test_invalid_action_returns_500(self):
        response = handler(self._event("explode"), {})
        assert response["statusCode"] == 500

    def test_load_exception_propagates(self):
        with (
            patch("main.load", side_effect=RuntimeError("db down")),
            pytest.raises(RuntimeError, match="db down"),
        ):
            handler(self._event("load"), {})
