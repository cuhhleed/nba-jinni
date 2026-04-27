import { useQuery } from "@tanstack/react-query";
import api from "../lib/api.ts";
import type { TeamScheduleResponse } from "../types/teams.ts";

export function useTeamSchedule(teamId: number) {
  return useQuery({
    queryKey: ["team", teamId, "schedule"],
    queryFn: () =>
      api.get<TeamScheduleResponse>(`/teams/${teamId}/games`).then((r) => r.data),
    enabled: teamId > 0,
  });
}
