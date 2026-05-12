import { Link } from "react-router";
import { useStandingsPreview } from "../../hooks/useStandingsPreview";
import { useTeams } from "../../hooks/useTeams";
import { formatStreak } from "../../lib/format";
import TeamLogo from "../teams/TeamLogo";
import CarpetBadge from "../ui/CarpetBadge";
import ErrorState from "../ui/ErrorState";
import LoadingState from "../ui/LoadingState";

const COL_GRID = "grid grid-cols-[2rem_1fr_3.5rem_3rem_3rem]";

const HEADERS = ["RNK", "TEAM", "W/L", "L10", "STRK"];

export default function Top10Standings() {
  const { data: standings, isLoading: sLoading, error: sError } = useStandingsPreview();
  const { data: teams, isLoading: tLoading, error: tError } = useTeams();

  const isLoading = sLoading || tLoading;
  const hasError = sError || tError;
  const teamMap = new Map(teams?.map((t) => [t.id, t]) ?? []);

  return (
    <div>
      <CarpetBadge className="p-4 mb-7 flex items-center justify-between">
        <h2 className="text-xl font-brand text-sky-600">Top 10</h2>
        <Link
          to="/standings"
          className="text-xs text-amber-500 hover:text-amber-300 underline-offset-2 hover:underline transition-colors"
        >
          See full standings
        </Link>
      </CarpetBadge>

      <div className="mt-3">
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
        {!isLoading && !hasError && standings && (
          <>
            <div
              className={`${COL_GRID} bg-gray-900 border border-amber-500 px-2 py-1.5 divide-x divide-amber-500`}
            >
              {HEADERS.map((h) => (
                <span
                  key={h}
                  className="text-[10px] lg:text-xs text-sky-600 uppercase tracking-wide text-center"
                >
                  {h}
                </span>
              ))}
            </div>
            {standings.map((s, i) => {
              const team = teamMap.get(s.team_id);
              return (
                <Link
                  key={s.team_id}
                  to={`/teams/${s.team_id}`}
                  className={`${COL_GRID} bg-white border-b border-b-amber-500/20 px-2 py-1.5 divide-x divide-amber-500/20 hover:bg-amber-500/10 transition-colors`}
                >
                  <span className="text-xs text-gray-900 font-semibold text-center self-center">
                    {i + 1}
                  </span>
                  <div className="flex items-center gap-1 px-1">
                    <TeamLogo
                      teamId={s.team_id}
                      size="sm"
                      alt={team?.code}
                      className="shrink-0"
                    />
                    <span className="text-xs font-brand text-gray-900 truncate">
                      {team?.code ?? "—"}
                    </span>
                  </div>
                  <span className="text-xs text-gray-900 text-center self-center">
                    {s.wins}-{s.losses}
                  </span>
                  <span className="text-xs text-gray-900 text-center self-center">
                    {s.win_L10}-{s.loss_L10}
                  </span>
                  <span
                    className={`text-xs text-center self-center ${
                      s.streak > 0
                        ? "text-green-500"
                        : s.streak < 0
                          ? "text-red-600"
                          : "text-gray-400"
                    }`}
                  >
                    {formatStreak(s.streak)}
                  </span>
                </Link>
              );
            })}
          </>
        )}
      </div>
    </div>
  );
}
