from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import ForeignKey
from datetime import date
from nbajinni_shared.base import Base

class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    home_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"),index=True)
    away_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)
    season_year: Mapped[int] = mapped_column(ForeignKey("seasons.year"))
    game_date: Mapped[date] = mapped_column(index=True)
    status: Mapped[int] = mapped_column()