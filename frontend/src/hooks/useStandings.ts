import { useQuery } from "@tanstack/react-query";
import api from "../lib/api.ts";
import type { Standing } from "../types/teams.ts";

export function useStandings() {
  return useQuery({
    queryKey: ["standings"],
    queryFn: () => api.get<Standing[]>("/standings").then((res) => res.data),
    staleTime: 5 * 60 * 1000,
  });
}
