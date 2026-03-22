from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import ForeignKey
from datetime import date
from nbajinni_shared.base import Base

class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    first_name: Mapped[str] = mapped_column()
    last_name: Mapped[str] = mapped_column()
    birth_date: Mapped[date] = mapped_column()
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))