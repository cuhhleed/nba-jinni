"""create seasons table

Revision ID: 2d5fbed26139
Revises: 
Create Date: 2026-03-16 03:15:18.784036

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2d5fbed26139'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "seasons",
        sa.Column("year", sa.Integer(), nullable=False, autoincrement=False),
        sa.PrimaryKeyConstraint("year")
    )


def downgrade() -> None:
    op.drop_table("seasons")
