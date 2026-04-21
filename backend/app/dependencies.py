from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from nbajinni_shared.logging import configure_logging, get_logger
from nbajinni_shared.models.standings import Standing
from nbajinni_shared.session import get_session_factory

configure_logging()
logger = get_logger("backend_api")

AsyncSessionLocal = get_session_factory()


async def get_db():
    try:
        async with AsyncSessionLocal() as session:
            yield session
    except Exception as e:
        logger.error("get_session_failed", error=str(e))
        raise


async def get_current_season(db: AsyncSession) -> str:
    """
    Returns the most recent season string by querying max(Standing.season).

    Standing rows are small and always present for the active season, making this
    a reliable proxy for "current season" that avoids offseason edge cases where a
    new Season row exists but no games have been played yet.

    Raises HTTP 503 if the standings table is empty (no season data loaded).
    """
    result = await db.scalar(select(func.max(Standing.season)))
    if result is None:
        raise HTTPException(status_code=503, detail="Season data not yet loaded")
    return result