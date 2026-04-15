"""update_game_schema

Revision ID: 37faaa6ce77d
Revises: 64101360f15a
Create Date: 2026-04-01 01:03:50.628967

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '37faaa6ce77d'
down_revision: Union[str, None] = '64101360f15a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(op.f('games_season_year_fkey'), 'games', type_='foreignkey')
    op.drop_constraint(op.f('player_season_averages_season_fkey'), 'player_season_averages', type_='foreignkey')
    op.drop_constraint(op.f('team_season_averages_season_id_fkey'), 'team_season_averages', type_='foreignkey')
    op.drop_constraint(op.f('standings_season_fkey'), 'standings', type_='foreignkey')
    op.drop_constraint('seasons_pkey', 'seasons', type_='primary')
    op.add_column('seasons', sa.Column('season', sa.String(), nullable=False))
    op.create_primary_key('seasons_pkey', 'seasons', ['season'])
    op.drop_column('seasons', 'year')
    op.drop_constraint(op.f('player_game_stats_game_id_fkey'), 'player_game_stats', type_='foreignkey')
    op.drop_constraint(op.f('team_game_stats_game_id_fkey'), 'team_game_stats', type_='foreignkey')
    op.add_column('games', sa.Column('season', sa.String(), nullable=False))
    op.alter_column('games', 'id',
               existing_type=sa.INTEGER(),
               type_=sa.String(),
               existing_nullable=False)
    op.create_index(op.f('ix_games_season'), 'games', ['season'], unique=False)
    op.create_foreign_key(op.f('games_season_fkey'), 'games', 'seasons', ['season'], ['season'])
    op.drop_column('games', 'season_year')
    op.add_column('player_game_stats', sa.Column('season', sa.String(), nullable=False))
    op.alter_column('player_game_stats', 'game_id',
               existing_type=sa.INTEGER(),
               type_=sa.String(),
               existing_nullable=False)
    op.drop_index(op.f('ix_player_game_stats_player_id'), table_name='player_game_stats')
    op.create_index(op.f('ix_player_game_stats_season'), 'player_game_stats', ['season'], unique=False)
    op.create_index(op.f('ix_player_game_stats_team_id'), 'player_game_stats', ['team_id'], unique=False)
    op.create_foreign_key(op.f('player_game_stats_season_fkey'), 'player_game_stats', 'seasons', ['season'], ['season'])
    op.create_foreign_key(op.f('player_game_stats_game_id_fkey'), 'player_game_stats', 'games', ['game_id'], ['id'])
    op.alter_column('player_season_averages', 'season',
               existing_type=sa.INTEGER(),
               type_=sa.String(),
               existing_nullable=False)
    op.drop_index(op.f('ix_player_season_averages_player_id'), table_name='player_season_averages')
    op.create_foreign_key(op.f('player_season_averages_season_fkey'), 'player_season_averages', 'seasons', ['season'], ['season'])
    op.alter_column('standings', 'season',
               existing_type=sa.INTEGER(),
               type_=sa.String(),
               existing_nullable=False)
    op.create_foreign_key(op.f('standings_season_fkey'), 'standings', 'seasons', ['season'], ['season'])
    op.alter_column('team_game_stats', 'game_id',
               existing_type=sa.INTEGER(),
               type_=sa.String(),
               existing_nullable=False)
    op.create_foreign_key(op.f('team_game_stats_game_id_fkey'), 'team_game_stats', 'games', ['game_id'], ['id'])
    op.add_column('team_season_averages', sa.Column('season', sa.String(), nullable=False))
    op.create_foreign_key(op.f('team_season_averages_season_fkey'), 'team_season_averages', 'seasons', ['season'], ['season'])
    op.drop_column('team_season_averages', 'season_id')


def downgrade() -> None:
    op.add_column('team_season_averages', sa.Column('season_id', sa.INTEGER(), autoincrement=False, nullable=False))
    op.drop_constraint(op.f('team_season_averages_season_fkey'), 'team_season_averages', type_='foreignkey')
    op.drop_column('team_season_averages', 'season')
    op.drop_constraint(op.f('team_game_stats_game_id_fkey'), 'team_game_stats', type_='foreignkey')
    op.alter_column('team_game_stats', 'game_id',
               existing_type=sa.String(),
               type_=sa.INTEGER(),
               existing_nullable=False)
    op.drop_constraint(op.f('standings_season_fkey'), 'standings', type_='foreignkey')
    op.alter_column('standings', 'season',
               existing_type=sa.String(),
               type_=sa.INTEGER(),
               existing_nullable=False)
    
    op.drop_constraint(op.f('player_game_stats_season_fkey'), 'player_game_stats', type_='foreignkey')
    op.drop_constraint(op.f('player_season_averages_season_fkey'), 'player_season_averages', type_='foreignkey')
    op.drop_constraint('seasons_pkey', 'seasons', type_='primary')
    op.add_column('seasons', sa.Column('year', sa.INTEGER(), autoincrement=False, nullable=False))
    op.create_primary_key('seasons_pkey', 'seasons', ['year'])
    op.drop_column('seasons', 'season')
    op.create_index(op.f('ix_player_season_averages_player_id'), 'player_season_averages', ['player_id'], unique=False)
    op.alter_column('player_season_averages', 'season',
               existing_type=sa.String(),
               type_=sa.INTEGER(),
               existing_nullable=False)
    op.drop_constraint(op.f('player_game_stats_game_id_fkey'), 'player_game_stats', type_='foreignkey')
    op.drop_index(op.f('ix_player_game_stats_team_id'), table_name='player_game_stats')
    op.drop_index(op.f('ix_player_game_stats_season'), table_name='player_game_stats')
    op.create_index(op.f('ix_player_game_stats_player_id'), 'player_game_stats', ['player_id'], unique=False)
    op.alter_column('player_game_stats', 'game_id',
               existing_type=sa.String(),
               type_=sa.INTEGER(),
               existing_nullable=False)
    op.drop_column('player_game_stats', 'season')
    op.drop_constraint(op.f('games_season_fkey'), 'games', type_='foreignkey')
    op.add_column('games', sa.Column('season_year', sa.INTEGER(), autoincrement=False, nullable=False))
    op.drop_index(op.f('ix_games_season'), table_name='games')
    op.alter_column('games', 'id',
               existing_type=sa.String(),
               type_=sa.INTEGER(),
               existing_nullable=False)
    op.drop_column('games', 'season')
    op.create_foreign_key(op.f('player_game_stats_game_id_fkey'), 'player_game_stats', 'games', ['game_id'], ['id'])
    op.create_foreign_key(op.f('team_game_stats_game_id_fkey'), 'team_game_stats', 'games', ['game_id'], ['id'])
    op.create_foreign_key(op.f('games_season_year_fkey'), 'games', 'seasons', ['season_year'], ['year'])
    op.create_foreign_key(op.f('player_season_averages_season_fkey'), 'player_season_averages', 'seasons', ['season'], ['year'])
    op.create_foreign_key(op.f('standings_season_fkey'), 'standings', 'seasons', ['season'], ['year'])
    
    op.create_foreign_key(op.f('team_season_averages_season_id_fkey'), 'team_season_averages', 'seasons', ['season_id'], ['year'])
