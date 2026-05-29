"""create team_playoff_season_averages

Revision ID: e5f6a1b2c3d4
Revises: d4e5f6a1b2c3
Create Date: 2026-05-28 00:00:04.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "e5f6a1b2c3d4"
down_revision: Union[str, None] = "d4e5f6a1b2c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "team_playoff_season_averages",
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("season", sa.String(), nullable=False),
        sa.Column("games_played", sa.Integer(), nullable=False),
        sa.Column("points", sa.Numeric(precision=5, scale=1), nullable=False),
        sa.Column("opponent_points", sa.Numeric(precision=5, scale=1), nullable=False),
        sa.Column("rebounds", sa.Numeric(precision=5, scale=1), nullable=False),
        sa.Column("assists", sa.Numeric(precision=5, scale=1), nullable=False),
        sa.Column("steals", sa.Numeric(precision=5, scale=1), nullable=False),
        sa.Column("blocks", sa.Numeric(precision=5, scale=1), nullable=False),
        sa.Column("turnovers", sa.Numeric(precision=5, scale=1), nullable=False),
        sa.Column("fg_pct", sa.Numeric(precision=5, scale=3), nullable=False),
        sa.Column("three_pct", sa.Numeric(precision=5, scale=3), nullable=False),
        sa.Column("ft_pct", sa.Numeric(precision=5, scale=3), nullable=False),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["season"], ["seasons.season"]),
        sa.PrimaryKeyConstraint("team_id", "season"),
        sa.UniqueConstraint("team_id", "season"),
    )


def downgrade() -> None:
    op.drop_table("team_playoff_season_averages")
