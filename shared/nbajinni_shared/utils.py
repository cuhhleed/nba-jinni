import asyncio
from datetime import datetime

from nba_api.stats.endpoints import CommonAllPlayers
from nba_api.stats.endpoints import ScheduleLeagueV2
from nba_api.stats.endpoints import BoxScoreTraditionalV3
from nba_api.stats.endpoints import LeagueStandingsV3
from nbajinni_shared.nba_api_wrapper import NbaApiWrapper
from nbajinni_shared.models.player_game_stats import PlayerGameStat
from nbajinni_shared.models.team_game_stats import TeamGameStat
from nbajinni_shared.models.player_season_averages import PlayerSeasonAverage
from nbajinni_shared.models.team_season_averages import TeamSeasonAverage
from nbajinni_shared.models.standings import Standing
from nbajinni_shared.models.games import Game
from nbajinni_shared.models.players import Player
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select, func, exists, update

wrapper = NbaApiWrapper()

def get_current_season() -> str:
    now = datetime.now()
    if now.month >= 10:
        return f"{now.year}-{str(now.year + 1)[-2:]}"
    else:
        return f"{now.year - 1}-{str(now.year)[-2:]}"

current_season = get_current_season()

async def get_all_players(season=current_season):
    return (await asyncio.to_thread(wrapper.call, CommonAllPlayers, is_only_current_season=1, league_id="00", season=season))[0]

async def get_all_games(season=current_season):
    return (await asyncio.to_thread(wrapper.call, ScheduleLeagueV2, league_id="00", season=season))[0]

async def get_game_stats(game_id):
    box_score = await asyncio.to_thread(
        wrapper.call,
        BoxScoreTraditionalV3,
        game_id=game_id,
        start_period=0,
        end_period=0,
        range_type=0,
        start_range=0,
        end_range=0
    )

    if box_score is None:
        return None, None
    
    player_stats = box_score[0]
    team_stats = box_score[2]

    return (player_stats, team_stats)

async def ingest_games(games, session):
    processed_games, processed_player_stats, processed_team_stats = 0, 0, 0

    for game in games:
        game_id = game.id
        player_stats, team_stats = await get_game_stats(game_id)
        
        if player_stats is None:
            continue

        for _, player_stat_row in player_stats.iterrows():
            player_exists = await session.scalar(
                select(exists().where(Player.id == player_stat_row["personId"]))
            )

            if not player_exists:
                continue

            min_floor = int(player_stat_row["minutes"].split(":")[0]) if player_stat_row["minutes"] else 0
            stmt = (
                insert(PlayerGameStat).values(
                    game_id=game_id,
                    player_id=player_stat_row["personId"],
                    season=game.season,
                    team_id=player_stat_row["teamId"],
                    pos=player_stat_row["position"],
                    min=min_floor,
                    points=player_stat_row["points"],
                    fgm=player_stat_row["fieldGoalsMade"],
                    fga=player_stat_row["fieldGoalsAttempted"],
                    fgp=player_stat_row["fieldGoalsPercentage"],
                    ftm=player_stat_row["freeThrowsMade"],
                    fta=player_stat_row["freeThrowsAttempted"],
                    ftp=player_stat_row["freeThrowsPercentage"],
                    tpm=player_stat_row["threePointersMade"],
                    tpa=player_stat_row["threePointersAttempted"],
                    tpp=player_stat_row["threePointersPercentage"],
                    off_reb=player_stat_row["reboundsOffensive"],
                    def_reb=player_stat_row["reboundsDefensive"],
                    tot_reb=player_stat_row["reboundsTotal"],
                    asts=player_stat_row["assists"],
                    stls=player_stat_row["steals"],
                    blks=player_stat_row["blocks"],
                    tos=player_stat_row["turnovers"],
                    pfs=player_stat_row["foulsPersonal"],
                    plus_minus=player_stat_row["plusMinusPoints"]
                ).on_conflict_do_nothing()
            )

            result = await session.execute(stmt)
            if result.rowcount == 1:
                processed_player_stats += 1
        
        for _, team_stat_row in team_stats.iterrows():
            stmt = (
                insert(TeamGameStat).values(
                    game_id=team_stat_row["gameId"],
                    team_id=team_stat_row["teamId"],
                    season=game.season,
                    points=team_stat_row["points"],
                    opponent_points = team_stats[team_stats["teamId"] != team_stat_row["teamId"]]["points"].values[0],
                    rebounds=team_stat_row["reboundsTotal"],
                    assists=team_stat_row["assists"],
                    steals=team_stat_row["steals"],
                    blocks=team_stat_row["blocks"],
                    turnovers=team_stat_row["turnovers"],
                    fg_pct=team_stat_row["fieldGoalsPercentage"],
                    three_pct=team_stat_row["threePointersPercentage"],
                    ft_pct=team_stat_row["freeThrowsPercentage"],
                ).on_conflict_do_nothing()
            )

            result = await session.execute(stmt)
            if result.rowcount == 1:
                processed_team_stats += 1
        
        processed_games += 1
        game.status = 3
    
    return (processed_games, processed_player_stats, processed_team_stats)

