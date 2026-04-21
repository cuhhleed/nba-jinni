from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from nbajinni_shared.logging import configure_logging, get_logger
from nbajinni_shared.models.standings import Standing
from ..dependencies import get_db, get_current_season
from ..schemas.standing import StandingBase

configure_logging()
logger = get_logger("backend_api")

router = APIRouter()


@router.get("/standings", response_model=list[StandingBase])
async def get_standings(db: AsyncSession = Depends(get_db)):
    current_season = await get_current_season(db)

    stmt = (
        select(Standing)
        .where(Standing.season == current_season)
        .order_by(Standing.conference, Standing.conference_rank)
    )

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/standings/preview", response_model=list[StandingBase])
async def get_standings_preview(db: AsyncSession = Depends(get_db)):
    # Crosses conference boundaries — top 10 by win_pct regardless of East/West.
    current_season = await get_current_season(db)

    stmt = (
        select(Standing)
        .where(Standing.season == current_season)
        .order_by(Standing.win_pct.desc())
        .limit(10)
    )

    result = await db.execute(stmt)
    return result.scalars().all()
