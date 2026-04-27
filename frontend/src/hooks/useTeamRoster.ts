import { useQuery } from "@tanstack/react-query";
import api from "../lib/api.ts";
import type { Player } from "../types/players.ts";

export function useTeamRoster(teamId: number) {
  return useQuery({
    queryKey: ["team", teamId, "roster"],
    queryFn: () => api.get<Player[]>(`/teams/${teamId}/roster`).then((r) => r.data),
    enabled: teamId > 0,
  });
}
