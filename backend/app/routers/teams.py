from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, or_, and_

from nbajinni_shared.logging import configure_logging, get_logger
from nbajinni_shared.models.teams import Team
from nbajinni_shared.models.games import Game
from ..dependencies import get_db, get_current_season
from nbajinni_shared.models.players import Player
from nbajinni_shared.models.team_season_averages import TeamSeasonAverage
from ..schemas.team import TeamBase, TeamWithStanding, TeamStatsResponse
from ..schemas.player import PlayerBase
from ..schemas.game import GameWithTeamStats, TeamScheduleResponse

configure_logging()
logger = get_logger("backend_api")

router = APIRouter()

@router.get("/teams", response_model=list[TeamBase])
async def get_teams(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team))
    return result.scalars().all()

@router.get("/teams/{team_id}", response_model=TeamWithStanding)
async def get_team_details(team_id: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Team)
        .where(Team.id == team_id)
        .options(selectinload(Team.standing))
    )

    result = await db.execute(stmt)
    team = result.scalar_one_or_none()

    if team is None:
        raise HTTPException(status_code=404, detail="Team not found.")

    return team


@router.get("/teams/{team_id}/stats", response_model=TeamStatsResponse)
async def get_team_stats(team_id: int, db: AsyncSession = Depends(get_db)):
    team_exists = await db.scalar(select(Team.id).where(Team.id == team_id))
    if team_exists is None:
        raise HTTPException(status_code=404, detail="Team not found.")

    current_season = await get_current_season(db)

    season_average = await db.scalar(
        select(TeamSeasonAverage)
        .where(TeamSeasonAverage.team_id == team_id, TeamSeasonAverage.season == current_season)
    )

    team_filter = and_(or_(Game.home_team_id == team_id, Game.away_team_id == team_id),
                       Game.status == Game.COMPLETED_STATUS,
                       Game.season == current_season)

    recent_games = (await db.execute(
        select(Game)
        .where(team_filter)
        .options(selectinload(Game.team_stats))
        .order_by(Game.game_date.desc())
        .limit(5)
    )).scalars().all()

    return TeamStatsResponse(
        season_average=season_average,
        recent_game_stats=[GameWithTeamStats.model_validate(g) for g in recent_games]
    )

@router.get("/teams/{team_id}/roster", response_model=list[PlayerBase])
async def get_team_roster(team_id: int, db: AsyncSession = Depends(get_db)):
    team_exists = await db.scalar(select(Team.id).where(Team.id == team_id))
    if team_exists is None:
        raise HTTPException(status_code=404, detail="Team not found.")

    result = await db.execute(select(Player).where(Player.team_id == team_id))
    players = result.scalars().all()

    if not players:
        logger.warning("team_empty_roster", message="Team has no players, but probably should.", team_id=team_id)

    return players


@router.get("/teams/{team_id}/games", response_model=TeamScheduleResponse)
async def get_team_games(team_id: int, db: AsyncSession = Depends(get_db)):
    team_exists = await db.scalar(select(Team.id).where(Team.id == team_id))
    if team_exists is None:
        raise HTTPException(status_code=404, detail="Team not found.")

    current_season = await get_current_season(db)
    team_filter = and_(or_(Game.home_team_id == team_id, Game.away_team_id == team_id),
                       Game.season == current_season)

    recent_result = await db.execute(
        select(Game)
        .where(team_filter, Game.status == Game.COMPLETED_STATUS)
        .options(selectinload(Game.team_stats))
        .order_by(Game.game_date.desc())
        .limit(10)
    )
    recent = [GameWithTeamStats.model_validate(g) for g in recent_result.scalars().all()]

    upcoming_result = await db.execute(
        select(Game)
        .where(team_filter, Game.status != Game.COMPLETED_STATUS)
        .order_by(Game.game_date.asc())
        .limit(10)
    )
    upcoming = upcoming_result.scalars().all()

    return TeamScheduleResponse(recent=recent, upcoming=upcoming)