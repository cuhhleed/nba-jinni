from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import ForeignKey
from datetime import date
from nbajinni_shared.base import Base
from typing import Optional

class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    first_name: Mapped[str] = mapped_column()
    last_name: Mapped[str] = mapped_column()
    birth_date: Mapped[Optional[date]] = mapped_column(nullable=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)