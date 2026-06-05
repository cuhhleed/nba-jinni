import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from nba_api.live.nba.endpoints import BoxScore, ScoreBoard
from nbajinni_shared.logging import configure_logging, get_logger
from nbajinni_shared.models.games import Game
from nbajinni_shared.models.player_game_stats import PlayerGameStat
from nbajinni_shared.models.team_season_averages import TeamSeasonAverage
from nbajinni_shared.models.teams import Team
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..cache.stale_cache import StaleCache
from ..dependencies import get_current_season, get_db
from ..limiter import limiter
from ..schemas.game import (
    GameDetailResponse,
    GameLive,
    GamePreview,
    GameResult,
    GameWithTeamStats,
    LiveScoreboardEntry,
    LiveScoreboardResponse,
    PlayerLiveStat,
)
from ..schemas.player_game_stat import PlayerGameStatBase, PlayerGameStatWithName
from ..schemas.team_game_stat import TeamGameStatBase

configure_logging()
logger = get_logger("backend_api")

router = APIRouter()

_live_cache: StaleCache = StaleCache()

_GAME_STATUS_MAP = {1: "scheduled", 2: "live", 3: "final"}

# nba_api ships a Chrome 87 (Dec 2020) User-Agent that Akamai's bot protection now
# flags with HTTP 403 + an HTML "Access Denied" page. We override with a current
# Chrome fingerprint plus Origin/Referer/sec-ch-ua headers.
_LIVE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",  # noqa: E501
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Origin": "https://www.nba.com",
    "Referer": "https://www.nba.com/",
    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}


def _bulk_ttl(scoreboard) -> float:
    games = scoreboard.games.get_dict()
    statuses = [g.get("gameStatus") for g in games]
    if 2 in statuses:
        return 30.0
    if statuses and all(s == 3 for s in statuses):
        return 300.0
    return 1800.0


def _per_game_ttl(boxscore) -> float:
    game_info = boxscore.game.get_dict()
    status = game_info.get("gameStatus")
    if status == 2:
        return 30.0
    return 300.0


def _safe_div(num: float, denom: float) -> float:
    return num / denom if denom else 0.0


def _build_live_team_stat(
    *,
    team_stats: dict,
    game_id: str,
    team_id: int,
    season: str,
    own_points: int,
    opp_points: int,
) -> TeamGameStatBase:
    return TeamGameStatBase(
        game_id=game_id,
        team_id=team_id,
        season=season,
        points=own_points,
        opponent_points=opp_points,
        rebounds=team_stats.get("reboundsTotal", 0),
        assists=team_stats.get("assists", 0),
        steals=team_stats.get("steals", 0),
        blocks=team_stats.get("blocks", 0),
        turnovers=team_stats.get("turnovers", 0),
        fg_pct=_safe_div(
            team_stats.get("fieldGoalsMade", 0),
            team_stats.get("fieldGoalsAttempted", 0),
        ),
        three_pct=_safe_div(
            team_stats.get("threePointersMade", 0),
            team_stats.get("threePointersAttempted", 0),
        ),
        ft_pct=_safe_div(
            team_stats.get("freeThrowsMade", 0),
            team_stats.get("freeThrowsAttempted", 0),
        ),
    )


def _build_player_stat(p: dict) -> PlayerLiveStat:
    stats = p.get("statistics", {})
    return PlayerLiveStat(
        player_id=p["personId"],
        first_name=p["firstName"],
        last_name=p["familyName"],
        points=stats.get("points", 0),
        rebounds=stats.get("reboundsTotal", 0),
        assists=stats.get("assists", 0),
        steals=stats.get("steals", 0),
        blocks=stats.get("blocks", 0),
        turnovers=stats.get("turnovers", 0),
        fg_made=stats.get("fieldGoalsMade", 0),
        fg_attempted=stats.get("fieldGoalsAttempted", 0),
        three_made=stats.get("threePointersMade", 0),
        three_attempted=stats.get("threePointersAttempted", 0),
        ft_made=stats.get("freeThrowsMade", 0),
        ft_attempted=stats.get("freeThrowsAttempted", 0),
        minutes=stats.get("minutes", "PT00M00.00S"),
    )


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