async def ingest_standings(session, season):
    processed = 0

    standings = (await asyncio.to_thread(wrapper.call, LeagueStandingsV3, league_id="00", season=season, season_type="Regular Season"))[0]

    for _, standing in standings.iterrows():
        home_record = standing["HOME"].split('-')
        away_record = standing["ROAD"].split('-')
        last_ten_record= standing["L10"].split('-')
        stmt = (
            insert(Standing).values(
                season=season,
                team_id=standing["TeamID"],
                conference=standing["Conference"],
                conference_rank=standing["PlayoffRank"],
                wins=standing["WINS"],
                wins_home=int(home_record[0]),
                wins_away=int(away_record[0]),
                losses=standing["LOSSES"],
                losses_home=int(home_record[1]),
                losses_away=int(away_record[1]),
                win_pct=standing["WinPCT"],
                games_behind=standing["ConferenceGamesBack"],
                win_L10=int(last_ten_record[0]),
                loss_L10=int(last_ten_record[1]),
                streak=standing["CurrentStreak"],
                points_pg=standing["PointsPG"],
                opp_points_pg=standing["OppPointsPG"],
                updated_at=datetime.now()
            )
            .on_conflict_do_update(
                index_elements=["team_id", "season"],
                set_={
                    "conference": standing["Conference"],
                    "conference_rank": standing["PlayoffRank"],
                    "wins": standing["WINS"],
                    "wins_home": int(home_record[0]),
                    "wins_away": int(away_record[0]),
                    "losses": standing["LOSSES"],
                    "losses_home": int(home_record[1]),
                    "losses_away": int(away_record[1]),
                    "win_pct": standing["WinPCT"],
                    "games_behind": standing["ConferenceGamesBack"],
                    "win_L10": int(last_ten_record[0]),
                    "loss_L10": int(last_ten_record[1]),
                    "streak": standing["CurrentStreak"],
                    "points_pg": standing["PointsPG"],
                    "opp_points_pg": standing["OppPointsPG"],
                    "updated_at": datetime.now()
                }
            )
        )

        result = await session.execute(stmt)
        if result.rowcount in (1, 2):
            processed += 1

    return processed

async def ingest_roster(session, season):
    players = await get_all_players(season)
    processed = 0

    await session.execute(update(Player).values(active=False))

    for _, player in players.iterrows():
        if player["TEAM_ID"] == 0:
            continue

        full_name_split = player["DISPLAY_FIRST_LAST"].split(" ")
        first_name = full_name_split[0]
        last_name = " ".join(full_name_split[1:])
        stmt = (
            insert(Player)
            .values(
                id=player["PERSON_ID"],
                first_name=first_name,
                last_name=last_name,
                team_id=player["TEAM_ID"],
                birth_date=None,
            )
            .on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "first_name": first_name,
                    "last_name": last_name,
                    "team_id": player["TEAM_ID"],
                    "birth_date": None,
                    "active": True,
                },
            )
        )
        result = await session.execute(stmt)
        if result.rowcount in (1, 2):
            processed += 1

    return processed

async def ingest_schedule(session, season):
    games = await get_all_games(season)
    processed = 0

    for _, game in games.iterrows():
        if game["gameLabel"]:
            continue

        game_date = datetime.strptime(game["gameDate"], "%m/%d/%Y %H:%M:%S").date()
        stmt = (
            insert(Game)
            .values(
                id=game["gameId"],
                home_team_id=game["homeTeam_teamId"],
                away_team_id=game["awayTeam_teamId"],
                game_date=game_date,
                season=season,
                status=game["gameStatus"]
            )
            .on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "home_team_id": game["homeTeam_teamId"],
                    "away_team_id": game["awayTeam_teamId"],
                    "game_date": game_date
                },
            )
        )
        result = await session.execute(stmt)
        if result.rowcount in (1, 2):
            processed += 1

    return processed

