import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from nbajinni_shared.models.teams import Team
from nbajinni_shared.models.players import Player
from nbajinni_shared.models.games import Game
from nbajinni_shared.models.seasons import Season
from nbajinni_shared.models.standings import Standing
from nbajinni_shared.models.player_game_stats import PlayerGameStat
from nbajinni_shared.models.team_game_stats import TeamGameStat
from nbajinni_shared.models.player_season_averages import PlayerSeasonAverage
from nbajinni_shared.models.team_season_averages import TeamSeasonAverage
import os
from datetime import date
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / ".env")


# Session-scoped engine — connection pool created once for the entire test run
@pytest_asyncio.fixture
async def engine():
    engine = create_async_engine(os.getenv("TEST_DATABASE_URL"), pool_size=1, max_overflow=0)
    yield engine
    await engine.dispose()


# Function-scoped connection and session — rolled back after each test
@pytest_asyncio.fixture
async def session(engine):
    async with engine.connect() as connection:
        await connection.begin()
        async_session = AsyncSession(bind=connection, expire_on_commit=False)
        yield async_session
        await connection.rollback()


@pytest_asyncio.fixture
async def test_home_team(session):
    team = Team(id=1610612747, name="Los Angeles Lakers", nickname="Lakers", code="LAL", conference="West")
    session.add(team)
    await session.flush()
    return team


@pytest_asyncio.fixture
async def test_away_team(session):
    team = Team(id=1610612738, name="Boston Celtics", nickname="Celtics", code="BOS", conference="East")
    session.add(team)
    await session.flush()
    return team


@pytest_asyncio.fixture
async def test_player(session, test_home_team):
    player = Player(id=2544, first_name="LeBron", last_name="James", team_id=test_home_team.id)
    session.add(player)
    await session.flush()
    return player

@pytest_asyncio.fixture
async def test_second_player(session, test_away_team):
    player = Player(id=2545, first_name="Kyrie", last_name="Irving", team_id=test_away_team.id)
    session.add(player)
    await session.flush()
    return player


@pytest_asyncio.fixture
async def test_game(session, test_home_team, test_away_team):
    game = Game(id="0022300001", home_team_id=test_home_team.id, away_team_id=test_away_team.id, game_date=date(2024, 10, 1), season="2024-25", status=1)
    session.add(game)
    await session.flush()
    return game

@pytest_asyncio.fixture
async def test_second_game(session, test_home_team, test_away_team):
    game = Game(id="0022300002", home_team_id=test_home_team.id, away_team_id=test_away_team.id, game_date=date(2024, 10, 2), season="2024-25", status=1)
    session.add(game)
    await session.flush()
    return game

@pytest_asyncio.fixture
async def test_future_game(session, test_home_team, test_away_team):
    game = Game(id="0022300003", home_team_id=test_home_team.id, away_team_id=test_away_team.id, game_date=date(2099, 12, 31), season="2024-25", status=1)
    session.add(game)
    await session.flush()
    return game

@pytest_asyncio.fixture
async def test_season(session):
    season = Season(season="2024-25")
    session.add(season)
    await session.flush()
    return season


@pytest_asyncio.fixture
async def test_standing(session, test_season, test_home_team):
    standing = Standing(
        season=test_season.season,
        team_id=test_home_team.id,
        conference="West",
        conference_rank=1,
        wins=40,
        wins_home=22,
        wins_away=18,
        losses=10,
        losses_home=4,
        losses_away=6,
        win_pct=0.80,
        games_behind=0.0,
        win_L10=8,
        loss_L10=2,
        streak=5,
        points_pg=115.5,
        opp_points_pg=108.2,
    )
    session.add(standing)
    await session.flush()
    return standing


@pytest_asyncio.fixture
async def test_away_standing(session, test_season, test_away_team):
    standing = Standing(
        season=test_season.season,
        team_id=test_away_team.id,
        conference="East",
        conference_rank=1,
        wins=38,
        wins_home=20,
        wins_away=18,
        losses=12,
        losses_home=5,
        losses_away=7,
        win_pct=0.76,
        games_behind=0.0,
        win_L10=7,
        loss_L10=3,
        streak=3,
        points_pg=112.0,
        opp_points_pg=105.5,
    )
    session.add(standing)
    await session.flush()
    return standing


@pytest_asyncio.fixture
async def test_second_season(session):
    season = Season(season="2023-24")
    session.add(season)
    await session.flush()
    return season


@pytest_asyncio.fixture
async def test_player_game_stat(session, test_season, test_game, test_player, test_home_team):
    stat = PlayerGameStat(
        game_id=test_game.id,
        player_id=test_player.id,
        season=test_season.season,
        team_id=test_home_team.id,
        pos="SF",
        min=36,
        points=30,
        fgm=11,
        fga=20,
        ftm=6,
        fta=8,
        tpm=2,
        tpa=5,
        off_reb=1,
        def_reb=7,
        tot_reb=8,
        asts=10,
        stls=2,
        blks=1,
        tos=3,
        pfs=2,
        fgp=55.00,
        ftp=75.00,
        tpp=40.00,
        plus_minus=12,
    )
    session.add(stat)
    await session.flush()
    return stat


