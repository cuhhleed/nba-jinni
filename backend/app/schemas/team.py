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

class TeamWithRoster(TeamBase):
    players: list["PlayerBase"]


class TeamDetail(TeamBase):
    standing: "StandingBase"
    season_averages: list["TeamSeasonAverageBase"]

class TeamWithSeasonAverage(TeamBase):
    season_averages: list["TeamSeasonAverageBase"]

class TeamWithGames(TeamBase):
    home_games: list["GameBase"]
    away_games: list["GameBase"]

class TeamWithStandingAndAverage(TeamBase):
    # Used in GamePreview: exposes team identity, current-season standing, and
    # season averages (pre-filtered by the handler to the game's season).
    standing: Optional["StandingBase"]
    season_averages: list["TeamSeasonAverageBase"]

class TeamWithStanding(TeamBase):
    standing: Optional["StandingBase"]

from .player import PlayerBase
from .standing import StandingBase
from .team_season_average import TeamSeasonAverageBase
from .game import GameBase

TeamWithRoster.model_rebuild()
TeamDetail.model_rebuild()
TeamSeasonAverageBase.model_rebuild()
TeamWithGames.model_rebuild()
TeamWithStandingAndAverage.model_rebuild()
TeamWithStanding.model_rebuild()

