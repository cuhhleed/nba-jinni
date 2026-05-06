import { useQuery } from "@tanstack/react-query";
import api from "../lib/api.ts";
import type { PlayerSeasonAverage } from "../types/players.ts";

export function usePlayerSeasonAverage(playerId: number) {
  return useQuery({
    queryKey: ["player", playerId, "seasonAverage"],
    queryFn: () =>
      api
        .get<PlayerSeasonAverage>(`/players/${playerId}/season-average`)
        .then((r) => r.data),
    enabled: playerId > 0,
  });
}
