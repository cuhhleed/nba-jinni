from pydantic import BaseModel, ConfigDict

class TeamSeasonAverageBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    team_id: int
    season: str
    games_played: int
    points: float
    opponent_points: float
    rebounds: float
    assists: float
    steals: float
    blocks: float
    turnovers: float
    fg_pct: float
    three_pct: float
    ft_pct: float