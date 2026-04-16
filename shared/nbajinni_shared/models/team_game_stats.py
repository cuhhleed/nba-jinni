from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy import ForeignKey
from sqlalchemy import Numeric
from nbajinni_shared.base import Base

class TeamGameStat(Base):
    __tablename__ = "team_game_stats"

    game_id: Mapped[str] = mapped_column(ForeignKey("games.id"), primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), primary_key=True)
    season: Mapped[str] = mapped_column(ForeignKey("seasons.season"), index=True)
    points: Mapped[int] = mapped_column()
    opponent_points: Mapped[int] = mapped_column()
    rebounds: Mapped[int] = mapped_column()
    assists: Mapped[int] = mapped_column()
    steals: Mapped[int] = mapped_column()
    blocks: Mapped[int] = mapped_column()
    turnovers: Mapped[int] = mapped_column()
    fg_pct: Mapped[float] = mapped_column(Numeric(5, 3))
    three_pct: Mapped[float] = mapped_column(Numeric(5, 3))
    ft_pct: Mapped[float] = mapped_column(Numeric(5, 3))

    # relationship for bi-directionality
    team: Mapped["Team"] = relationship("Team", back_populates="game_stats")
    game: Mapped["Game"] = relationship("Game", back_populates="team_stats")