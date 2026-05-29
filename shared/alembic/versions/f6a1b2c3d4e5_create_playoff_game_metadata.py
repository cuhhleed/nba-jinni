"""create playoff_game_metadata

Revision ID: f6a1b2c3d4e5
Revises: e5f6a1b2c3d4
Create Date: 2026-05-28 00:00:05.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "f6a1b2c3d4e5"
down_revision: Union[str, None] = "e5f6a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "playoff_game_metadata",
        sa.Column("game_id", sa.String(), nullable=False),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("series_game_number", sa.Integer(), nullable=False),
        sa.Column("series_record", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("game_id"),
    )


def downgrade() -> None:
    op.drop_table("playoff_game_metadata")
