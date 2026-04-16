from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column, relationship
from nbajinni_shared.base import Base
from typing import Optional

class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column()
    nickname: Mapped[str] = mapped_column()
    code: Mapped[str] = mapped_column()
    conference: Mapped[Optional[str]] = mapped_column()
    logo: Mapped[Optional[str]] = mapped_column()

    # relationship for bi-directionality
    players: Mapped[list["Player"]] = relationship("Player", back_populates="team")
    game_stats: Mapped[list["TeamGameStat"]] = relationship("TeamGameStat", back_populates="team")
    season_averages: Mapped[list["TeamSeasonAverage"]] = relationship("TeamSeasonAverage", back_populates="team")
    standing: Mapped["Standing"] = relationship("Standing", back_populates="team")
    home_games: Mapped[list["Game"]] = relationship("Game", foreign_keys="[Game.home_team_id]", back_populates="home_team")
    away_games: Mapped[list["Game"]] = relationship("Game", foreign_keys="[Game.away_team_id]", back_populates="away_team")