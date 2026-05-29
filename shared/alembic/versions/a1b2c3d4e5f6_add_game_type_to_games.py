"""add game_type to games

Revision ID: a1b2c3d4e5f6
Revises: 2bded37eada6
Create Date: 2026-05-28 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "2bded37eada6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "games",
        sa.Column("game_type", sa.String(), nullable=False, server_default="regular"),
    )


def downgrade() -> None:
    op.drop_column("games", "game_type")
