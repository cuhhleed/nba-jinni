from datetime import datetime, timezone
from typing import Annotated

from pydantic import PlainSerializer


def _serialize_utc(dt: datetime) -> str:
    # Project convention is "naive datetimes are UTC" (see ingestion code).
    # Emit a Z suffix so JS `new Date(...)` parses as UTC instead of local time.
    if dt.tzinfo is None:
        return dt.isoformat() + "Z"
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


UTCDatetime = Annotated[datetime, PlainSerializer(_serialize_utc, return_type=str)]
