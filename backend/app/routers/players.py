from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func

from nbajinni_shared.logging import configure_logging, get_logger
from nbajinni_shared.models.players import Player
from nbajinni_shared.models.games import Game
from nbajinni_shared.models.player_game_stats import PlayerGameStat
from nbajinni_shared.models.player_season_averages import PlayerSeasonAverage
from ..dependencies import get_db, get_current_season
from ..schemas.player import PlayerDetail, PlayerBase
from ..schemas.player_game_stat import PlayerGameStatBase, PlayerGameStatWithContext
from ..schemas.player_season_average import PlayerSeasonAverageBase, PlayerSeasonAverageWithPlayer

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


@router.get("/players/top/preview", response_model=dict[str, list[PlayerSeasonAverageWithPlayer]])
async def get_top_players_preview(db: AsyncSession = Depends(get_db)):
    """
    Returns top 3 players per stat category for the current season.
    Categories: points, rebounds, assists, steals, blocks.

    Early-season handling: the games_played >= 10 floor is only applied when at
    least one player in the league has played >= 10 games; otherwise no floor.

    Note: queries run sequentially rather than via asyncio.gather because
    AsyncSession is not safe for concurrent access on the same session object.
    """
    current_season = await get_current_season(db)

    # Determine whether the games-played floor should apply
    max_games_played = await db.scalar(
        select(func.max(PlayerSeasonAverage.games_played))
        .where(PlayerSeasonAverage.season == current_season)
    )
    apply_floor = (max_games_played is not None and max_games_played >= 10)

    def build_top3_stmt(order_col):
        stmt = (
            select(PlayerSeasonAverage)
            .where(PlayerSeasonAverage.season == current_season)
            .options(selectinload(PlayerSeasonAverage.player))
            .order_by(order_col.desc())
            .limit(3)
        )
        if apply_floor:
            stmt = stmt.where(PlayerSeasonAverage.games_played >= 10)
        return stmt

    categories = {
        "points":   PlayerSeasonAverage.points_pg,
        "rebounds": PlayerSeasonAverage.tot_reb_pg,
        "assists":  PlayerSeasonAverage.asts_pg,
        "steals":   PlayerSeasonAverage.stls_pg,
        "blocks":   PlayerSeasonAverage.blks_pg,
    }

    result_map: dict[str, list[PlayerSeasonAverageWithPlayer]] = {}
    for key, col in categories.items():
        rows = (await db.execute(build_top3_stmt(col))).scalars().all()
        result_map[key] = [PlayerSeasonAverageWithPlayer.model_validate(r) for r in rows]

    return result_map


@router.get("/players/{player_id}/season-averages", response_model=list[PlayerSeasonAverageBase])
async def get_player_season_averages(player_id: int, db: AsyncSession = Depends(get_db)):
    player_exists = await db.scalar(select(Player.id).where(Player.id == player_id))
    if player_exists is None:
        raise HTTPException(status_code=404, detail="Player not found.")

    stmt = (
        select(PlayerSeasonAverage)
        .where(PlayerSeasonAverage.player_id == player_id)
        .order_by(PlayerSeasonAverage.season.desc())
    )

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/players/{player_id}/last-5-games", response_model=list[PlayerGameStatWithContext])
async def get_player_last_5_games(player_id: int, db: AsyncSession = Depends(get_db)):
    player_exists = await db.scalar(select(Player.id).where(Player.id == player_id))
    if player_exists is None:
        raise HTTPException(status_code=404, detail="Player not found.")

    stmt = (
        select(PlayerGameStat, Game)
        .join(Game, PlayerGameStat.game_id == Game.id)
        .where(PlayerGameStat.player_id == player_id)
        .order_by(Game.game_date.desc())
        .limit(5)
    )

    rows = (await db.execute(stmt)).all()

    stats: list[PlayerGameStatWithContext] = []
    for pgs, game in rows:
        opponent_team_id = (
            game.away_team_id if pgs.team_id == game.home_team_id else game.home_team_id
        )
        base = PlayerGameStatBase.model_validate(pgs).model_dump()
        base["game_date"] = game.game_date
        base["opponent_team_id"] = opponent_team_id
        stats.append(PlayerGameStatWithContext.model_validate(base))
    return stats


@router.get("/players/{player_id}/vs-opponent", response_model=list[PlayerGameStatWithContext])
async def get_player_vs_opponent(
    player_id: int,
    team_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    player_exists = await db.scalar(select(Player.id).where(Player.id == player_id))
    if player_exists is None:
        raise HTTPException(status_code=404, detail="Player not found.")

    current_season = await get_current_season(db)

    stmt = (
        select(PlayerGameStat, Game)
        .join(Game, PlayerGameStat.game_id == Game.id)
        .where(
            PlayerGameStat.player_id == player_id,
            PlayerGameStat.season == current_season,
            # The target team must appear in the game (either side)
            (Game.home_team_id == team_id) | (Game.away_team_id == team_id),
            # The player must not be on the target team
            PlayerGameStat.team_id != team_id,
        )
        .order_by(Game.game_date.desc())
    )

    rows = (await db.execute(stmt)).all()

    stats: list[PlayerGameStatWithContext] = []
    for pgs, game in rows:
        opponent_team_id = (
            game.away_team_id if pgs.team_id == game.home_team_id else game.home_team_id
        )
        base = PlayerGameStatBase.model_validate(pgs).model_dump()
        base["game_date"] = game.game_date
        base["opponent_team_id"] = opponent_team_id
        stats.append(PlayerGameStatWithContext.model_validate(base))
    return stats


@router.get("/players/{player_id}", response_model=PlayerDetail)
async def get_player_details(player_id: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Player)
        .where(Player.id == player_id)
        .options(
            selectinload(Player.team),
        )
    )

    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if player is None:
        raise HTTPException(status_code=404, detail="Player not found.")

    return player
