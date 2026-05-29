"""add game_type to team_game_stats

Revision ID: c3d4e5f6a1b2
Revises: b2c3d4e5f6a1
Create Date: 2026-05-28 00:00:02.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a1b2"
down_revision: Union[str, None] = "b2c3d4e5f6a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "team_game_stats",
        sa.Column("game_type", sa.String(), nullable=False, server_default="regular"),
    )


def downgrade() -> None:
    op.drop_column("team_game_stats", "game_type")
