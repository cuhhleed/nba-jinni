"""Seed a dummy playoff game + metadata into the dev DB for local simulation.

Usage (run from scripts/):
    # Insert a live in-progress playoff game (gameStatus=2 in fixture)
    poetry run python dev/seed_dummy_playoff_game.py --state live

    # Insert a finished-uningested playoff game (gameStatus=3 in fixture)
    poetry run python dev/seed_dummy_playoff_game.py --state final

The script inserts (or upserts) a Game row with game_type="playoff" and a
corresponding PlayoffGameMetadata row. The DB status is kept at 1 (not yet
ingested as completed) so the /games/live/{game_id} endpoint will serve it.

Combine with the NBAJINNI_LIVE_FIXTURE_DIR env var to override the NBA API:
    NBAJINNI_LIVE_FIXTURE_DIR=scripts/dev/fixtures poetry run uvicorn app.main:app

Prerequisites: DATABASE_URL must be resolvable in the environment.
"""
import argparse
import asyncio
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from nbajinni_shared.models.games import Game
from nbajinni_shared.models.playoff_game_metadata import PlayoffGameMetadata
from nbajinni_shared.models.standings import Standing
from nbajinni_shared.session import get_session_factory

# ── Constants ──────────────────────────────────────────────────────────────────

# Game ID must match the fixture filename (e.g. PLAYOFF001.json).
GAME_ID = "PLAYOFF001"
HOME_TEAM_ID = 1610612747  # LAL
AWAY_TEAM_ID = 1610612738  # BOS
FALLBACK_SEASON = "2024-25"
FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _build_game(state: str, season: str) -> Game:
    """Return an unsaved Game ORM instance for the requested state."""
    # tipoff_at in the past so the /games/live/ guard does not reject the request.
    tipoff = datetime.now(timezone.utc) - timedelta(hours=2)
    return Game(
        id=GAME_ID,
        home_team_id=HOME_TEAM_ID,
        away_team_id=AWAY_TEAM_ID,
        game_date=tipoff.date(),
        tipoff_at=tipoff.replace(tzinfo=None),  # stored as naive UTC
        season=season,
        status=1,   # NOT 3 — keeps the game in live territory
        game_type="playoff",
    )


def _build_metadata() -> PlayoffGameMetadata:
    """Return an unsaved PlayoffGameMetadata ORM instance."""
    return PlayoffGameMetadata(
        game_id=GAME_ID,
        round_label="First Round",
        series_game_number=3,
        series_record="Series tied 1-1",
    )


def _build_standing(team_id: int, season: str, conference: str, wins: int, losses: int) -> Standing:
    """Return a synthetic Standing row used only when the dev DB has none for this team+season."""
    total = wins + losses
    return Standing(
        season=season,
        team_id=team_id,
        conference=conference,
        conference_rank=1,
        wins=wins,
        wins_home=wins // 2,
        wins_away=wins - wins // 2,
        losses=losses,
        losses_home=losses // 2,
        losses_away=losses - losses // 2,
        win_pct=round(wins / total, 2) if total else 0.0,
        games_behind=0.0,
        win_L10=min(wins, 7),
        loss_L10=min(losses, 3),
        streak=1,
        points_pg=112.0,
        opp_points_pg=108.0,
    )


async def _ensure_standing(session: AsyncSession, team_id: int, season: str, conference: str, wins: int, losses: int) -> None:
    """Insert a synthetic Standing row for (team_id, season) when one does not exist."""
    existing = await session.scalar(
        select(Standing.team_id).where(Standing.team_id == team_id, Standing.season == season)
    )
    if existing is None:
        session.add(_build_standing(team_id, season, conference, wins, losses))


async def _seed(state: str) -> None:
    fixture_file = FIXTURE_DIR / f"{'live' if state == 'live' else 'final'}_playoff_game.json"
    if not fixture_file.exists():
        raise FileNotFoundError(
            f"Fixture not found: {fixture_file}\n"
            "Expected files: live_playoff_game.json, final_playoff_game.json"
        )

    session_factory = get_session_factory()
    async with session_factory() as session:
        async with session.begin():
            # Use the DB's current season (the one Team.standing resolves against)
            # so the banner W–L shows the standings we insert below.
            current_season = await session.scalar(select(func.max(Standing.season)))
            season = current_season or FALLBACK_SEASON

            # Delete existing rows so the script is idempotent.
            await session.execute(
                text("DELETE FROM playoff_game_metadata WHERE game_id = :gid"),
                {"gid": GAME_ID},
            )
            await session.execute(
                text("DELETE FROM games WHERE id = :gid"),
                {"gid": GAME_ID},
            )

            # Ensure standings exist for both teams in the current season — this is
            # what GameBanner reads via Team.standing to render the W–L badge.
            await _ensure_standing(session, HOME_TEAM_ID, season, "West", wins=52, losses=30)
            await _ensure_standing(session, AWAY_TEAM_ID, season, "East", wins=58, losses=24)

            session.add(_build_game(state, season))
            await session.flush()  # FK satisfied before metadata insert
            session.add(_build_metadata())

    # The env-gate in get_live_game looks up fixtures by `{game_id}.json`.
    # Copy the state-specific template to that filename so re-seeding swaps states.
    active_fixture = FIXTURE_DIR / f"{GAME_ID}.json"
    shutil.copyfile(fixture_file, active_fixture)

    print(f"Seeded game {GAME_ID!r} in state={state!r}, season={season!r}")
    print(f"Active fixture: {active_fixture} (copied from {fixture_file.name})")
    print(
        "\nTo simulate this game:\n"
        f"  export NBAJINNI_LIVE_FIXTURE_DIR={FIXTURE_DIR.resolve()}\n"
        f"  Then request: GET /games/live/{GAME_ID}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed a dummy playoff game for local dev.")
    parser.add_argument(
        "--state",
        choices=["live", "final"],
        default="live",
        help=(
            "'live'  → gameStatus=2 in fixture, game in progress. "
            "'final' → gameStatus=3 in fixture, finished but not yet ingested."
        ),
    )
    args = parser.parse_args()
    asyncio.run(_seed(args.state))


if __name__ == "__main__":
    main()
