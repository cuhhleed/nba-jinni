import { useQuery } from "@tanstack/react-query";
import api from "../lib/api.ts";
import type { TopPlayersPreview } from "../types/players.ts";

export function useTopPlayersPreview() {
  return useQuery({
    queryKey: ["topPlayersPreview"],
    queryFn: () =>
      api.get<TopPlayersPreview>("/players/top/preview").then((res) => res.data),
    staleTime: 5 * 60_000,
  });
}