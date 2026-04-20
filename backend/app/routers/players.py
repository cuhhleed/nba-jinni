from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func

from nbajinni_shared.logging import configure_logging, get_logger
from nbajinni_shared.models.players import Player
from ..dependencies import get_db
from ..schemas.player import PlayerDetail, PlayerBase

configure_logging()
logger = get_logger("backend_api")

router = APIRouter()

@router.get("/players/search", response_model=list[PlayerBase])
async def get_player_search(q: str = Query(..., min_length=2), db: AsyncSession = Depends(get_db)):
    safe_q = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    stmt = (
        select(Player)
        .where(func.concat(Player.first_name, ' ', Player.last_name).ilike(f"%{safe_q}%", escape="\\"))
        .limit(10)
    )

    result = await db.execute(stmt)
    search_results = result.scalars().all()
    
    return search_results

@router.get("/players/{player_id}", response_model=PlayerDetail)
async def get_player_details(player_id: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Player)
        .where(Player.id == player_id)
        .options(
            selectinload(Player.team),
            selectinload(Player.game_stats),
            selectinload(Player.season_averages)
        )
    )

    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if player is None:
        raise HTTPException(status_code=404, detail="Player not found.")
    
    return player