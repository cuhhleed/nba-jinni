from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import Optional

class PlayerBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    birth_date: Optional[date]

class PlayerWithTeam(PlayerBase):
    team: "TeamBase"

class PlayerDetail(PlayerBase):
    team: "TeamBase"
    game_stats: list["PlayerGameStatBase"]
    season_averages: list["PlayerSeasonAverageBase"]

from .team import TeamBase
from .player_game_stat import PlayerGameStatBase
from .player_season_average import PlayerSeasonAverageBase

PlayerWithTeam.model_rebuild()
PlayerDetail.model_rebuild()