from pydantic import BaseModel, ConfigDict
from datetime import date


class PlayerGameStatBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    game_id: str
    player_id: int
    season: str
    team_id: int
    pos: str
    min: int
    points: int
    fgm: int
    fga: int
    ftm: int
    fta: int
    tpm: int
    tpa: int
    off_reb: int
    def_reb: int
    tot_reb: int
    asts: int
    stls: int
    blks: int
    tos: int
    pfs: int
    fgp: float
    ftp: float
    tpp: float
    plus_minus: int


class PlayerGameStatWithContext(PlayerGameStatBase):
    """
    Extends PlayerGameStatBase with game-level context fields that are not stored
    on PlayerGameStat directly but are resolved from the joined Game row:
    - game_date: populated from Game.game_date in the handler query
    - opponent_team_id: whichever of Game.home_team_id / Game.away_team_id
      does not equal PlayerGameStat.team_id
    """

    game_date: date
    opponent_team_id: int