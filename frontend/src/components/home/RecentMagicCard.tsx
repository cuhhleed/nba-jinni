import { Link } from "react-router";
import type { RecentPerformance } from "../../types/players";
import PlayerHeadshot from "../players/PlayerHeadshot";
import TeamLogo from "../teams/TeamLogo";
import CarpetBadge from "../ui/CarpetBadge";

type Props = {
  performance: RecentPerformance;
};

type StatCellProps = { label: string; value: number };

function StatCell({ label, value }: StatCellProps) {
  return (
    <div className="flex flex-col items-center">
      <span className="text-[10px] uppercase tracking-wide text-amber-500 group-hover:text-sky-500">
        {label}
      </span>
      <span className="text-sm font-bold text-sky-500">{value}</span>
    </div>
  );
}

export default function RecentMagicCard({ performance }: Props) {
  return (
    <Link to={`/games/${performance.game_id}`} className="block m-3 group">
      <CarpetBadge hoverable className="p-3 group-hover:bg-amber-500">
        <TeamLogo
          teamId={performance.team_id}
          size="sm"
          className="absolute top-2 right-2"
        />

        <div className="flex items-center gap-3 pr-8">
          <PlayerHeadshot
            playerId={performance.player_id}
            size="md"
            className="shrink-0"
          />
          <span className="text-sm font-semibold text-sky-500 truncate">
            {performance.full_name}
          </span>
        </div>

        <div className="mt-2 flex flex-col gap-1">
          <div className="grid grid-cols-5 gap-2">
            <StatCell label="PTS" value={performance.points} />
            <StatCell label="REB" value={performance.tot_reb} />
            <StatCell label="AST" value={performance.asts} />
            <StatCell label="STL" value={performance.stls} />
            <StatCell label="BLK" value={performance.blks} />
            <div />
          </div>
        </div>
      </CarpetBadge>
    </Link>
  );
}