@router.get("/games/live/today", response_model=LiveScoreboardResponse)
@limiter.limit("30/minute")
async def get_live_scoreboard(request: Request):
    cached = _live_cache.get_fresh("today")
    if cached is not None:
        logger.info("live_cache_hit", key="today")
        return cached

    try:
        data = await asyncio.to_thread(ScoreBoard, headers=_LIVE_HEADERS)
        games_list = data.games.get_dict()
        entries = []
        for g in games_list:
            # The NBA pre-schedules "if necessary" playoff slots; these phantom entries
            # carry "TBD" as the status text until the game is confirmed.
            if g.get("gameStatusText", "").strip().upper() == "TBD":
                continue
            tipoff_at = datetime.fromisoformat(g["gameTimeUTC"].replace("Z", "+00:00"))
            status_int = g.get("gameStatus", 1)
            state = _GAME_STATUS_MAP.get(status_int, "scheduled")
            home_score = g["homeTeam"].get("score") if status_int in (2, 3) else None
            away_score = g["awayTeam"].get("score") if status_int in (2, 3) else None
            period = g.get("period") if status_int in (2, 3) else None
            game_clock = g.get("gameClock") if status_int == 2 else None
            entries.append(
                LiveScoreboardEntry(
                    id=g["gameId"],
                    home_team_id=g["homeTeam"]["teamId"],
                    away_team_id=g["awayTeam"]["teamId"],
                    home_score=home_score,
                    away_score=away_score,
                    period=period,
                    game_clock=game_clock,
                    game_status_text=g.get("gameStatusText", ""),
                    tipoff_at=tipoff_at,
                    state=state,
                )
            )
        last_updated_at = datetime.now(timezone.utc)
        response = LiveScoreboardResponse(
            games=entries,
            last_updated_at=last_updated_at,
            is_stale=False,
        )
        ttl = _bulk_ttl(data)
        _live_cache.set("today", response, ttl)
        logger.info("live_cache_miss_refetched", key="today", ttl=ttl)
        return response
    except Exception as e:
        logger.warning("live_upstream_failed", endpoint="bulk", error=str(e))
        stale = _live_cache.get_stale("today")
        if stale is None:
            raise HTTPException(status_code=503, detail="Live data unavailable")
        value, last_updated_at_epoch = stale
        stale_response = value.model_copy(
            update={
                "is_stale": True,
                "last_updated_at": datetime.fromtimestamp(
                    last_updated_at_epoch, tz=timezone.utc
                ),
            }
        )
        logger.warning(
            "live_serving_stale",
            key="today",
            age_seconds=datetime.now(timezone.utc).timestamp() - last_updated_at_epoch,
        )
        return stale_response


