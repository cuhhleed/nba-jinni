from pydantic import BaseModel, ConfigDict
from datetime import date

class GameBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    home_team_id: int
    away_team_id: int
    season: str
    game_date: date
    status: int


class GameWithTeams(GameBase):
    home_team: "TeamWithSeasonAverage"
    away_team: "TeamWithSeasonAverage"

from .team import TeamWithSeasonAverage
GameWithTeams.model_rebuild()