from sqlalchemy import select, func

from nbajinni_shared.utils import compute_player_playoff_averages
from nbajinni_shared.models.player_playoff_season_averages import PlayerPlayoffSeasonAverage
from nbajinni_shared.models.player_game_stats import PlayerGameStat
from nbajinni_shared.models.games import Game
from datetime import date, datetime


async def _expected_player_averages(session, season, player_id):
    result = await session.execute(
        select(
            func.count(PlayerGameStat.game_id).label("games_played"),
            func.round(func.avg(PlayerGameStat.min), 2).label("min_pg"),
            func.round(func.avg(PlayerGameStat.points), 2).label("points_pg"),
            func.round(func.avg(PlayerGameStat.fgm), 2).label("fgm_pg"),
            func.round(func.avg(PlayerGameStat.fga), 2).label("fga_pg"),
            func.round(func.avg(PlayerGameStat.ftm), 2).label("ftm_pg"),
            func.round(func.avg(PlayerGameStat.fta), 2).label("fta_pg"),
            func.round(func.avg(PlayerGameStat.tpm), 2).label("tpm_pg"),
            func.round(func.avg(PlayerGameStat.tpa), 2).label("tpa_pg"),
            func.round(func.avg(PlayerGameStat.off_reb), 2).label("off_reb_pg"),
            func.round(func.avg(PlayerGameStat.def_reb), 2).label("def_reb_pg"),
            func.round(func.avg(PlayerGameStat.tot_reb), 2).label("tot_reb_pg"),
            func.round(func.avg(PlayerGameStat.asts), 2).label("asts_pg"),
            func.round(func.avg(PlayerGameStat.stls), 2).label("stls_pg"),
            func.round(func.avg(PlayerGameStat.blks), 2).label("blks_pg"),
            func.round(func.avg(PlayerGameStat.tos), 2).label("tos_pg"),
            func.round(func.avg(PlayerGameStat.pfs), 2).label("pfs_pg"),
            func.round(func.avg(PlayerGameStat.fgp), 2).label("fgp"),
            func.round(func.avg(PlayerGameStat.ftp), 2).label("ftp"),
            func.round(func.avg(PlayerGameStat.tpp), 2).label("tpp"),
            func.round(func.avg(PlayerGameStat.plus_minus), 2).label("plus_minus_pg"),
        )
        .where(
            PlayerGameStat.season == season,
            PlayerGameStat.player_id == player_id,
            PlayerGameStat.game_type == "playoff",
        )
    )
    return result.one()


async def test_first_time_insert(
    session, test_season, test_player, test_home_team, test_playoff_game
):
    stat = PlayerGameStat(
        game_id=test_playoff_game.id,
        player_id=test_player.id,
        season=test_season.season,
        team_id=test_home_team.id,
        pos="SF",
        min=38,
        points=28,
        fgm=10,
        fga=19,
        ftm=6,
        fta=8,
        tpm=2,
        tpa=6,
        off_reb=2,
        def_reb=6,
        tot_reb=8,
        asts=8,
        stls=2,
        blks=1,
        tos=2,
        pfs=2,
        fgp=52.63,
        ftp=75.00,
        tpp=33.33,
        plus_minus=10,
        game_type="playoff",
    )
    session.add(stat)
    await session.flush()

    result = await compute_player_playoff_averages(test_season.season, session)

    assert result == 1

    rows = (await session.execute(select(PlayerPlayoffSeasonAverage))).scalars().all()
    assert len(rows) == 1

    avg = rows[0]
    expected = await _expected_player_averages(session, test_season.season, test_player.id)

    assert avg.player_id == test_player.id
    assert avg.season == test_season.season
    assert avg.games_played == expected.games_played
    assert avg.points_pg == expected.points_pg
    assert avg.min_pg == expected.min_pg
    assert avg.fgm_pg == expected.fgm_pg
    assert avg.fga_pg == expected.fga_pg
    assert avg.ftm_pg == expected.ftm_pg
    assert avg.fta_pg == expected.fta_pg
    assert avg.tpm_pg == expected.tpm_pg
    assert avg.tpa_pg == expected.tpa_pg
    assert avg.off_reb_pg == expected.off_reb_pg
    assert avg.def_reb_pg == expected.def_reb_pg
    assert avg.tot_reb_pg == expected.tot_reb_pg
    assert avg.asts_pg == expected.asts_pg
    assert avg.stls_pg == expected.stls_pg
    assert avg.blks_pg == expected.blks_pg
    assert avg.tos_pg == expected.tos_pg
    assert avg.pfs_pg == expected.pfs_pg
    assert avg.fgp == expected.fgp
    assert avg.ftp == expected.ftp
    assert avg.tpp == expected.tpp
    assert avg.plus_minus_pg == expected.plus_minus_pg