@router.get("/games/live/{game_id}", response_model=GameLive)
@limiter.limit("30/minute")
async def get_live_game(request: Request, game_id: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Game)
        .where(Game.id == game_id)
        .options(
            selectinload(Game.home_team).selectinload(Team.standing),
            selectinload(Game.home_team).selectinload(Team.season_averages),
            selectinload(Game.away_team).selectinload(Team.standing),
            selectinload(Game.away_team).selectinload(Team.season_averages),
            selectinload(Game.playoff_metadata),
        )
    )
    game = (await db.execute(stmt)).scalar_one_or_none()
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found.")
    if game.status == Game.COMPLETED_STATUS:
        raise HTTPException(
            status_code=409,
            detail="Game is final; use /games/{game_id}",
        )
    now = datetime.now(timezone.utc)
    tipoff = (
        game.tipoff_at.replace(tzinfo=timezone.utc)
        if game.tipoff_at.tzinfo is None
        else game.tipoff_at
    )
    if now < tipoff:
        raise HTTPException(
            status_code=409,
            detail="Game has not started; use /games/{game_id}",
        )

    cache_key = f"game:{game_id}"
    cached = _live_cache.get_fresh(cache_key)
    if cached is not None:
        logger.info("live_cache_hit", key=cache_key)
        return cached

    try:
        # Env-gate: when NBAJINNI_LIVE_FIXTURE_DIR is set, load a canned JSON file
        # instead of calling the real NBA API. Used for local dev simulation.
        # NBAResponse.get_dict() calls json.loads(self._response), so we provide a
        # minimal stand-in whose get_dict() returns the fixture dict directly.
        if fixture_dir := os.getenv("NBAJINNI_LIVE_FIXTURE_DIR"):
            fixture_path = Path(fixture_dir) / f"{game_id}.json"
            logger.info("live_using_fixture", game_id=game_id, path=str(fixture_path))
            data = json.loads(fixture_path.read_text())
            box = BoxScore.__new__(BoxScore)
            box.nba_response = type(
                "_FixtureResponse", (), {"get_dict": lambda self: data}
            )()
            box.load_response()
        else:
            box = await asyncio.to_thread(BoxScore, game_id, headers=_LIVE_HEADERS)
        game_info = box.game.get_dict()
        home_team_dict = box.home_team.get_dict()
        away_team_dict = box.away_team.get_dict()
        home_players = box.home_team_player_stats.get_dict()
        away_players = box.away_team_player_stats.get_dict()

        is_final = game_info.get("gameStatus") == 3
        home_score = home_team_dict.get("score", 0)
        away_score = away_team_dict.get("score", 0)
        home_team_stat = _build_live_team_stat(
            team_stats=home_team_dict.get("statistics", {}),
            game_id=game.id,
            team_id=game.home_team_id,
            season=game.season,
            own_points=home_score,
            opp_points=away_score,
        )
        away_team_stat = _build_live_team_stat(
            team_stats=away_team_dict.get("statistics", {}),
            game_id=game.id,
            team_id=game.away_team_id,
            season=game.season,
            own_points=away_score,
            opp_points=home_score,
        )

        last_updated_at = datetime.now(timezone.utc)
        response = GameLive(
            id=game_info["gameId"],
            home_team=game.home_team,
            away_team=game.away_team,
            home_score=home_score,
            away_score=away_score,
            period=game_info.get("period", 0),
            game_clock=game_info.get("gameClock", ""),
            game_status_text=game_info.get("gameStatusText", ""),
            home_player_stats=[_build_player_stat(p) for p in home_players],
            away_player_stats=[_build_player_stat(p) for p in away_players],
            home_team_stat=home_team_stat,
            away_team_stat=away_team_stat,
            last_updated_at=last_updated_at,
            is_stale=False,
            playoff_metadata=game.playoff_metadata,
            is_final=is_final,
        )
        ttl = _per_game_ttl(box)
        _live_cache.set(cache_key, response, ttl)
        logger.info("live_cache_miss_refetched", key=cache_key, ttl=ttl)
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(
            "live_upstream_failed", endpoint="per_game", error=str(e), game_id=game_id
        )
        stale = _live_cache.get_stale(cache_key)
        if stale is None:
            raise HTTPException(status_code=503, detail="Live data unavailable")
        value, last_updated_at_epoch = stale
        stale_response = value.model_copy(
            update={
                "is_stale": True,
                "last_updated_at": datetime.fromtimestamp(
                    last_updated_at_epoch, tz=timezone.utc
                ),
            }
        )
        logger.warning(
            "live_serving_stale",
            key=cache_key,
            age_seconds=datetime.now(timezone.utc).timestamp() - last_updated_at_epoch,
        )
        return stale_response


@router.get("/games/{game_id}/playerstats", response_model=list[PlayerGameStatWithName])
async def get_game_player_stats(game_id: str, db: AsyncSession = Depends(get_db)):
    game_exists = await db.scalar(select(Game.id).where(Game.id == game_id))
    if game_exists is None:
        raise HTTPException(status_code=404, detail="Game not found.")

    stmt = (
        select(PlayerGameStat)
        .where(PlayerGameStat.game_id == game_id)
        .options(selectinload(PlayerGameStat.player))
        .order_by(PlayerGameStat.team_id, PlayerGameStat.points.desc())
    )

    rows = (await db.execute(stmt)).scalars().all()
    stats = []
    for pgs in rows:
        base = PlayerGameStatBase.model_validate(pgs).model_dump()
        base["first_name"] = pgs.player.first_name
        base["last_name"] = pgs.player.last_name
        stats.append(PlayerGameStatWithName.model_validate(base))
    return stats


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
                selectinload(Game.playoff_metadata),
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
            selectinload(Game.playoff_metadata),
        )
    )
    game = (await db.execute(stmt)).scalar_one()
    return GamePreview.model_validate(game)
