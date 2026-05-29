"""create player_playoff_season_averages

Revision ID: d4e5f6a1b2c3
Revises: c3d4e5f6a1b2
Create Date: 2026-05-28 00:00:03.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a1b2c3"
down_revision: Union[str, None] = "c3d4e5f6a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "player_playoff_season_averages",
        sa.Column("season", sa.String(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("games_played", sa.Integer(), nullable=False),
        sa.Column("min_pg", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("points_pg", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("fgm_pg", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("fga_pg", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("ftm_pg", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("fta_pg", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("tpm_pg", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("tpa_pg", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("off_reb_pg", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("def_reb_pg", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("tot_reb_pg", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("asts_pg", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("stls_pg", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("blks_pg", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("tos_pg", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("pfs_pg", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("fgp", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("ftp", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("tpp", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("plus_minus_pg", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"]),
        sa.ForeignKeyConstraint(["season"], ["seasons.season"]),
        sa.PrimaryKeyConstraint("season", "player_id"),
        sa.UniqueConstraint("player_id", "season"),
    )


def downgrade() -> None:
    op.drop_table("player_playoff_season_averages")
