import type { Team, Standing, TeamSeasonAverage, TeamWithStanding } from "./teams";

export type TeamGameStat = {
  game_id: string;
  team_id: number;
  season: string;
  points: number;
  opponent_points: number;
  rebounds: number;
  assists: number;
  steals: number;
  blocks: number;
  turnovers: number;
  fg_pct: number;
  three_pct: number;
  ft_pct: number;
};

// Re-export for convenience — game components import from this module.
export type { TeamWithStanding };

// TeamWithStandingAndAverage — used by GamePreview.
export type TeamWithStandingAndAverage = Team & {
  standing: Standing | null;
  season_averages: TeamSeasonAverage[];
};

export type GamePreview = GameBase & {
  kind: "preview";
  home_team: TeamWithStandingAndAverage;
  away_team: TeamWithStandingAndAverage;
};

export type GameResult = GameBase & {
  kind: "result";
  home_team: TeamWithStanding;
  away_team: TeamWithStanding;
  home_team_stat: TeamGameStat;
  away_team_stat: TeamGameStat;
};

export type PlayerLiveStat = {
  player_id: number;
  first_name: string;
  last_name: string;
  points: number;
  rebounds: number;
  assists: number;
  steals: number;
  blocks: number;
  turnovers: number;
  fg_made: number;
  fg_attempted: number;
  three_made: number;
  three_attempted: number;
  ft_made: number;
  ft_attempted: number;
  minutes: string;
};

export type GameLive = {
  kind: "live";
  id: string;
  home_team: TeamWithStandingAndAverage;
  away_team: TeamWithStandingAndAverage;
  home_score: number;
  away_score: number;
  period: number;
  game_clock: string;
  game_status_text: string;
  home_player_stats: PlayerLiveStat[];
  away_player_stats: PlayerLiveStat[];
  last_updated_at: string;
  is_stale: boolean;
};

export type GameDetailResponse = GamePreview | GameResult | GameLive;

// Box score row — includes player names added by the backend schema extension.
export type PlayerGameBoxScore = {
  game_id: string;
  player_id: number;
  team_id: number;
  first_name: string;
  last_name: string;
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

export type GameBase = {
  id: string;
  home_team_id: number;
  away_team_id: number;
  season: string;
  game_date: string;
  status: number;
  tipoff_at: string;
};

export type GameWithTeamStats = GameBase & {
  home_team_stat: TeamGameStat | null;
  away_team_stat: TeamGameStat | null;
};

export type LiveScoreboardEntry = {
  id: string;
  home_team_id: number;
  away_team_id: number;
  home_score: number | null;
  away_score: number | null;
  period: number | null;
  game_clock: string | null;
  game_status_text: string;
  tipoff_at: string;
  state: "scheduled" | "live" | "final";
};

export type LiveScoreboardResponse = {
  games: LiveScoreboardEntry[];
  last_updated_at: string;
  is_stale: boolean;
};