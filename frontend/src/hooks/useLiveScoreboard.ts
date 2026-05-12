import { useQuery } from "@tanstack/react-query";
import api from "../lib/api.ts";
import type { LiveScoreboardResponse } from "../types/games.ts";

export function useLiveScoreboard() {
  return useQuery({
    queryKey: ["liveScoreboard"],
    queryFn: () =>
      api.get<LiveScoreboardResponse>("/games/live/today").then((res) => res.data),
    staleTime: 30_000,
    refetchInterval: 30_000,
  });
}