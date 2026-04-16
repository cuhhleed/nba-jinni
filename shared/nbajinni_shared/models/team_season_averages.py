from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy import ForeignKey
from sqlalchemy import Numeric
from sqlalchemy import UniqueConstraint
from nbajinni_shared.base import Base

class TeamSeasonAverage(Base):
    __tablename__ = "team_season_averages"
    __table_args__ = (UniqueConstraint("team_id", "season"),)

    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), primary_key=True)
    season: Mapped[str] = mapped_column(ForeignKey("seasons.season"), primary_key=True)
    games_played: Mapped[int] = mapped_column()
    points: Mapped[float] = mapped_column(Numeric(5, 1))
    opponent_points: Mapped[float] = mapped_column(Numeric(5, 1))
    rebounds: Mapped[float] = mapped_column(Numeric(5, 1))
    assists: Mapped[float] = mapped_column(Numeric(5, 1))
    steals: Mapped[float] = mapped_column(Numeric(5, 1))
    blocks: Mapped[float] = mapped_column(Numeric(5, 1))
    turnovers: Mapped[float] = mapped_column(Numeric(5, 1))
    fg_pct: Mapped[float] = mapped_column(Numeric(5, 3))
    three_pct: Mapped[float] = mapped_column(Numeric(5, 3))
    ft_pct: Mapped[float] = mapped_column(Numeric(5, 3))

    # relationship for bi-directionality
    team: Mapped["Team"] = relationship("Team", back_populates="season_averages")