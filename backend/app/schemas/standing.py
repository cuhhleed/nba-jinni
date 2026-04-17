from pydantic import BaseModel, ConfigDict

class StandingBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    season: str
    team_id: int
    conference: str
    conference_rank: int
    wins: int
    wins_home: int
    wins_away: int
    losses: int
    losses_home: int
    losses_away: int
    win_pct: float
    games_behind: float
    win_L10: int
    loss_L10: int
    streak: int
    points_pg: float
    opp_points_pg: float