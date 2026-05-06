import { useQuery } from "@tanstack/react-query";
import api from "../lib/api.ts";
import type { PlayerDetail } from "../types/players.ts";

export function usePlayerInfo(playerId: number) {
  return useQuery({
    queryKey: ["player", playerId],
    queryFn: () => api.get<PlayerDetail>(`/players/${playerId}`).then((r) => r.data),
    enabled: playerId > 0,
  });
}
