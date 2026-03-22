from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from nbajinni_shared.base import Base


class Season(Base):
    __tablename__ = "seasons"

    year: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)