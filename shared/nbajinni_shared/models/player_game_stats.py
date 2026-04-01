from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import ForeignKey
from sqlalchemy import Numeric
from nbajinni_shared.base import Base

class PlayerGameStat(Base):
    __tablename__ = "player_game_stats"

    game_id: Mapped[str] = mapped_column(ForeignKey("games.id"), primary_key=True, index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), primary_key=True)
    season: Mapped[str] = mapped_column(ForeignKey("seasons.season"), index=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)
    pos: Mapped[str] = mapped_column()
    min: Mapped[int] = mapped_column()
    points: Mapped[int] = mapped_column()
    fgm: Mapped[int] = mapped_column()
    fga: Mapped[int] = mapped_column()
    ftm: Mapped[int] = mapped_column()
    fta: Mapped[int] = mapped_column()
    tpm: Mapped[int] = mapped_column()
    tpa: Mapped[int] = mapped_column()
    off_reb: Mapped[int] = mapped_column()
    def_reb: Mapped[int] = mapped_column()
    tot_reb: Mapped[int] = mapped_column()
    asts: Mapped[int] = mapped_column()
    stls: Mapped[int] = mapped_column()
    blks: Mapped[int] = mapped_column()
    tos: Mapped[int] = mapped_column()
    pfs: Mapped[int] = mapped_column()
    fgp: Mapped[float] = mapped_column(Numeric(5, 2))
    ftp: Mapped[float] = mapped_column(Numeric(5, 2))
    tpp: Mapped[float] = mapped_column(Numeric(5, 2))
    plus_minus: Mapped[int] = mapped_column()