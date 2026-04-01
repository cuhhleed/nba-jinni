from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import ForeignKey
from sqlalchemy import Numeric
from nbajinni_shared.base import Base
from datetime import datetime
from sqlalchemy import func

class Standing(Base):
    __tablename__ = "standings"

    season: Mapped[int] = mapped_column(ForeignKey("seasons.season"), primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), primary_key=True,index=True)
    conference: Mapped[str] = mapped_column()
    conference_rank: Mapped[int] = mapped_column()
    wins: Mapped[int] = mapped_column()
    wins_home: Mapped[int] = mapped_column()
    wins_away: Mapped[int] = mapped_column()
    losses: Mapped[int] = mapped_column()
    losses_home: Mapped[int] = mapped_column()
    losses_away: Mapped[int] = mapped_column()
    win_pct: Mapped[float] = mapped_column(Numeric(5, 2))
    games_behind: Mapped[float] = mapped_column(Numeric(5, 2))
    win_L10: Mapped[int] = mapped_column()
    loss_L10: Mapped[int] = mapped_column()
    streak: Mapped[int] = mapped_column()
    points_pg: Mapped[float] = mapped_column(Numeric(5, 1))
    opp_points_pg: Mapped[float] = mapped_column(Numeric(5, 1))
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())