import { useParams } from "react-router";
import { useTeamRoster } from "../../hooks/useTeamRoster";
import type { Player } from "../../types/players";
import PlayerHeadshot from "../players/PlayerHeadshot";
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
      <div className="stats-tab-container grid grid-cols-1 scroll-auto">
        {roster.map((player) => (
          <div className="player-tab-container grid grid-cols-2 justify-center hover:bg-amber-500">
            <PlayerHeadshot
              size="sm"
              playerId={player.id}
              alt={player.first_name + " " + player.last_name}
            ></PlayerHeadshot>
            <div className="text-center flex">
              {player.first_name + " " + player.last_name}
            </div>
          </div>
        ))}
      </div>
    );
  }
}
