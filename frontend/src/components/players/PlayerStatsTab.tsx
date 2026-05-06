import { useParams } from "react-router";
import { usePlayerSeasonAverage } from "../../hooks/usePlayerSeasonAverage";
import type { PlayerSeasonAverage } from "../../types/players";
import EmptyState from "../ui/EmptyState";
import ErrorState from "../ui/ErrorState";
import LoadingState from "../ui/LoadingState";
import StatBubble from "../ui/StatBubble";

export default function PlayerStatsTab() {
  const { id } = useParams();
  const playerId = Number(id);

  const { data: playerAverages, isLoading, error } = usePlayerSeasonAverage(playerId);
  if (isLoading) {
    return <LoadingState />;
  } else if (error) {
    return <ErrorState />;
  } else if (playerAverages) {
    const averages = buildAverages(playerAverages);
    return averages;
  }
}

function buildAverages(averages: PlayerSeasonAverage | null) {
  if (!averages) {
    return <EmptyState />;
  } else {
    return (
      <div className="stats-tab-container grid grid-cols-7 my-8">
        <h2 className="col-span-7 lg:text-2xl text-gray-900 text-center">
          {averages.season} Statistics
        </h2>
        <div className="big-3-container grid grid-cols-3 col-span-5 col-start-2">
          <StatBubble value={averages.points_pg.toFixed(1)} label="PPG" size="lg" />
          <StatBubble value={averages.tot_reb_pg.toFixed(1)} label="RPG" size="lg" />
          <StatBubble value={averages.asts_pg.toFixed(1)} label="APG" size="lg" />
        </div>

        <div className="off-stats-container grid grid-cols-4 col-span-5 col-start-2">
          <StatBubble value={(averages.fgp * 100).toFixed(1)} label="FG%" />
          <StatBubble value={(averages.tpp * 100).toFixed(1)} label="3P%" />
          <StatBubble value={(averages.ftp * 100).toFixed(1)} label="FT%" />
          <StatBubble value={averages.min_pg.toFixed(1)} label="MIN" />
        </div>

        <div className="def-stats-container grid grid-cols-4 col-span-5 col-start-2">
          <StatBubble value={averages.blks_pg.toFixed(1)} label="BPG" />
          <StatBubble value={averages.stls_pg.toFixed(1)} label="SPG" />
          <StatBubble value={averages.tos_pg.toFixed(1)} label="TPG" />
          <StatBubble value={averages.plus_minus_pg.toFixed(1)} label="+/-" />
        </div>
      </div>
    );
  }
}
