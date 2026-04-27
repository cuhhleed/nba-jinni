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

export type GameBase = {
  id: string;
  home_team_id: number;
  away_team_id: number;
  season: string;
  game_date: string;
  status: number;
};

export type GameWithTeamStats = GameBase & {
  home_team_stat: TeamGameStat | null;
  away_team_stat: TeamGameStat | null;
};