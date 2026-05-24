import { Link } from "react-router";
import type { LiveScoreboardEntry } from "../../types/games";
import type { Team } from "../../types/teams";
import TeamLogo from "../teams/TeamLogo";
import CarpetBadge from "../ui/CarpetBadge";
import FreshnessBadge from "../ui/FreshnessBadge";

type Props = {
  entry: LiveScoreboardEntry;
  teamMap: Map<number, Team>;
  isStale: boolean;
  lastUpdatedAt: string;
};

export default function GameCarpetBadge({
  entry,
  teamMap,
  isStale,
  lastUpdatedAt,
}: Props) {
  const home = teamMap.get(entry.home_team_id);
  const away = teamMap.get(entry.away_team_id);

  const homeWon =
    entry.state === "final" && entry.home_score != null && entry.away_score != null
      ? entry.home_score > entry.away_score
      : null;

  const tipoffLocal = new Date(entry.tipoff_at).toLocaleTimeString([], {
    hour: "numeric",
    minute: "2-digit",
  });

  return (
    <Link
      to={`/games/${entry.id}`}
      className="block flex-shrink-0 w-[calc((100%-32px)/2)] sm:w-[calc((100%-64px)/3)] lg:w-[calc((100%-96px)/4)] group"
    >
      <CarpetBadge hoverable size="sm" className="p-2 h-full group-hover:bg-amber-500">
        {entry.state === "live" && (
          <div className="flex items-center gap-1.5 mb-1">
            <span className="w-2 h-2 rounded-full bg-red-600 animate-pulse inline-block" />
            {isStale && (
              <FreshnessBadge isStale lastUpdatedAt={lastUpdatedAt} size="sm" />
            )}
          </div>
        )}

        <div
          className={`flex flex-col gap-1 mt-1 ${
            entry.state !== "live" ? "mt-2" : ""
          } ${entry.state === "scheduled" ? "items-center" : ""}`}
        >
          <div className="flex items-center justify-between gap-1">
            <div className="flex items-center gap-1 min-w-0">
              <TeamLogo teamId={entry.home_team_id} size="sm" className="shrink-0" />
              <span className="text-xs font-brand text-sky-500 truncate">
                {home?.code ?? "—"}
              </span>
            </div>
            {entry.state !== "scheduled" && (
              <span
                className={`text-sm font-bold shrink-0 ${
                  entry.state === "final"
                    ? homeWon
                      ? "text-green-500"
                      : "text-red-600"
                    : "text-gray-100"
                }`}
              >
                {entry.home_score ?? "—"}
              </span>
            )}
          </div>

          <div className="flex items-center justify-between gap-1">
            <div className="flex items-center gap-1 min-w-0">
              <TeamLogo teamId={entry.away_team_id} size="sm" className="shrink-0" />
              <span className="text-xs font-brand text-sky-500 truncate">
                {away?.code ?? "—"}
              </span>
            </div>
            {entry.state !== "scheduled" && (
              <span
                className={`text-sm font-bold shrink-0 ${
                  entry.state === "final"
                    ? homeWon === false
                      ? "text-green-500"
                      : "text-red-600"
                    : "text-gray-100"
                }`}
              >
                {entry.away_score ?? "—"}
              </span>
            )}
          </div>
        </div>

        {entry.state === "final" && (
          <div className="text-center">
            <p className="text-[11px] text-amber-500 group-hover:text-sky-500 text-center mt-3">
              Final
            </p>
          </div>
        )}

        {entry.state === "scheduled" && (
          <div className="text-center">
            <span className="text-[10px] text-amber-500 group-hover:text-sky-500 text-center mt-1.5">
              {tipoffLocal}
            </span>
          </div>
        )}

        {entry.state === "live" && entry.game_clock && (
          <div className="text-center">
            <span className="text-[10px] text-amber-500 group-hover:text-sky-500 text-center mt-1">
              Q{entry.period}{" "}
            </span>
            <span className="text-[10px] text-amber-500 group-hover:text-sky-500 text-center mt-1">
              {entry.game_clock.slice(2, 4)}:{entry.game_clock.slice(5, 7)}
            </span>
          </div>
        )}
      </CarpetBadge>
    </Link>
  );
}
