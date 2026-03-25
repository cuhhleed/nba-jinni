"""make teams conference and logo nullable

Revision ID: de83bacbf317
Revises: 64adc755b41c
Create Date: 2026-03-24 21:49:17.518583

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'de83bacbf317'
down_revision: Union[str, None] = '64adc755b41c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('teams', 'conference', nullable=True)
    op.alter_column('teams', 'logo', nullable=True)


def downgrade() -> None:
    op.alter_column('teams', 'conference', nullable=False)
    op.alter_column('teams', 'logo', nullable=False)