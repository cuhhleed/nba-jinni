import { Link, useParams } from "react-router";
import { useTeamRoster } from "../../hooks/useTeamRoster";
import type { Player } from "../../types/players";
import PlayerHeadshot from "../players/PlayerHeadshot";
import CornerFrame from "../ui/CornerFrame";
import EmptyState from "../ui/EmptyState";
import ErrorPage from "../ui/ErrorPage";
import LoadingPage from "../ui/LoadingPage";

export default function RosterTab() {
  const { id } = useParams();
  const teamId = Number(id);

  const { data: teamRoster, isLoading, error } = useTeamRoster(teamId);
  if (isLoading) {
    return <LoadingPage />;
  } else if (error) {
    return <ErrorPage />;
  } else if (teamRoster) {
    const roster = buildRoster(teamRoster);
    return roster;
  }
}

function buildRoster(roster: Player[] | null) {
  if (!roster) {
    return <EmptyState />;
  } else {
    return (
      <div className="stats-tab-container grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-3 scroll-auto">
        {roster.map((player) => (
          <CornerFrame
            size="sm"
            className="player-tab-container m-4 bg-gray-900 hover:bg-amber-500 border-4 border-amber-500 border-double hover:shadow-lg hover:scale-105 transition-all"
          >
            <Link
              className="flex flex-col items-center justify-center"
              to={`/players/${player.id}`}
              key={player.id}
            >
              <PlayerHeadshot
                size="sm"
                playerId={player.id}
                alt={player.first_name + " " + player.last_name}
                className="my-1"
              ></PlayerHeadshot>
              <div className="text-center my-2 text-sm text-sky-600">
                {player.first_name + " " + player.last_name}
              </div>
            </Link>
          </CornerFrame>
        ))}
      </div>
    );
  }
}
