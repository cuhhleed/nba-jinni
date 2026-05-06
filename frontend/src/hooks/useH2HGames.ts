import { useQuery } from "@tanstack/react-query";
import api from "../lib/api.ts";
import type { GameWithTeamStats } from "../types/games.ts";

export function useH2HGames(teamA: number, teamB: number) {
  return useQuery({
    queryKey: ["games", "h2h", teamA, teamB],
    queryFn: () =>
      api
        .get<GameWithTeamStats[]>(`/games/h2h`, {
          params: { team_a: teamA, team_b: teamB },
        })
        .then((r) => r.data),
    enabled: teamA > 0 && teamB > 0,
    staleTime: 5 * 60 * 1000,
  });
}
