import { Link } from "react-router";
import type { GamePreview, GameWithTeamStats } from "../../../types/games";
import { useTeamSchedule } from "../../../hooks/useTeamSchedule";
import EmptyState from "../../ui/EmptyState";
import ErrorPage from "../../ui/ErrorPage";
import LoadingPage from "../../ui/LoadingPage";
import TeamLogo from "../../teams/TeamLogo";

type Props = {
  game: GamePreview;
};

function RecentGameRow({
  game,
  perspectiveTeamId,
}: {
  game: GameWithTeamStats;
  perspectiveTeamId: number;
}) {
  const [myTeamStat, oppTeamStat] =
    game.home_team_id === perspectiveTeamId
      ? [game.home_team_stat, game.away_team_stat]
      : [game.away_team_stat, game.home_team_stat];

  if (!myTeamStat || !oppTeamStat) return null;

  const won = myTeamStat.points > oppTeamStat.points;

  return (
    <Link
      to={`/games/${game.id}`}
      className="grid grid-cols-3 items-center px-2 sm:px-3 py-1.5 border-b border-amber-500/20 hover:bg-amber-500/10 transition-colors"
    >
      <span className="text-[10px] sm:text-xs text-gray-900">{game.game_date}</span>
      <div className="flex justify-center">
        <TeamLogo size="sm" teamId={oppTeamStat.team_id} />
      </div>
      <span
        className={`text-[10px] sm:text-xs font-medium text-right ${
          won ? "text-green-500" : "text-red-600"
        }`}
      >
        {myTeamStat.points}–{oppTeamStat.points}
      </span>
    </Link>
  );
}

function TeamLast5({
  teamId,
  teamCode,
}: {
  teamId: number;
  teamCode: string;
}) {
  const { data: schedule, isLoading, error } = useTeamSchedule(teamId);

  if (isLoading) return <LoadingPage />;
  if (error) return <ErrorPage />;

  const recent = schedule?.recent?.slice(0, 5) ?? [];

  return (
    <div className="flex flex-col">
      <span className="text-[10px] sm:text-xs text-sky-600 bg-gray-900 text-center sticky top-0 py-1 font-brand">
        {teamCode} — Last 5
      </span>
      {recent.length === 0 ? (
        <EmptyState />
      ) : (
        recent.map((game) => (
          <RecentGameRow
            key={game.id}
            game={game}
            perspectiveTeamId={teamId}
          />
        ))
      )}
    </div>
  );
}

export default function PreviewLast5Tab({ game }: Props) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 bg-white">
      <div className="sm:border-r border-amber-500">
        <TeamLast5
          teamId={game.home_team_id}
          teamCode={game.home_team.code}
        />
      </div>
      <div>
        <TeamLast5
          teamId={game.away_team_id}
          teamCode={game.away_team.code}
        />
      </div>
    </div>
  );
}
