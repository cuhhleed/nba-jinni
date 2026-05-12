export type Player = {
  id: number;
  first_name: string;
  last_name: string;
  birth_date: string | null;
};

import type { Team } from "./teams";

export type PlayerDetail = Player & {
  team: Team; // non-optional; matches backend's `team: TeamBase` in PlayerDetail schema
};
// Derive the player's team id from `player.team.id` — the backend does not expose `team_id` separately.

export type PlayerSeasonAverage = {
  season: string;
  player_id: number;
  games_played: number;
  min_pg: number;
  points_pg: number;
  fgm_pg: number;
  fga_pg: number;
  fgp: number;
  ftm_pg: number;
  fta_pg: number;
  ftp: number;
  tpm_pg: number;
  tpa_pg: number;
  tpp: number;
  off_reb_pg: number;
  def_reb_pg: number;
  tot_reb_pg: number;
  asts_pg: number;
  stls_pg: number;
  blks_pg: number;
  tos_pg: number;
  pfs_pg: number;
  plus_minus_pg: number;
};

export type PlayerGameStat = {
  game_id: string;
  player_id: number;
  season: string;
  team_id: number;
  pos: string;
  min: number;
  points: number;
  fgm: number;
  fga: number;
  fgp: number;
  ftm: number;
  fta: number;
  ftp: number;
  tpm: number;
  tpa: number;
  tpp: number;
  off_reb: number;
  def_reb: number;
  tot_reb: number;
  asts: number;
  stls: number;
  blks: number;
  tos: number;
  pfs: number;
  plus_minus: number;
};

export type PlayerGameStatWithContext = PlayerGameStat & {
  game_date: string;
  opponent_team_id: number;
};

export type PlayerSeasonAverageWithPlayer = PlayerSeasonAverage & {
  player: Player;
};

export type RecentPerformance = {
  player_id: number;
  full_name: string;
  team_id: number;
  game_id: string;
  points: number;
  tot_reb: number;
  asts: number;
  stls: number;
  blks: number;
};

export type TopPlayersPreview = Record<
  "points" | "rebounds" | "assists" | "steals" | "blocks",
  PlayerSeasonAverageWithPlayer[]
>;
