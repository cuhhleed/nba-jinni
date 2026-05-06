import { useQuery } from "@tanstack/react-query";
import api from "../lib/api.ts";
import type { GameDetailResponse } from "../types/games.ts";

export function useGameDetail(gameId: string) {
  return useQuery({
    queryKey: ["game", gameId],
    queryFn: () =>
      api.get<GameDetailResponse>(`/games/${gameId}`).then((r) => r.data),
    enabled: gameId.length > 0,
    staleTime: 5 * 60 * 1000,
  });
}
