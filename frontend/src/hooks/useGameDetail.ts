import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import api from "../lib/api.ts";
import type { GameDetailResponse, GameLive, GamePreview, GameResult } from "../types/games.ts";

async function fetchGameDetail(gameId: string): Promise<GameDetailResponse> {
  // First fetch the base game data to determine state.
  const baseResponse = await api.get<GamePreview | GameResult>(`/games/${gameId}`);
  const baseGame = baseResponse.data;

  // State A: completed and ingested — return result directly, no live call needed.
  if (baseGame.status === 3) {
    return baseGame;
  }

  // State B: game has not yet tipped off — return preview directly.
  const tipoffTime = new Date(baseGame.tipoff_at);
  if (Date.now() < tipoffTime.getTime()) {
    return baseGame;
  }

  // State C: tipoff has passed but game is not yet fully ingested — attempt live endpoint.
  try {
    const liveResponse = await api.get<GameLive>(`/games/live/${gameId}`);
    return liveResponse.data;
  } catch (err) {
    if (axios.isAxiosError(err) && err.response?.status === 409) {
      // Race condition: ingest landed between the two calls. Re-fetch base to get the
      // final result (the server now considers this game completed).
      const fallbackResponse = await api.get<GamePreview | GameResult>(`/games/${gameId}`);
      return fallbackResponse.data;
    }
    // Any other error (404, 5xx, network) propagates to React Query for normal error handling.
    throw err;
  }
}

export function useGameDetail(gameId: string) {
  return useQuery({
    queryKey: ["gameDetail", gameId],
    queryFn: () => fetchGameDetail(gameId),
    enabled: gameId.length > 0,
    staleTime: 5 * 60 * 1000,
    // Poll every 60 s only while the game is in live state; disable otherwise.
    refetchInterval: (query) =>
      query.state.data?.kind === "live" ? 60_000 : false,
  });
}
