"""add indexes

Revision ID: 64adc755b41c
Revises: da5726f6b6a0
Create Date: 2026-03-18 23:46:22.999903

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '64adc755b41c'
down_revision: Union[str, None] = 'da5726f6b6a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('ix_player_game_stats_player_id', 'player_game_stats', ['player_id'])
    op.create_index('ix_player_game_stats_game_id', 'player_game_stats', ['game_id'])
    op.create_index('ix_games_game_date', 'games', ['game_date'])
    op.create_index('ix_games_home_team_id', 'games', ['home_team_id'])
    op.create_index('ix_games_away_team_id', 'games', ['away_team_id'])
    op.create_index('ix_standings_team_id', 'standings', ['team_id'])
    op.create_index('ix_players_team_id', 'players', ['team_id'])
    op.create_index('ix_player_season_averages_player_id', 'player_season_averages', ['player_id'])


def downgrade() -> None:
    op.drop_index('ix_player_game_stats_player_id', table_name='player_game_stats')
    op.drop_index('ix_player_game_stats_game_id', table_name='player_game_stats')
    op.drop_index('ix_games_game_date', table_name='games')
    op.drop_index('ix_games_home_team_id', table_name='games')
    op.drop_index('ix_games_away_team_id', table_name='games')
    op.drop_index('ix_standings_team_id', table_name='standings')
    op.drop_index('ix_players_team_id', table_name='players')
    op.drop_index('ix_player_season_averages_player_id', table_name='player_season_averages')
