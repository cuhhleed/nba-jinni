from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, or_
from datetime import date, timedelta

from nbajinni_shared.logging import configure_logging, get_logger
from nbajinni_shared.models.teams import Team
from nbajinni_shared.models.team_season_averages import TeamSeasonAverage
from nbajinni_shared.models.games import Game
from nbajinni_shared.models.player_game_stats import PlayerGameStat
from ..dependencies import get_db, get_current_season
from ..schemas.game import (
    GameBase,
    GameWithTeams,
    GamePreview,
    GameResult,
    GameDetailResponse,
    GameWithTeamStats,
)
from ..schemas.player_game_stat import PlayerGameStatBase

configure_logging()
logger = get_logger("backend_api")

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


@router.get("/games/h2h", response_model=list[GameWithTeamStats])
async def get_h2h_games(
    team_a: int = Query(...),
    team_b: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns all head-to-head games between two teams for the current season.
    The matchup is symmetric — either team can be home or away.
    Returns an empty list (not 404) when the teams haven't played each other yet.
    """
    current_season = await get_current_season(db)

    stmt = (
        select(Game)
        .where(
            Game.season == current_season,
            or_(
                (Game.home_team_id == team_a) & (Game.away_team_id == team_b),
                (Game.home_team_id == team_b) & (Game.away_team_id == team_a),
            ),
        )
        .options(selectinload(Game.team_stats))
        .order_by(Game.game_date.asc())
    )

    result = await db.execute(stmt)
    games = result.scalars().all()

    return [GameWithTeamStats.model_validate(g) for g in games]


@router.get("/games/{game_id}/playerstats", response_model=list[PlayerGameStatBase])
async def get_game_player_stats(game_id: str, db: AsyncSession = Depends(get_db)):
    game_exists = await db.scalar(select(Game.id).where(Game.id == game_id))
    if game_exists is None:
        raise HTTPException(status_code=404, detail="Game not found.")

    stmt = (
        select(PlayerGameStat)
        .where(PlayerGameStat.game_id == game_id)
        .order_by(PlayerGameStat.team_id, PlayerGameStat.points.desc())
    )

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/games/{game_id}", response_model=GameDetailResponse)
async def get_game_details(game_id: str, db: AsyncSession = Depends(get_db)):
    game = await db.scalar(select(Game).where(Game.id == game_id))
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found.")

    if game.status == Game.COMPLETED_STATUS:
        stmt = (
            select(Game)
            .where(Game.id == game_id)
            .options(
                selectinload(Game.team_stats),
                selectinload(Game.home_team).selectinload(Team.standing),
                selectinload(Game.away_team).selectinload(Team.standing),
            )
        )
        game = (await db.execute(stmt)).scalar_one()
        if len(game.team_stats) < 2:
            raise HTTPException(
                status_code=409,
                detail="Game is marked complete but team stats are not yet available.",
            )
        return GameResult.model_validate(game)

    stmt = (
        select(Game)
        .where(Game.id == game_id)
        .options(
            selectinload(Game.home_team).selectinload(
                Team.season_averages.and_(TeamSeasonAverage.season == game.season)
            ),
            selectinload(Game.home_team).selectinload(Team.standing),
            selectinload(Game.away_team).selectinload(
                Team.season_averages.and_(TeamSeasonAverage.season == game.season)
            ),
            selectinload(Game.away_team).selectinload(Team.standing),
        )
    )
    game = (await db.execute(stmt)).scalar_one()
    return GamePreview.model_validate(game)
