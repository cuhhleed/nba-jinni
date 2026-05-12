from datetime import date as date_type
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
from ..schemas.player_game_stat import PlayerGameStatBase, PlayerGameStatWithContext, RecentPerformance
from ..schemas.player_season_average import (
    PlayerSeasonAverageBase,
    PlayerSeasonAverageWithPlayer,
)

configure_logging()
logger = get_logger("backend_api")

router = APIRouter()


@router.get("/players/search", response_model=list[PlayerBase])
async def get_player_search(
    q: str = Query(..., min_length=2), db: AsyncSession = Depends(get_db)
):
    safe_q = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    stmt = (
        select(Player)
        .where(
            Player.team_id != 0,
            func.concat(Player.first_name, " ", Player.last_name).ilike(
                f"%{safe_q}%", escape="\\"
            ),
        )
        .limit(10)
    )

    result = await db.execute(stmt)
    search_results = result.scalars().all()

    return search_results


@router.get("/players", response_model=list[PlayerBase])
async def get_player_search(db: AsyncSession = Depends(get_db)):

    stmt = select(Player).where(Player.team_id != 0)

    result = await db.execute(stmt)
    search_results = result.scalars().all()

    return search_results


@router.get(
    "/players/top/preview",
    response_model=dict[str, list[PlayerSeasonAverageWithPlayer]],
)
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
        select(func.max(PlayerSeasonAverage.games_played)).where(
            PlayerSeasonAverage.season == current_season
        )
    )
    apply_floor = max_games_played is not None and max_games_played >= 10

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
        "points": PlayerSeasonAverage.points_pg,
        "rebounds": PlayerSeasonAverage.tot_reb_pg,
        "assists": PlayerSeasonAverage.asts_pg,
        "steals": PlayerSeasonAverage.stls_pg,
        "blocks": PlayerSeasonAverage.blks_pg,
    }

    result_map: dict[str, list[PlayerSeasonAverageWithPlayer]] = {}
    for key, col in categories.items():
        rows = (await db.execute(build_top3_stmt(col))).scalars().all()
        result_map[key] = [
            PlayerSeasonAverageWithPlayer.model_validate(r) for r in rows
        ]

    return result_map


@router.get(
    "/players/top/recent-performances",
    response_model=list[RecentPerformance],
)
async def get_recent_top_performances(db: AsyncSession = Depends(get_db)):
    """
    Returns up to 3 standout individual performances from the last two ingested game-days.

    Recency is defined relative to the most-recent game_date that has player_game_stats
    rows — not by calendar offset from now — so UTC/ET drift on west-coast games does
    not create a one-day gap in results.

    Scoring: base = points + tot_reb + asts + stls + blks.
    Rows where base < 35 are discarded.  Rows from the most-recent game-day receive a
    +5 bonus.  Results are sorted by (base + bonus) desc, then base desc as a tie-break.
    """
    current_date_utc = date_type.today()

    recent_dates_stmt = (
        select(Game.game_date)
        .join(PlayerGameStat, PlayerGameStat.game_id == Game.id)
        .where(Game.game_date <= current_date_utc)
        .group_by(Game.game_date)
        .order_by(Game.game_date.desc())
        .limit(2)
    )
    recent_dates_result = await db.execute(recent_dates_stmt)
    recent_date_rows = recent_dates_result.scalars().all()

    if not recent_date_rows:
        return []

    most_recent = recent_date_rows[0]
    recent_dates = list(recent_date_rows)

    stmt = (
        select(PlayerGameStat, Game.game_date, Player.first_name, Player.last_name, Player.team_id)
        .join(Game, PlayerGameStat.game_id == Game.id)
        .join(Player, PlayerGameStat.player_id == Player.id)
        .where(Game.game_date.in_(recent_dates))
    )
    rows = (await db.execute(stmt)).all()

    scored: list[tuple[int, int, RecentPerformance]] = []
    for pgs, game_date, first_name, last_name, team_id in rows:
        base = pgs.points + pgs.tot_reb + pgs.asts + pgs.stls + pgs.blks
        if base < 35:
            continue
        bonus = 5 if game_date == most_recent else 0
        perf = RecentPerformance(
            player_id=pgs.player_id,
            full_name=f"{first_name} {last_name}",
            team_id=team_id,
            game_id=pgs.game_id,
            points=pgs.points,
            tot_reb=pgs.tot_reb,
            asts=pgs.asts,
            stls=pgs.stls,
            blks=pgs.blks,
        )
        scored.append((base + bonus, base, perf))

    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [perf for _, _, perf in scored[:3]]


@router.get(
    "/players/{player_id}/season-average", response_model=PlayerSeasonAverageBase
)
async def get_player_season_average(player_id: int, db: AsyncSession = Depends(get_db)):
    player_exists = await db.scalar(select(Player.id).where(Player.id == player_id))
    if player_exists is None:
        raise HTTPException(status_code=404, detail="Player not found.")

    stmt = (
        select(PlayerSeasonAverage)
        .where(PlayerSeasonAverage.player_id == player_id)
        .order_by(PlayerSeasonAverage.season.desc())
        .limit(1)
    )

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


@router.get(
    "/players/{player_id}/last-5-games", response_model=list[PlayerGameStatWithContext]
)
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


@router.get(
    "/players/{player_id}/vs-opponent", response_model=list[PlayerGameStatWithContext]
)
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
