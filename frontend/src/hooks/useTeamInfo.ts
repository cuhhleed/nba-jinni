import { useQuery } from "@tanstack/react-query";
import api from "../lib/api.ts";
import type { TeamWithStanding } from "../types/teams.ts";

export function useTeamInfo(teamId: number) {
  return useQuery({
    queryKey: ["team", teamId],
    queryFn: () => api.get<TeamWithStanding>(`/teams/${teamId}`).then((r) => r.data),
    enabled: teamId > 0,
  });
}
