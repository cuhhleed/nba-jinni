import { useState } from "react";
import { Link } from "react-router";
import { useTopPlayersPreview } from "../../hooks/useTopPlayersPreview";
import type { TopPlayersPreview } from "../../types/players";
import PlayerHeadshot from "../players/PlayerHeadshot";
import CarpetBadge from "../ui/CarpetBadge";
import ErrorState from "../ui/ErrorState";
import LoadingState from "../ui/LoadingState";
import PillTabs from "../ui/PillTabs";

type StatKey = keyof TopPlayersPreview;

const TABS: { id: StatKey; label: string }[] = [
  { id: "points", label: "PTS" },
  { id: "rebounds", label: "REB" },
  { id: "assists", label: "AST" },
  { id: "steals", label: "STL" },
  { id: "blocks", label: "BLK" },
];

const STAT_FIELD: Record<
  StatKey,
  "points_pg" | "tot_reb_pg" | "asts_pg" | "stls_pg" | "blks_pg"
> = {
  points: "points_pg",
  rebounds: "tot_reb_pg",
  assists: "asts_pg",
  steals: "stls_pg",
  blocks: "blks_pg",
};

const COL_GRID = "grid grid-cols-[2rem_1fr_4rem]";

export default function StatLeaders() {
  const [activeTab, setActiveTab] = useState<StatKey>("points");
  const { data: preview, isLoading, error } = useTopPlayersPreview();

  const rows = preview?.[activeTab] ?? [];

  return (
    <div>
      <CarpetBadge className="p-4 mb-7 flex flex-col items-center gap-3">
        <h2 className="text-xl font-brand text-sky-600">Stat Leaders</h2>
        <PillTabs
          tabs={TABS}
          activeTab={activeTab}
          onChange={setActiveTab}
          className="bg-sky-600"
          activeClassName="bg-amber-500 text-gray-900 font-brand"
          inactiveClassName="text-gray-900 bg-sky-600 hover:text-amber-500"
        />
      </CarpetBadge>

      <div className="mt-3">
        {isLoading && (
          <div className="flex justify-center py-6">
            <LoadingState />
          </div>
        )}
        {error && !isLoading && (
          <div className="flex justify-center py-6">
            <ErrorState />
          </div>
        )}
        {!isLoading && !error && (
          <>
            <div
              className={`${COL_GRID} bg-gray-900 border border-amber-500 px-2 py-1.5 divide-x divide-amber-500`}
            >
              {["RNK", "PLAYER", TABS.find((t) => t.id === activeTab)?.label ?? ""].map(
                (h, i) => (
                  <span
                    key={i}
                    className="text-[10px] lg:text-xs font-brand text-sky-600 uppercase tracking-wide text-center self-center"
                  >
                    {h}
                  </span>
                )
              )}
            </div>
            {rows.map((row, i) => (
              <Link
                key={row.player.id}
                to={`/players/${row.player.id}`}
                className={`${COL_GRID} bg-white border-b border-b-amber-500/20 px-2 py-1.5 divide-x divide-amber-500/20 hover:bg-amber-500/10 transition-colors`}
              >
                <span className="text-xs font-semibold text-gray-700 text-center self-center">
                  {i + 1}
                </span>
                <div className="flex items-center gap-1.5 px-1 min-w-0">
                  <PlayerHeadshot
                    playerId={row.player.id}
                    size="sm"
                    className="shrink-0"
                  />
                  <span className="text-xs text-gray-900 truncate">
                    {row.player.first_name} {row.player.last_name}
                  </span>
                </div>
                <span className="text-xs font-bold text-gray-900 text-center self-center">
                  {row[STAT_FIELD[activeTab]].toFixed(1)}
                </span>
              </Link>
            ))}
          </>
        )}
      </div>
    </div>
  );
}
