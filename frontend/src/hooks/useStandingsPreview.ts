import { useQuery } from "@tanstack/react-query";
import api from "../lib/api.ts";
import type { Standing } from "../types/teams.ts";

export function useStandingsPreview() {
  return useQuery({
    queryKey: ["standingsPreview"],
    queryFn: () =>
      api.get<Standing[]>("/standings/preview").then((res) => res.data),
    staleTime: 5 * 60_000,
  });
}