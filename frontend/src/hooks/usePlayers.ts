import { useQuery } from "@tanstack/react-query";
import api from "../lib/api.ts";
import type { Player } from "../types/players.ts";

export function usePlayers() {
  return useQuery({
    queryKey: ["players"],
    queryFn: () => api.get<Player[]>("/players").then((res) => res.data),
  });
}
