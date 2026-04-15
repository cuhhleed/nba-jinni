"""make players birth_date nullable

Revision ID: a99b296966ad
Revises: de83bacbf317
Create Date: 2026-03-24 22:43:49.058505

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a99b296966ad'
down_revision: Union[str, None] = 'de83bacbf317'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('players', 'birth_date', nullable=True)


def downgrade() -> None:
    op.alter_column('players', 'birth_date', nullable=False)
