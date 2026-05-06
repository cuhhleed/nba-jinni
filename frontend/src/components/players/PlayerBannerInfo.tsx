import { Link, useParams } from "react-router";
import { usePlayerInfo } from "../../hooks/usePlayerInfo";
import TeamLogo from "../teams/TeamLogo";
import ErrorPage from "../ui/ErrorPage";
import LoadingPage from "../ui/LoadingPage";
import PlayerHeadshot from "./PlayerHeadshot";

export default function PlayerBannerInfo() {
  const { id } = useParams();
  const playerId = Number(id);

  const { data: playerInfo, isLoading, error } = usePlayerInfo(playerId);
  if (isLoading) {
    return <LoadingPage />;
  } else if (error) {
    return <ErrorPage />;
  } else if (playerInfo) {
    const playerTeamId = playerInfo.team.id;
    let hidden = "";
    if (!playerTeamId || playerTeamId == 0) {
      hidden = "invisible";
    }
    return (
      <div className="player-banner-container relative flex flex-col items-center text-sky-600">
        <Link
          to={`/teams/${playerTeamId}`}
          className={`absolute top-0 left-0 group hover:bg-amber-500 flex flex-col items-center ${hidden} rounded-md`}
        >
          <TeamLogo teamId={playerTeamId} size="sm" />
          <span className="text-center text-xs group-hover:text-gray-900">
            {playerInfo.team.code}
          </span>
        </Link>
        <PlayerHeadshot playerId={playerId} size="lg" />
        <span>
          {playerInfo.first_name} {playerInfo.last_name}
        </span>
      </div>
    );
  }
}
