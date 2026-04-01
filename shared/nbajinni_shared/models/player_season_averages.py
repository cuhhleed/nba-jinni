from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import ForeignKey
from sqlalchemy import Numeric
from sqlalchemy import UniqueConstraint
from nbajinni_shared.base import Base

class PlayerSeasonAverage(Base):
    __tablename__ = "player_season_averages"
    __table_args__ = (UniqueConstraint("player_id", "season"),)

    season: Mapped[str] = mapped_column(ForeignKey("seasons.season"), primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    games_played: Mapped[int] = mapped_column()
    min_pg: Mapped[float] = mapped_column(Numeric(5, 2))
    points_pg: Mapped[float] = mapped_column(Numeric(5, 2))
    fgm_pg: Mapped[float] = mapped_column(Numeric(5, 2))
    fga_pg: Mapped[float] = mapped_column(Numeric(5, 2))
    ftm_pg: Mapped[float] = mapped_column(Numeric(5, 2))
    fta_pg: Mapped[float] = mapped_column(Numeric(5, 2))
    tpm_pg: Mapped[float] = mapped_column(Numeric(5, 2))
    tpa_pg: Mapped[float] = mapped_column(Numeric(5, 2))
    off_reb_pg: Mapped[float] = mapped_column(Numeric(5, 2))
    def_reb_pg: Mapped[float] = mapped_column(Numeric(5, 2))
    tot_reb_pg: Mapped[float] = mapped_column(Numeric(5, 2))
    asts_pg: Mapped[float] = mapped_column(Numeric(5, 2))
    stls_pg: Mapped[float] = mapped_column(Numeric(5, 2))
    blks_pg: Mapped[float] = mapped_column(Numeric(5, 2))
    tos_pg: Mapped[float] = mapped_column(Numeric(5, 2))
    pfs_pg: Mapped[float] = mapped_column(Numeric(5, 2))
    fgp: Mapped[float] = mapped_column(Numeric(5, 2))
    ftp: Mapped[float] = mapped_column(Numeric(5, 2))
    tpp: Mapped[float] = mapped_column(Numeric(5, 2))
    plus_minus_pg: Mapped[float] = mapped_column(Numeric(5, 2))