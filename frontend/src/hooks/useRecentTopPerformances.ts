import { useQuery } from "@tanstack/react-query";
import api from "../lib/api.ts";
import type { RecentPerformance } from "../types/players.ts";

export function useRecentTopPerformances() {
  return useQuery({
    queryKey: ["recentTopPerformances"],
    queryFn: () =>
      api
        .get<RecentPerformance[]>("/players/top/recent-performances")
        .then((res) => res.data),
    staleTime: 5 * 60_000,
  });
}