from datetime import datetime
import asyncio
from nba_api.stats.endpoints import CommonAllPlayers

def get_current_season() -> str:
    now = datetime.now()
    if now.month >= 10:
        return f"{now.year}-{str(now.year + 1)[-2:]}"
    else:
        return f"{now.year - 1}-{str(now.year)[-2:]}"
    
async def get_all_players(season=get_current_season()):
    players = await asyncio.to_thread(CommonAllPlayers, is_only_current_season=1, league_id="00", season=season)
    return players.get_data_frames()[0]

