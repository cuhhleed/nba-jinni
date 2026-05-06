import { useQuery } from "@tanstack/react-query";
import api from "../lib/api.ts";
import type { PlayerGameStatWithContext } from "../types/players.ts";

export function usePlayerLast5Games(playerId: number) {
  return useQuery({
    queryKey: ["player", playerId, "last5Games"],
    queryFn: () =>
      api
        .get<PlayerGameStatWithContext[]>(`/players/${playerId}/last-5-games`)
        .then((r) => r.data),
    enabled: playerId > 0,
  });
}
