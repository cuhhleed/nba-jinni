from pydantic import BaseModel, ConfigDict

class PlayerSeasonAverageBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    season: str
    player_id: int
    games_played: int
    min_pg: float
    points_pg: float
    fgm_pg: float
    fga_pg: float
    ftm_pg: float
    fta_pg: float
    tpm_pg: float
    tpa_pg: float
    off_reb_pg: float
    def_reb_pg: float
    tot_reb_pg: float
    asts_pg: float
    stls_pg: float
    blks_pg: float
    tos_pg: float
    pfs_pg: float
    fgp: float
    ftp: float
    tpp: float
    plus_minus_pg: float