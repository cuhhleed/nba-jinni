from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy import ForeignKey
from datetime import date
from nbajinni_shared.base import Base

class Game(Base):
    __tablename__ = "games"

    id: Mapped[str] = mapped_column(primary_key=True)
    home_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)
    away_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)
    season: Mapped[str] = mapped_column(ForeignKey("seasons.season"), index=True)
    game_date: Mapped[date] = mapped_column(index=True)
    status: Mapped[int] = mapped_column()

    # relationships for bi-directionality
    home_team: Mapped["Team"] = relationship("Team", foreign_keys=[home_team_id], back_populates="home_games")
    away_team: Mapped["Team"] = relationship("Team", foreign_keys=[away_team_id], back_populates="away_games")
    player_stats: Mapped[list["PlayerGameStat"]] = relationship("PlayerGameStat", back_populates="game")
    team_stats: Mapped[list["TeamGameStat"]] = relationship("TeamGameStat", back_populates="game")