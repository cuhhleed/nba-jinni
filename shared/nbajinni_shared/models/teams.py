from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
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