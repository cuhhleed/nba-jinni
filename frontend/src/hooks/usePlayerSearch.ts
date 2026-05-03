import { useQuery } from "@tanstack/react-query";
import api from "../lib/api.ts";
import type { Player } from "../types/players.ts";

export function usePlayerSearch(q: string) {
  return useQuery({
    queryKey: ["players", "search", q],
    queryFn: () =>
      api.get<Player[]>("/players/search", { params: { q } }).then((res) => res.data),
    enabled: q.trim().length >= 2,
  });
}