async def compute_player_averages(season, session):
    processed = 0
    # Player averages
    player_avg_query = (
        select(
            PlayerGameStat.player_id,
            func.count(PlayerGameStat.game_id).label("games_played"),
            func.avg(PlayerGameStat.min).label("min_pg"),
            func.avg(PlayerGameStat.points).label("points_pg"),
            func.avg(PlayerGameStat.fgm).label("fgm_pg"),
            func.avg(PlayerGameStat.fga).label("fga_pg"),
            func.avg(PlayerGameStat.ftm).label("ftm_pg"),
            func.avg(PlayerGameStat.fta).label("fta_pg"),
            func.avg(PlayerGameStat.tpm).label("tpm_pg"),
            func.avg(PlayerGameStat.tpa).label("tpa_pg"),
            func.avg(PlayerGameStat.off_reb).label("off_reb_pg"),
            func.avg(PlayerGameStat.def_reb).label("def_reb_pg"),
            func.avg(PlayerGameStat.tot_reb).label("tot_reb_pg"),
            func.avg(PlayerGameStat.asts).label("asts_pg"),
            func.avg(PlayerGameStat.stls).label("stls_pg"),
            func.avg(PlayerGameStat.blks).label("blks_pg"),
            func.avg(PlayerGameStat.tos).label("tos_pg"),
            func.avg(PlayerGameStat.pfs).label("pfs_pg"),
            func.avg(PlayerGameStat.fgp).label("fgp"),
            func.avg(PlayerGameStat.ftp).label("ftp"),
            func.avg(PlayerGameStat.tpp).label("tpp"),
            func.avg(PlayerGameStat.plus_minus).label("plus_minus_pg"),
        )
        .where(PlayerGameStat.season == season)
        .group_by(PlayerGameStat.player_id)
    )

    player_results = await session.execute(player_avg_query)

    for row in player_results:
        stmt = (
            insert(PlayerSeasonAverage)
            .values(
                player_id=row.player_id,
                season=season,
                games_played=row.games_played,
                min_pg=row.min_pg,
                points_pg=row.points_pg,
                fgm_pg=row.fgm_pg,
                fga_pg=row.fga_pg,
                ftm_pg=row.ftm_pg,
                fta_pg=row.fta_pg,
                tpm_pg=row.tpm_pg,
                tpa_pg=row.tpa_pg,
                off_reb_pg=row.off_reb_pg,
                def_reb_pg=row.def_reb_pg,
                tot_reb_pg=row.tot_reb_pg,
                asts_pg=row.asts_pg,
                stls_pg=row.stls_pg,
                blks_pg=row.blks_pg,
                tos_pg=row.tos_pg,
                pfs_pg=row.pfs_pg,
                fgp=row.fgp,
                ftp=row.ftp,
                tpp=row.tpp,
                plus_minus_pg=row.plus_minus_pg,
            )
            .on_conflict_do_update(
                index_elements=["player_id", "season"],
                set_={
                    "games_played": row.games_played,
                    "min_pg": row.min_pg,
                    "points_pg": row.points_pg,
                    "fgm_pg": row.fgm_pg,
                    "fga_pg": row.fga_pg,
                    "ftm_pg": row.ftm_pg,
                    "fta_pg": row.fta_pg,
                    "tpm_pg": row.tpm_pg,
                    "tpa_pg": row.tpa_pg,
                    "off_reb_pg": row.off_reb_pg,
                    "def_reb_pg": row.def_reb_pg,
                    "tot_reb_pg": row.tot_reb_pg,
                    "asts_pg": row.asts_pg,
                    "stls_pg": row.stls_pg,
                    "blks_pg": row.blks_pg,
                    "tos_pg": row.tos_pg,
                    "pfs_pg": row.pfs_pg,
                    "fgp": row.fgp,
                    "ftp": row.ftp,
                    "tpp": row.tpp,
                    "plus_minus_pg": row.plus_minus_pg,
                },
            )
        )

        result = await session.execute(stmt)
        if result.rowcount in (1, 2):
            processed += 1

    return processed

async def compute_team_averages(season, session):
    processed = 0
    # Team averages
    team_avg_query = (
        select(
            TeamGameStat.team_id,
            func.count(TeamGameStat.game_id).label("games_played"),
            func.avg(TeamGameStat.points).label("points"),
            func.avg(TeamGameStat.opponent_points).label("opponent_points"),
            func.avg(TeamGameStat.rebounds).label("rebounds"),
            func.avg(TeamGameStat.assists).label("assists"),
            func.avg(TeamGameStat.steals).label("steals"),
            func.avg(TeamGameStat.blocks).label("blocks"),
            func.avg(TeamGameStat.turnovers).label("turnovers"),
            func.avg(TeamGameStat.fg_pct).label("fg_pct"),
            func.avg(TeamGameStat.three_pct).label("three_pct"),
            func.avg(TeamGameStat.ft_pct).label("ft_pct"),
        )
        .where(TeamGameStat.season == season)
        .group_by(TeamGameStat.team_id)
    )

    team_results = await session.execute(team_avg_query)

    for row in team_results:
        stmt = (
            insert(TeamSeasonAverage)
            .values(
                team_id=row.team_id,
                season=season,
                games_played=row.games_played,
                points=row.points,
                opponent_points=row.opponent_points,
                rebounds=row.rebounds,
                assists=row.assists,
                steals=row.steals,
                blocks=row.blocks,
                turnovers=row.turnovers,
                fg_pct=row.fg_pct,
                three_pct=row.three_pct,
                ft_pct=row.ft_pct,
            )
            .on_conflict_do_update(
                index_elements=["team_id", "season"],
                set_={
                    "games_played": row.games_played,
                    "points": row.points,
                    "opponent_points": row.opponent_points,
                    "rebounds": row.rebounds,
                    "assists": row.assists,
                    "steals": row.steals,
                    "blocks": row.blocks,
                    "turnovers": row.turnovers,
                    "fg_pct": row.fg_pct,
                    "three_pct": row.three_pct,
                    "ft_pct": row.ft_pct,
                },
            )
        )

        result = await session.execute(stmt)
        if result.rowcount in (1, 2):
            processed += 1

    return processed
