from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, or_

from nbajinni_shared.logging import configure_logging, get_logger
from nbajinni_shared.models.teams import Team
from nbajinni_shared.models.games import Game
from ..dependencies import get_db, get_current_season
from ..schemas.team import TeamBase, TeamDetail, TeamWithRoster
from ..schemas.game import GameWithTeamStats

configure_logging()
logger = get_logger("backend_api")

router = APIRouter()

@router.get("/teams", response_model=list[TeamBase])
async def get_teams(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team))
    return result.scalars().all()

@router.get("/teams/{team_id}", response_model=TeamDetail)
async def get_team_details(team_id: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Team)
        .where(Team.id == team_id)
        .options(
            selectinload(Team.standing),
            selectinload(Team.season_averages)
        )
    )

    result = await db.execute(stmt)
    team = result.scalar_one_or_none()

    if team is None:
        raise HTTPException(status_code=404, detail="Team not found.")
    
    return team

@router.get("/teams/{team_id}/roster", response_model=TeamWithRoster)
async def get_team_roster(team_id: int, db: AsyncSession = Depends(get_db)):
    team_exists = await db.scalar(select(Team.id).where(Team.id == team_id))
    if team_exists is None:
        raise HTTPException(status_code=404, detail="Team not found.")
    
    stmt = (
        select(Team)
        .where(Team.id == team_id)
        .options(
            selectinload(Team.players)
        )
    )

    result = await db.execute(stmt)
    team_roster = result.scalar()

    if not team_roster:
        logger.warning("team_empty_roster", message="Team has no players, but probably should.", team_id=team_id)

    return team_roster


@router.get("/teams/{team_id}/games", response_model=list[GameWithTeamStats])
async def get_team_games(team_id: int, db: AsyncSession = Depends(get_db)):
    team_exists = await db.scalar(select(Team.id).where(Team.id == team_id))
    if team_exists is None:
        raise HTTPException(status_code=404, detail="Team not found.")

    current_season = await get_current_season(db)

    stmt = (
        select(Game)
        .where(
            or_(Game.home_team_id == team_id, Game.away_team_id == team_id),
            Game.season == current_season,
        )
        .options(selectinload(Game.team_stats))
        .order_by(Game.game_date.asc())
    )

    result = await db.execute(stmt)
    games = result.scalars().all()

    return [GameWithTeamStats.model_validate(g) for g in games]