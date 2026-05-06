import { Link, useParams } from "react-router";
import { useTeamSchedule } from "../../hooks/useTeamSchedule";
import type { GameBase, GameWithTeamStats } from "../../types/games";
import EmptyState from "../ui/EmptyState";
import ErrorPage from "../ui/ErrorPage";
import LoadingPage from "../ui/LoadingPage";
import TeamLogo from "./TeamLogo";

export default function GamesTab() {
  const { id } = useParams();
  const teamId = Number(id);

  const { data: teamSchedule, isLoading, error } = useTeamSchedule(teamId);
  if (isLoading) {
    return <LoadingPage />;
  } else if (error) {
    return <ErrorPage />;
  } else if (teamSchedule) {
    return (
      <div className="game-tab-container bg-white grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2">
        <div className="recent-games-container flex flex-col">
          <span className="text-sky-600 bg-gray-900 text-center sticky top-0">
            Recent
          </span>
          {buildRecentGames(teamSchedule.recent, teamId)}
        </div>

        <div className="upcoming-games-container flex flex-col">
          <span className="text-sky-600 bg-gray-900 text-center sticky top-0">
            Upcoming
          </span>
          {buildNextGames(teamSchedule?.upcoming, teamId)}
        </div>
      </div>
    );
  }
}

function buildRecentGames(pastGames: GameWithTeamStats[] | null, teamId: number) {
  if (!pastGames || pastGames.length == 0) {
    return <EmptyState />;
  } else {
    return (
      <div className="past-games-container border-amber-500 sm:border-r lg:border-r">
        {pastGames.map((game) => buildRecentGame(game, teamId))}
      </div>
    );
  }
}

function buildRecentGame(game: GameWithTeamStats, teamId: number) {
  const [myTeamStat, oppTeamStat] =
    game.home_team_id == teamId
      ? [game.home_team_stat, game.away_team_stat]
      : [game.away_team_stat, game.home_team_stat];

  if (myTeamStat && oppTeamStat) {
    const won = myTeamStat.points > oppTeamStat.points;
    return (
      <div className="past-game-container  hover:bg-amber-500/10 py-2">
        <div className="mx-4 grid grid-cols-3 items-center justify-left">
          <Link
            to={`/games/${game.id}`}
            key={game.id}
            className="grid grid-cols-2 col-span-2"
          >
            <span>{game.game_date}</span>
            <TeamLogo size="sm" teamId={oppTeamStat.team_id}></TeamLogo>
          </Link>
          <span className={won ? "text-green-500" : "text-red-600"}>
            {myTeamStat.points}-{oppTeamStat.points}
          </span>
        </div>
      </div>
    );
  }
}

function buildNextGames(nextGames: GameBase[], teamId: number) {
  if (!nextGames || nextGames.length == 0) {
    return <EmptyState />;
  } else {
    return (
      <div className="next-games-container">
        {nextGames.map((game) => buildNextGame(game, teamId))}
      </div>
    );
  }
}

function buildNextGame(game: GameBase, teamId: number) {
  const [oppId, isHome] =
    game.home_team_id != teamId
      ? [game.home_team_id, true]
      : [game.away_team_id, false];

  return (
    <div className="next-game-container grid grid-cols-3 text-gray-900">
      <span>{game.game_date}</span>
      <TeamLogo size="sm" teamId={oppId}></TeamLogo>
      <span className="text-gray-900">{isHome ? "(H)" : "(A)"}</span>
    </div>
  );
}
