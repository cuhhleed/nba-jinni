import { useParams } from "react-router";
import { useTeamStats } from "../../hooks/useTeamStats";
import type { TeamSeasonAverage } from "../../types/teams";
import EmptyState from "../ui/EmptyState";
import ErrorPage from "../ui/ErrorPage";
import LoadingPage from "../ui/LoadingPage";

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
      <div className="stats-tab-container grid grid-cols-7 m-4">
        <h2 className="col-span-7 lg:text-2xl text-gray-900 text-center">
          {averages.season} Statistics
        </h2>
        <div className="big-3-container grid grid-cols-3 col-span-5 col-start-2">
          <div className="big-3-stat-container grid grid-cols-1 col-span-1">
            <div className="border rounded-xl text-center bg-white text-lg text-amber-400 sm:text-2xl lg:text-3xl font-brand px-3 py-2 w-fit mx-auto">
              {averages.points.toFixed(1)}
            </div>
            <span className="text-gray-900 text-center">PPG</span>
          </div>
          <div className="big-3-stat-container grid grid-cols-1 col-span-1">
            <div className="border rounded-xl text-center bg-white text-lg text-amber-400 sm:text-2xl lg:text-3xl font-brand px-3 py-2 w-fit mx-auto">
              {averages.rebounds.toFixed(1)}
            </div>
            <span className="text-gray-900 text-center">RPG</span>
          </div>
          <div className="big-3-stat-container grid grid-cols-1 col-span-1">
            <div className="border rounded-xl text-center bg-white text-lg text-amber-400 sm:text-2xl lg:text-3xl font-brand px-3 py-2 w-fit mx-auto">
              {averages.assists.toFixed(1)}
            </div>
            <span className="text-gray-900 text-center">APG</span>
          </div>
        </div>

        <div className="off-stats-container grid grid-cols-4 col-span-3 col-start-3">
          <div className="off-stat-container grid grid-cols-1 col-span-1">
            <div className="border rounded-xl text-center bg-white text-sm text-amber-400 sm:text-lg lg:text-xl font-brand px-3 py-2 w-fit mx-auto">
              {(averages.fg_pct * 100).toFixed(1)}
            </div>
            <span className="text-gray-900 text-center">FG%</span>
          </div>
          <div className="off-stat-container grid grid-cols-1 col-span-1">
            <div className="border rounded-xl text-center bg-white text-sm text-amber-400 sm:text-lg lg:text-xl font-brand px-3 py-2 w-fit mx-auto">
              {(averages.three_pct * 100).toFixed(1)}
            </div>
            <span className="text-gray-900 text-center">3P%</span>
          </div>
          <div className="off-stat-container grid grid-cols-1 col-span-1">
            <div className="border rounded-xl text-center bg-white text-sm text-amber-400 sm:text-lg lg:text-xl font-brand px-3 py-2 w-fit mx-auto">
              {(averages.ft_pct * 100).toFixed(1)}
            </div>
            <span className="text-gray-900 text-center">FT%</span>
          </div>
          <div className="off-stat-container grid grid-cols-1 col-span-1">
            <div className="border rounded-xl text-center bg-white text-sm text-amber-400 sm:text-lg lg:text-xl font-brand px-3 py-2 w-fit mx-auto">
              {averages.turnovers.toFixed(1)}
            </div>
            <span className="text-gray-900 text-center">TPG</span>
          </div>
        </div>

        <div className="def-stats-container grid grid-cols-3 col-span-3 col-start-3">
          <div className="off-stat-container grid grid-cols-1 col-span-1">
            <div className="border rounded-xl text-center bg-white text-sm text-amber-400 sm:text-lg lg:text-xl font-brand px-3 py-2 w-fit mx-auto">
              {averages.blocks.toFixed(1)}
            </div>
            <span className="text-gray-900 text-center">BPG</span>
          </div>
          <div className="off-stat-container grid grid-cols-1 col-span-1">
            <div className="border rounded-xl text-center bg-white text-sm text-amber-400 sm:text-lg lg:text-xl font-brand px-3 py-2 w-fit mx-auto">
              {averages.steals.toFixed(1)}
            </div>
            <span className="text-gray-900 text-center">SPG</span>
          </div>
          <div className="off-stat-container grid grid-cols-1 col-span-1">
            <div className="border rounded-xl text-center bg-white text-sm text-amber-400 sm:text-lg lg:text-xl font-brand px-3 py-2 w-fit mx-auto">
              {averages.opponent_points.toFixed(1)}
            </div>
            <span className="text-gray-900 text-center">OPPG</span>
          </div>
        </div>
      </div>
    );
  }
}
