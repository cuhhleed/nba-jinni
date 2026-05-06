import { Link } from "react-router";
import { useH2HGames } from "../../../hooks/useH2HGames";
import type { GameWithTeamStats } from "../../../types/games";
import TeamLogo from "../../teams/TeamLogo";
import EmptyState from "../../ui/EmptyState";
import ErrorPage from "../../ui/ErrorPage";
import LoadingPage from "../../ui/LoadingPage";

type Props = {
  homeTeamId: number;
  awayTeamId: number;
};

function H2HGameRow({ game }: { game: GameWithTeamStats }) {
  const homeStat = game.home_team_stat;
  const awayStat = game.away_team_stat;
  const isCompleted = homeStat && awayStat;

  return (
    <Link
      to={`/games/${game.id}`}
      className="grid grid-cols-[auto_1fr_auto_1fr_auto] items-center gap-2 px-3 py-2 border-b border-amber-500/20 hover:bg-amber-500/10 transition-colors"
    >
      <span className="text-[10px] sm:text-xs text-gray-900">{game.game_date}</span>
      <div className="flex items-center justify-end gap-1">
        <TeamLogo size="sm" teamId={game.home_team_id} />
      </div>
      {isCompleted ? (
        <span
          className={`text-xs sm:text-sm font-brand font-medium text-center ${
            homeStat.points > awayStat.points
              ? "text-green-500"
              : homeStat.points < awayStat.points
                ? "text-red-600"
                : "text-sky-600"
          }`}
        >
          {homeStat.points}–{awayStat.points}
        </span>
      ) : (
        <span className="text-[10px] sm:text-xs text-sky-600 text-center">
          Upcoming
        </span>
      )}
      <div className="flex items-center justify-start gap-1">
        <TeamLogo size="sm" teamId={game.away_team_id} />
      </div>
      {isCompleted ? (
        <span className="text-[10px] sm:text-xs text-sky-600 rounded px-1 py-0.5 text-center">
          Final
        </span>
      ) : (
        <span className="text-[10px] sm:text-xs text-sky-600 text-center">
          Upcoming
        </span>
      )}
    </Link>
  );
}

export default function H2HTab({ homeTeamId, awayTeamId }: Props) {
  const { data: games, isLoading, error } = useH2HGames(homeTeamId, awayTeamId);

  if (isLoading) return <LoadingPage />;
  if (error) return <ErrorPage />;
  if (!games || games.length === 0) return <EmptyState />;

  return (
    <div className="flex flex-col bg-white">
      {games.map((game) => (
        <H2HGameRow key={game.id} game={game} />
      ))}
    </div>
  );
}