async def test_upsert_existing(
    session, test_player_playoff_season_average, test_season, test_player,
    test_home_team, test_playoff_game
):
    stat = PlayerGameStat(
        game_id=test_playoff_game.id,
        player_id=test_player.id,
        season=test_season.season,
        team_id=test_home_team.id,
        pos="SF",
        min=38,
        points=28,
        fgm=10,
        fga=19,
        ftm=6,
        fta=8,
        tpm=2,
        tpa=6,
        off_reb=2,
        def_reb=6,
        tot_reb=8,
        asts=8,
        stls=2,
        blks=1,
        tos=2,
        pfs=2,
        fgp=52.63,
        ftp=75.00,
        tpp=33.33,
        plus_minus=10,
        game_type="playoff",
    )
    session.add(stat)
    await session.flush()

    stale_points_pg = test_player_playoff_season_average.points_pg

    result = await compute_player_playoff_averages(test_season.season, session)

    assert result == 1

    rows = (await session.execute(select(PlayerPlayoffSeasonAverage))).scalars().all()
    assert len(rows) == 1

    await session.refresh(test_player_playoff_season_average)
    avg = rows[0]
    expected = await _expected_player_averages(session, test_season.season, test_player.id)

    assert avg.games_played == expected.games_played
    assert avg.points_pg == expected.points_pg
    assert avg.points_pg != stale_points_pg


async def test_excludes_regular_games(
    session, test_season, test_player, test_home_team, test_game, test_playoff_game
):
    regular_stat = PlayerGameStat(
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
        game_type="regular",
    )
    playoff_stat = PlayerGameStat(
        game_id=test_playoff_game.id,
        player_id=test_player.id,
        season=test_season.season,
        team_id=test_home_team.id,
        pos="SF",
        min=40,
        points=20,
        fgm=8,
        fga=18,
        ftm=3,
        fta=4,
        tpm=1,
        tpa=4,
        off_reb=2,
        def_reb=5,
        tot_reb=7,
        asts=6,
        stls=1,
        blks=1,
        tos=2,
        pfs=2,
        fgp=44.44,
        ftp=75.00,
        tpp=25.00,
        plus_minus=5,
        game_type="playoff",
    )
    session.add_all([regular_stat, playoff_stat])
    await session.flush()

    result = await compute_player_playoff_averages(test_season.season, session)

    assert result == 1

    rows = (await session.execute(select(PlayerPlayoffSeasonAverage))).scalars().all()
    assert len(rows) == 1

    avg = rows[0]
    assert avg.games_played == 1
    assert avg.points_pg == 20


async def test_season_filtering(
    session, test_season, test_second_season, test_player, test_home_team,
    test_away_team, test_playoff_game
):
    other_playoff_game = Game(
        id="0042200001",
        home_team_id=test_home_team.id,
        away_team_id=test_away_team.id,
        game_date=date(2022, 4, 20),
        tipoff_at=datetime(2022, 4, 20, 20, 0),
        season="2023-24",
        status=3,
        game_type="playoff",
    )
    session.add(other_playoff_game)
    await session.flush()

    current_season_stat = PlayerGameStat(
        game_id=test_playoff_game.id,
        player_id=test_player.id,
        season=test_season.season,
        team_id=test_home_team.id,
        pos="SF",
        min=38,
        points=28,
        fgm=10,
        fga=19,
        ftm=6,
        fta=8,
        tpm=2,
        tpa=6,
        off_reb=2,
        def_reb=6,
        tot_reb=8,
        asts=8,
        stls=2,
        blks=1,
        tos=2,
        pfs=2,
        fgp=52.63,
        ftp=75.00,
        tpp=33.33,
        plus_minus=10,
        game_type="playoff",
    )
    other_season_stat = PlayerGameStat(
        game_id=other_playoff_game.id,
        player_id=test_player.id,
        season="2023-24",
        team_id=test_home_team.id,
        pos="SF",
        min=42,
        points=45,
        fgm=18,
        fga=28,
        ftm=7,
        fta=9,
        tpm=2,
        tpa=5,
        off_reb=4,
        def_reb=9,
        tot_reb=13,
        asts=11,
        stls=3,
        blks=2,
        tos=1,
        pfs=1,
        fgp=64.29,
        ftp=77.78,
        tpp=40.00,
        plus_minus=18,
        game_type="playoff",
    )
    session.add_all([current_season_stat, other_season_stat])
    await session.flush()

    result = await compute_player_playoff_averages(test_season.season, session)

    assert result == 1

    rows = (await session.execute(select(PlayerPlayoffSeasonAverage))).scalars().all()
    assert len(rows) == 1

    avg = rows[0]
    assert avg.season == test_season.season
    assert avg.games_played == 1
    assert avg.points_pg == 28


async def test_empty_season(session, test_season):
    result = await compute_player_playoff_averages("2024-25", session)

    assert result == 0

    rows = (await session.execute(select(PlayerPlayoffSeasonAverage))).scalars().all()
    assert len(rows) == 0
