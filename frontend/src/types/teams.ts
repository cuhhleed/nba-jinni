import type { GameBase, GameWithTeamStats } from "./games";

export type Team = {
  id: number;
  name: string;
  nickname: string;
  code: string;
  conference: string;
  logo: string;
};

export type Standing = {
  season: string;
  team_id: number;
  conference: string;
  conference_rank: number;
  wins: number;
  wins_home: number;
  wins_away: number;
  losses: number;
  losses_home: number;
  losses_away: number;
  win_pct: number;
  games_behind: number;
  win_L10: number;
  loss_L10: number;
  streak: number;
  points_pg: number;
  opp_points_pg: number;
};

export type TeamWithStanding = Team & {
  standing: Standing | null;
};

export type TeamSeasonAverage = {
  team_id: number;
  season: string;
  games_played: number;
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

export type TeamStatsResponse = {
  season_average: TeamSeasonAverage | null;
  recent_game_stats: GameWithTeamStats[];
};

export type TeamScheduleResponse = {
  recent: GameWithTeamStats[];
  upcoming: GameBase[];
};
