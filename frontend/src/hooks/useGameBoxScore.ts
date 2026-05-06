import { useQuery } from "@tanstack/react-query";
import api from "../lib/api.ts";
import type { PlayerGameBoxScore } from "../types/games.ts";

export function useGameBoxScore(gameId: string) {
  return useQuery({
    queryKey: ["game", gameId, "playerstats"],
    queryFn: () =>
      api
        .get<PlayerGameBoxScore[]>(`/games/${gameId}/playerstats`)
        .then((r) => r.data),
    enabled: gameId.length > 0,
    staleTime: 5 * 60 * 1000,
  });
}
