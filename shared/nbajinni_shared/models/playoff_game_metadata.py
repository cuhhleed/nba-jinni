from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy import ForeignKey
from nbajinni_shared.base import Base

if TYPE_CHECKING:
    from nbajinni_shared.models.games import Game


class PlayoffGameMetadata(Base):
    __tablename__ = "playoff_game_metadata"

    game_id: Mapped[str] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), primary_key=True)
    round: Mapped[int] = mapped_column()
    series_game_number: Mapped[int] = mapped_column()
    series_record: Mapped[str] = mapped_column()

    game: Mapped["Game"] = relationship("Game", back_populates="playoff_metadata")
