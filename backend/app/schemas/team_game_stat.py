from pydantic import BaseModel, ConfigDict

class TeamGameStatBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    game_id: str
    team_id: int
    season: str
    points: int
    opponent_points: int
    rebounds: int
    assists: int
    steals: int
    blocks: int
    turnovers: int
    fg_pct: float
    three_pct: float
    ft_pct: float