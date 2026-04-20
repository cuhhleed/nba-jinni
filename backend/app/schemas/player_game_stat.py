from pydantic import BaseModel, ConfigDict

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