from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy import select, func, and_
from sqlalchemy.orm import foreign
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
    home_games: Mapped[list["Game"]] = relationship("Game", foreign_keys="[Game.home_team_id]", back_populates="home_team")
    away_games: Mapped[list["Game"]] = relationship("Game", foreign_keys="[Game.away_team_id]", back_populates="away_team")


def _configure_team_standing_relationship() -> None:
    """
    Defines Team.standing as a viewonly, scalar relationship scoped to the
    current season via a correlated subquery on max(Standing.season).

    This is defined as a post-class function rather than inline in Team because
    the primaryjoin uses Python expression objects that require Standing to be
    fully mapped first. Calling this function after both Team and Standing are
    imported avoids forward-reference issues while keeping the expression
    type-safe.

    The correlated subquery `select(func.max(Standing.season)).scalar_subquery()`
    picks the lexicographically largest season string (e.g. "2024-25" > "2023-24"),
    which is equivalent to the most recent season for the NBA season format.
    """
    from nbajinni_shared.models.standings import Standing  # local import avoids circularity

    current_season_subquery = select(func.max(Standing.season)).scalar_subquery()

    Team.standing = relationship(  # type: ignore[attr-defined]
        Standing,
        primaryjoin=and_(
            Team.id == foreign(Standing.team_id),
            Standing.season == current_season_subquery,
        ),
        uselist=False,
        viewonly=True,
    )


_configure_team_standing_relationship()