import { useQuery } from "@tanstack/react-query";
import api from "../lib/api.ts";
import type { PlayerSeasonAverage } from "../types/players.ts";

export function usePlayerSeasonPlayoffAverage(playerId: number) {
  return useQuery({
    queryKey: ["player", playerId, "seasonPlayoffAverage"],
    queryFn: () =>
      api
        .get<PlayerSeasonAverage>(`/players/${playerId}/season-average?type=playoff`)
        .then((r) => r.data),
    enabled: playerId > 0,
  });
}
