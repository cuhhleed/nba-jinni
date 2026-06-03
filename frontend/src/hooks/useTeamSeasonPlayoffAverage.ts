import { useQuery } from "@tanstack/react-query";
import api from "../lib/api.ts";
import type { TeamSeasonAverage } from "../types/teams.ts";

export function useTeamSeasonPlayoffAverage(teamId: number) {
  return useQuery({
    queryKey: ["team", teamId, "seasonPlayoffAverage"],
    queryFn: () =>
      api
        .get<TeamSeasonAverage>(`/teams/${teamId}/season-average?type=playoff`)
        .then((r) => r.data),
    enabled: teamId > 0,
  });
}
