import { useParams } from "react-router";
import { useTeamStats } from "../../hooks/useTeamStats";
import type { TeamSeasonAverage } from "../../types/teams";
import EmptyState from "../ui/EmptyState";
import ErrorPage from "../ui/ErrorPage";
import LoadingPage from "../ui/LoadingPage";
import StatBubble from "../ui/StatBubble";

export default function StatsTab() {
  const { id } = useParams();
  const teamId = Number(id);

  const { data: teamStats, isLoading, error } = useTeamStats(teamId);
  if (isLoading) {
    return <LoadingPage />;
  } else if (error) {
    return <ErrorPage />;
  } else if (teamStats) {
    const averages = buildAverages(teamStats.season_average);
    return averages;
  }
}

function buildAverages(averages: TeamSeasonAverage | null) {
  if (!averages) {
    return <EmptyState />;
  } else {
    return (
      <div className="stats-tab-container grid grid-cols-7 my-8">
        <h2 className="col-span-7 lg:text-2xl text-gray-900 text-center">
          {averages.season} Statistics
        </h2>
        <div className="big-3-container grid grid-cols-3 col-span-5 col-start-2">
          <StatBubble value={averages.points.toFixed(1)} label="PPG" size="lg" />
          <StatBubble value={averages.rebounds.toFixed(1)} label="RPG" size="lg" />
          <StatBubble value={averages.assists.toFixed(1)} label="APG" size="lg" />
        </div>

        <div className="off-stats-container grid grid-cols-4 col-span-5 col-start-2">
          <StatBubble value={(averages.fg_pct * 100).toFixed(1)} label="FG%" />
          <StatBubble value={(averages.three_pct * 100).toFixed(1)} label="3P%" />
          <StatBubble value={(averages.ft_pct * 100).toFixed(1)} label="FT%" />
          <StatBubble value={averages.turnovers.toFixed(1)} label="TPG" />
        </div>

        <div className="def-stats-container grid grid-cols-3 col-span-3 col-start-3">
          <StatBubble value={averages.blocks.toFixed(1)} label="BPG" />
          <StatBubble value={averages.steals.toFixed(1)} label="SPG" />
          <StatBubble value={averages.opponent_points.toFixed(1)} label="OPPG" />
        </div>
      </div>
    );
  }
}
