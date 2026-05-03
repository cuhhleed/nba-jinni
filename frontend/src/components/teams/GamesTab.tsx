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
      <div className="game-tab-container bg-white">
        <div className="games-titles-container sticky top-0 grid grid-cols-2 bg-gray-900 text-center">
          <span className="text-sky-600 border-r border-amber-500">Recent</span>
          <span className="text-sky-600">Upcoming</span>
        </div>

        <div className="games-container grid grid-cols-2">
          {buildRecentGames(teamSchedule.recent, teamId)}
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
      <div className="past-games-container border-r border-amber-500">
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
      <div className="past-game-container  hover:bg-amber-500">
        <Link to={`/games/${game.id}`} key={game.id}>
          <div className="mx-4 grid grid-cols-3 items-center justify-left">
            <span>{game.game_date}</span>
            <TeamLogo size="sm" teamId={oppTeamStat.team_id}></TeamLogo>
            <span className={won ? "text-green-500" : "text-red-600"}>
              {myTeamStat.points}-{oppTeamStat.points}
            </span>
          </div>
        </Link>
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
