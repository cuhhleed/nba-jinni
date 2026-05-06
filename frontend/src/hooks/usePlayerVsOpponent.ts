import { useQuery } from "@tanstack/react-query";
import api from "../lib/api.ts";
import type { PlayerGameStatWithContext } from "../types/players.ts";

export function usePlayerVsOpponent(playerId: number, teamId: number) {
  return useQuery({
    queryKey: ["player", playerId, "vsOpponent", teamId],
    queryFn: () =>
      api
        .get<PlayerGameStatWithContext[]>(
          `/players/${playerId}/vs-opponent?team_id=${teamId}`
        )
        .then((r) => r.data),
    enabled: playerId > 0 && teamId > 0,
  });
}
