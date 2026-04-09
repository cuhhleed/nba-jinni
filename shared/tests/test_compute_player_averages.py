from sqlalchemy import select, func

from nbajinni_shared.utils import compute_player_averages
from nbajinni_shared.models.player_season_averages import PlayerSeasonAverage
from nbajinni_shared.models.player_game_stats import PlayerGameStat
from nbajinni_shared.models.games import Game
from datetime import date


async def _expected_player_averages(session, season, player_id):
    """Query the expected averages directly using func.avg rounded to 2dp,
    matching the Numeric(5,2) DB storage of PlayerSeasonAverage."""
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
        .where(PlayerGameStat.season == season, PlayerGameStat.player_id == player_id)
    )
    return result.one()


async def test_first_time_insert(
    session, test_player_game_stat, test_second_player_game_stat
):
    result = await compute_player_averages("2024-25", session)

    assert result == 1

    rows = (await session.execute(select(PlayerSeasonAverage))).scalars().all()
    assert len(rows) == 1

    avg = rows[0]
    expected = await _expected_player_averages(session, "2024-25", test_player_game_stat.player_id)

    assert avg.player_id == test_player_game_stat.player_id
    assert avg.season == "2024-25"
    assert avg.games_played == expected.games_played
    assert avg.min_pg == expected.min_pg
    assert avg.points_pg == expected.points_pg
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
    session, test_player_season_average, test_player_game_stat, test_second_player_game_stat
):
    stale_points_pg = test_player_season_average.points_pg

    result = await compute_player_averages("2024-25", session)

    assert result == 1

    rows = (await session.execute(select(PlayerSeasonAverage))).scalars().all()
    assert len(rows) == 1

    await session.refresh(test_player_season_average)
    avg = rows[0]
    expected = await _expected_player_averages(session, "2024-25", test_player_game_stat.player_id)

    assert avg.games_played == expected.games_played
    assert avg.points_pg == expected.points_pg
    assert avg.points_pg != stale_points_pg


async def test_excludes_other_season(
    session, test_season, test_second_season, test_home_team, test_away_team,
    test_player, test_player_game_stat, test_second_player_game_stat
):
    other_game = Game(
        id="0022200001",
        home_team_id=test_home_team.id,
        away_team_id=test_away_team.id,
        game_date=date(2023, 10, 1),
        season="2023-24",
        status=3,
    )
    session.add(other_game)
    await session.flush()

    other_stat = PlayerGameStat(
        game_id=other_game.id,
        player_id=test_player.id,
        season="2023-24",
        team_id=test_home_team.id,
        pos="SF",
        min=40,
        points=50,
        fgm=20,
        fga=30,
        ftm=8,
        fta=10,
        tpm=2,
        tpa=4,
        off_reb=5,
        def_reb=10,
        tot_reb=15,
        asts=12,
        stls=4,
        blks=3,
        tos=1,
        pfs=1,
        fgp=66.67,
        ftp=80.00,
        tpp=50.00,
        plus_minus=20,
    )
    session.add(other_stat)
    await session.flush()

    result = await compute_player_averages("2024-25", session)

    assert result == 1

    rows = (await session.execute(select(PlayerSeasonAverage))).scalars().all()
    assert len(rows) == 1

    avg = rows[0]
    expected = await _expected_player_averages(session, "2024-25", test_player.id)

    assert avg.season == "2024-25"
    assert avg.games_played == expected.games_played
    assert avg.points_pg == expected.points_pg


async def test_traded_player(
    session, test_season, test_home_team, test_away_team,
    test_player, test_game, test_second_game
):
    stat_team_a = PlayerGameStat(
        game_id=test_game.id,
        player_id=test_player.id,
        season=test_season.season,
        team_id=test_home_team.id,
        pos="SF",
        min=30,
        points=20,
        fgm=8,
        fga=15,
        ftm=3,
        fta=4,
        tpm=1,
        tpa=3,
        off_reb=2,
        def_reb=5,
        tot_reb=7,
        asts=6,
        stls=1,
        blks=1,
        tos=2,
        pfs=2,
        fgp=53.33,
        ftp=75.00,
        tpp=33.33,
        plus_minus=5,
    )

    stat_team_b = PlayerGameStat(
        game_id=test_second_game.id,
        player_id=test_player.id,
        season=test_season.season,
        team_id=test_away_team.id,
        pos="SF",
        min=28,
        points=18,
        fgm=7,
        fga=14,
        ftm=3,
        fta=5,
        tpm=1,
        tpa=4,
        off_reb=1,
        def_reb=4,
        tot_reb=5,
        asts=8,
        stls=2,
        blks=0,
        tos=3,
        pfs=3,
        fgp=50.00,
        ftp=60.00,
        tpp=25.00,
        plus_minus=-2,
    )

    session.add_all([stat_team_a, stat_team_b])
    await session.flush()

    result = await compute_player_averages(test_season.season, session)

    assert result == 1

    rows = (await session.execute(select(PlayerSeasonAverage))).scalars().all()
    assert len(rows) == 1

    avg = rows[0]
    expected = await _expected_player_averages(session, test_season.season, test_player.id)

    assert avg.games_played == expected.games_played
    assert avg.points_pg == expected.points_pg
    assert avg.asts_pg == expected.asts_pg


async def test_empty_season(session, test_season):
    result = await compute_player_averages("2024-25", session)

    assert result == 0

    rows = (await session.execute(select(PlayerSeasonAverage))).scalars().all()
    assert len(rows) == 0


async def test_multiple_players(
    session, test_player_game_stat, test_second_player_game_stat,
    test_second_player_first_game_stat
):
    result = await compute_player_averages("2024-25", session)

    assert result == 2

    rows = (await session.execute(
        select(PlayerSeasonAverage).order_by(PlayerSeasonAverage.player_id)
    )).scalars().all()
    assert len(rows) == 2

    lebron_expected = await _expected_player_averages(session, "2024-25", test_player_game_stat.player_id)
    lebron_avg = rows[0]
    assert lebron_avg.player_id == test_player_game_stat.player_id
    assert lebron_avg.games_played == lebron_expected.games_played
    assert lebron_avg.points_pg == lebron_expected.points_pg

    kyrie_expected = await _expected_player_averages(session, "2024-25", test_second_player_first_game_stat.player_id)
    kyrie_avg = rows[1]
    assert kyrie_avg.player_id == test_second_player_first_game_stat.player_id
    assert kyrie_avg.games_played == kyrie_expected.games_played
    assert kyrie_avg.points_pg == kyrie_expected.points_pg
