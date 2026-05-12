import { useCallback, useEffect, useRef, useState } from "react";
import { useLiveScoreboard } from "../../hooks/useLiveScoreboard";
import { useTeams } from "../../hooks/useTeams";
import type { Team } from "../../types/teams";
import ErrorState from "../ui/ErrorState";
import LoadingState from "../ui/LoadingState";
import GameCarpetBadge from "./GameCarpetBadge";

const GAP_PX = 12; // matches gap-3 (0.75rem @ 16px base)
const AUTO_ADVANCE_MS = 7000;

export default function GamesWidget() {
  const {
    data: scoreboard,
    isLoading: sbLoading,
    error: sbError,
  } = useLiveScoreboard();
  const { data: teams, isLoading: teamsLoading, error: teamsError } = useTeams();

  const viewportRef = useRef<HTMLDivElement>(null);
  const trackRef = useRef<HTMLDivElement>(null);
  const pageIndexRef = useRef(0);
  const isPausedRef = useRef(false);
  const [, setPageIndex] = useState(0);
  const [resetKey, setResetKey] = useState(0);

  const paginate = useCallback((rawIndex: number) => {
    const vp = viewportRef.current;
    const tr = trackRef.current;
    if (!vp || !tr) return;
    const vw = vp.offsetWidth;
    const tw = tr.scrollWidth;
    if (tw <= vw) return;
    const totalPages = Math.ceil(tw / (vw + GAP_PX));
    const idx = ((rawIndex % totalPages) + totalPages) % totalPages;
    pageIndexRef.current = idx;
    setPageIndex(idx);
    tr.style.transform = `translateX(-${idx * (vw + GAP_PX)}px)`;
  }, []);

  useEffect(() => {
    const games = scoreboard?.games;
    if (!games || games.length === 0) return;
    const id = setInterval(() => {
      if (!isPausedRef.current) paginate(pageIndexRef.current + 1);
    }, AUTO_ADVANCE_MS);
    return () => clearInterval(id);
  }, [resetKey, scoreboard?.games, paginate]);

  function handleArrow(dir: 1 | -1) {
    paginate(pageIndexRef.current + dir);
    setResetKey((k) => k + 1);
  }

  const isLoading = sbLoading || teamsLoading;
  const hasError = sbError || teamsError;

  const teamMap: Map<number, Team> = new Map(teams?.map((t) => [t.id, t]) ?? []);
  const games = scoreboard?.games ?? [];
  const isStale = scoreboard?.is_stale ?? false;
  const lastUpdatedAt = scoreboard?.last_updated_at ?? "";

  return (
    <div
      className="relative flex items-stretch gap-2"
      onMouseEnter={() => {
        isPausedRef.current = true;
      }}
      onMouseLeave={() => {
        isPausedRef.current = false;
      }}
    >
      <button
        onClick={() => handleArrow(-1)}
        aria-label="Previous games"
        className={`shrink-0 w-8 mr-3 flex items-center justify-center text-amber-500 hover:text-amber-300 transition-colors text-xl font-bold ${games.length <= 1 ? "invisible" : ""}`}
      >
        ‹
      </button>

      <div ref={viewportRef} className="overflow-hidden flex-1 py-4">
        {isLoading && (
          <div className="flex justify-center py-6">
            <LoadingState />
          </div>
        )}
        {hasError && !isLoading && (
          <div className="flex justify-center py-6">
            <ErrorState />
          </div>
        )}
        {!isLoading && !hasError && games.length === 0 && (
          <div className="flex justify-center py-6 text-gray-400 text-sm">
            No games scheduled today.
          </div>
        )}
        {!isLoading && !hasError && games.length > 0 && (
          <div
            ref={trackRef}
            className="flex gap-3 px-2 transition-transform duration-300 ease-in-out"
          >
            {games.map((entry) => (
              <GameCarpetBadge
                key={entry.id}
                entry={entry}
                teamMap={teamMap}
                isStale={isStale}
                lastUpdatedAt={lastUpdatedAt}
              />
            ))}
          </div>
        )}
      </div>

      <button
        onClick={() => handleArrow(1)}
        aria-label="Next games"
        className={`shrink-0 w-8 flex items-center justify-center text-amber-500 hover:text-amber-300 transition-colors text-xl font-bold ${games.length <= 1 ? "invisible" : ""}`}
      >
        ›
      </button>
    </div>
  );
}
