import { useQuery } from "@tanstack/react-query";
import api from "../lib/api.ts";
import type { TeamStatsResponse } from "../types/teams.ts";

export function useTeamStats(teamId: number) {
  return useQuery({
    queryKey: ["team", teamId, "stats"],
    queryFn: () =>
      api.get<TeamStatsResponse>(`/teams/${teamId}/stats`).then((r) => r.data),
    enabled: teamId > 0,
  });
}
