"""add tipoff at to games

Revision ID: 2bded37eada6
Revises: 12cae71f3617
Create Date: 2026-05-09 23:16:31.706422

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from nbajinni_shared.alembic_utils import add_required_column

# revision identifiers, used by Alembic.
revision: str = "2bded37eada6"
down_revision: Union[str, None] = "12cae71f3617"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    add_required_column(
        "games",
        sa.Column(
            "tipoff_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_column("games", "tipoff_at")
