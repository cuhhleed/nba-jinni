from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from datetime import date, timedelta

from nbajinni_shared.models.teams import Team
from nbajinni_shared.models.games import Game
from nbajinni_shared.models.team_season_averages import TeamSeasonAverage
from ..dependencies import get_db
from ..schemas.game import GameWithTeams, GameBase

router = APIRouter()

@router.get("/games/upcoming", response_model=list[GameBase])
async def get_upcoming_games(
    limit: int = Query(15, ge=1, le=50),
days: int = Query(3, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
):
    date_offset = date.today() + timedelta(days=days)
    stmt = (
        select(Game)
        .where(Game.game_date < date_offset, Game.game_date >= date.today())
        .order_by(Game.game_date.asc(), Game.id.asc())
        .limit(limit)
    )

    result = await db.execute(stmt)
    upcoming_games = result.scalars().all()
    
    return upcoming_games

@router.get("/games/{game_id}", response_model=GameWithTeams)
async def get_game_details(game_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalar_one_or_none()

    if game is None:
        raise HTTPException(status_code=404, detail="Game not found.")
    
    season = game.season

    stmt = (
        select(Game)
        .where(Game.id == game_id)
        .options(
            selectinload(Game.home_team).selectinload(
                Team.season_averages.and_(TeamSeasonAverage.season == season)
            ),
            selectinload(Game.away_team).selectinload(
                Team.season_averages.and_(TeamSeasonAverage.season == season)
            )
        )
    )

    result = await db.execute(stmt)
    return result.scalar_one()