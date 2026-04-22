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
    # Trimmed to base + team only. Dedicated endpoints exist for game_stats and
    # season_averages so eager-loading all of them here is unnecessary.
    team: "TeamBase"

from .team import TeamBase

PlayerWithTeam.model_rebuild()
PlayerDetail.model_rebuild()