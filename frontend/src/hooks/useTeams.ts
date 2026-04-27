import { useQuery } from "@tanstack/react-query";
import api from "../lib/api.ts";
import type { Team } from "../types/teams.ts";

export function useTeams() {
  return useQuery({
    queryKey: ["teams"],
    queryFn: () => api.get<Team[]>("/teams").then((res) => res.data),
  });
}
