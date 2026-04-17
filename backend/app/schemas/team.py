from pydantic import BaseModel, ConfigDict
from typing import Optional

class TeamBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    nickname: str
    code: str
    conference: Optional[str]
    logo: Optional[str]

class TeamDetail(TeamBase):
    standing: "StandingBase"
    season_averages: list["TeamSeasonAverageBase"]
    players: list["PlayerBase"]

class TeamWithSeasonAverage(TeamBase):
    season_averages: list["TeamSeasonAverageBase"]

class TeamWithGames(TeamBase):
    home_games: list["GameBase"]
    away_games: list["GameBase"]

from .player import PlayerBase
from .standing import StandingBase
from .team_season_average import TeamSeasonAverageBase
from .game import GameBase

TeamDetail.model_rebuild()
TeamSeasonAverageBase.model_rebuild()
TeamWithGames.model_rebuild()

