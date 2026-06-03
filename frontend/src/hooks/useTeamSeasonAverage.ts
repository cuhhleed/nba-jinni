import { useQuery } from "@tanstack/react-query";
import api from "../lib/api.ts";
import type { TeamSeasonAverage } from "../types/teams.ts";

export function useTeamSeasonAverage(teamId: number) {
  return useQuery({
    queryKey: ["team", teamId, "seasonAverage"],
    queryFn: () =>
      api
        .get<TeamSeasonAverage>(`/teams/${teamId}/season-average`)
        .then((r) => r.data),
    enabled: teamId > 0,
  });
}