@pytest_asyncio.fixture
async def test_second_player_game_stat(session, test_season, test_second_game, test_player, test_home_team):
    stat = PlayerGameStat(
        game_id=test_second_game.id,
        player_id=test_player.id,
        season=test_season.season,
        team_id=test_home_team.id,
        pos="SF",
        min=34,
        points=20,
        fgm=7,
        fga=16,
        ftm=4,
        fta=6,
        tpm=2,
        tpa=7,
        off_reb=3,
        def_reb=3,
        tot_reb=6,
        asts=5,
        stls=1,
        blks=2,
        tos=4,
        pfs=3,
        fgp=43.75,
        ftp=66.67,
        tpp=28.57,
        plus_minus=-4,
    )
    session.add(stat)
    await session.flush()
    return stat


@pytest_asyncio.fixture
async def test_second_player_first_game_stat(session, test_season, test_game, test_second_player, test_away_team):
    stat = PlayerGameStat(
        game_id=test_game.id,
        player_id=test_second_player.id,
        season=test_season.season,
        team_id=test_away_team.id,
        pos="PG",
        min=32,
        points=25,
        fgm=9,
        fga=18,
        ftm=5,
        fta=6,
        tpm=2,
        tpa=6,
        off_reb=0,
        def_reb=4,
        tot_reb=4,
        asts=7,
        stls=3,
        blks=0,
        tos=2,
        pfs=1,
        fgp=50.00,
        ftp=83.33,
        tpp=33.33,
        plus_minus=5,
    )
    session.add(stat)
    await session.flush()
    return stat


@pytest_asyncio.fixture
async def test_home_team_game_stat(session, test_season, test_game, test_home_team):
    stat = TeamGameStat(
        game_id=test_game.id,
        team_id=test_home_team.id,
        season=test_season.season,
        points=110,
        opponent_points=102,
        rebounds=45,
        assists=25,
        steals=8,
        blocks=5,
        turnovers=12,
        fg_pct=0.465,
        three_pct=0.380,
        ft_pct=0.810,
    )
    session.add(stat)
    await session.flush()
    return stat


@pytest_asyncio.fixture
async def test_home_team_second_game_stat(session, test_season, test_second_game, test_home_team):
    stat = TeamGameStat(
        game_id=test_second_game.id,
        team_id=test_home_team.id,
        season=test_season.season,
        points=98,
        opponent_points=105,
        rebounds=39,
        assists=20,
        steals=6,
        blocks=3,
        turnovers=15,
        fg_pct=0.425,
        three_pct=0.320,
        ft_pct=0.780,
    )
    session.add(stat)
    await session.flush()
    return stat


@pytest_asyncio.fixture
async def test_away_team_game_stat(session, test_season, test_game, test_away_team):
    stat = TeamGameStat(
        game_id=test_game.id,
        team_id=test_away_team.id,
        season=test_season.season,
        points=102,
        opponent_points=110,
        rebounds=38,
        assists=22,
        steals=7,
        blocks=4,
        turnovers=14,
        fg_pct=0.440,
        three_pct=0.350,
        ft_pct=0.750,
    )
    session.add(stat)
    await session.flush()
    return stat


@pytest_asyncio.fixture
async def test_player_season_average(session, test_season, test_player):
    avg = PlayerSeasonAverage(
        season=test_season.season,
        player_id=test_player.id,
        games_played=1,
        min_pg=10.00,
        points_pg=5.00,
        fgm_pg=2.00,
        fga_pg=5.00,
        ftm_pg=1.00,
        fta_pg=2.00,
        tpm_pg=0.00,
        tpa_pg=1.00,
        off_reb_pg=0.00,
        def_reb_pg=1.00,
        tot_reb_pg=1.00,
        asts_pg=1.00,
        stls_pg=0.00,
        blks_pg=0.00,
        tos_pg=1.00,
        pfs_pg=1.00,
        fgp=40.00,
        ftp=50.00,
        tpp=0.00,
        plus_minus_pg=0.00,
    )
    session.add(avg)
    await session.flush()
    return avg


@pytest_asyncio.fixture
async def test_team_season_average(session, test_season, test_home_team):
    avg = TeamSeasonAverage(
        team_id=test_home_team.id,
        season=test_season.season,
        games_played=1,
        points=80.0,
        opponent_points=85.0,
        rebounds=30.0,
        assists=15.0,
        steals=4.0,
        blocks=2.0,
        turnovers=10.0,
        fg_pct=0.400,
        three_pct=0.300,
        ft_pct=0.700,
    )
    session.add(avg)
    await session.flush()
    return avg