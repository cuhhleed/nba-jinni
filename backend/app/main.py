from mangum import Mangum
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text , select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta
import os
from dotenv import load_dotenv

from nbajinni_shared.session import get_session_factory
from nbajinni_shared.logging import configure_logging, get_logger
from nbajinni_shared.models.teams import Team
from nbajinni_shared.models.players import Player
from nbajinni_shared.models.games import Game
from nbajinni_shared.models.team_season_averages import TeamSeasonAverage

from .schemas.team import TeamBase, TeamDetail
from .schemas.player import PlayerDetail, PlayerBase
from .schemas.game import GameWithTeams, GameBase

load_dotenv()

configure_logging()
logger = get_logger("backend_api")

AsyncSessionLocal = get_session_factory()

app = FastAPI()


origins = [
    os.getenv("FRONTEND_ORIGIN")
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_db():
    
    try:
        async with AsyncSessionLocal() as session:
            yield session
    except Exception as e:
        logger.error("get_session_failed", error=str(e))
        raise


@app.get("/")
async def root():
    return {
        "name": "NBAJinni API",
        "version": "0.1.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))  # Verify DB connection
    return {"status": "healthy"}

@app.get("/teams", response_model=list[TeamBase])
async def get_teams(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team))
    return result.scalars().all()

@app.get("/teams/{team_id}", response_model=TeamDetail)
async def get_team_details(team_id: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Team)
        .where(Team.id == team_id)
        .options(
            selectinload(Team.standing),
            selectinload(Team.season_averages),
            selectinload(Team.players)
        )
    )

    result = await db.execute(stmt)
    team = result.scalar_one_or_none()

    if team is None:
        raise HTTPException(status_code=404, detail="Team not found.")
    
    return team

@app.get("/teams/{team_id}/roster", response_model=list[PlayerBase])
async def get_team_roster(team_id: int, db: AsyncSession = Depends(get_db)):
    team_exists = await db.scalar(select(Team.id).where(Team.id == team_id))
    if team_exists is None:
        raise HTTPException(status_code=404, detail="Team not found.")
    
    stmt = (
        select(Player)
        .where(Player.team_id == team_id)
    )

    result = await db.execute(stmt)
    roster = result.scalars().all()

    if not roster:
        logger.warning("team_empty_roster", message="Team has no players, but probably should.", team_id=team_id)
    
    return roster

@app.get("/players/search", response_model=list[PlayerBase])
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

@app.get("/players/{player_id}", response_model=PlayerDetail)
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

@app.get("/games/upcoming", response_model=list[GameBase])
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

@app.get("/games/{game_id}", response_model=GameWithTeams)
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

handler = Mangum(app, lifespan="off")
