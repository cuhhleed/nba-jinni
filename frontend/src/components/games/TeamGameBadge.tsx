import { Link } from "react-router";
import type { TeamWithStanding, TeamWithStandingAndAverage } from "../../types/games";
import TeamLogo from "../teams/TeamLogo";

type Props = {
  team: TeamWithStanding | TeamWithStandingAndAverage;
};

export default function TeamGameBadge({ team }: Props) {
  const { standing } = team;

  let wlColor = "text-gray-900";
  if (standing) {
    if (standing.wins > standing.losses) {
      wlColor = "text-green-500";
    } else if (standing.wins < standing.losses) {
      wlColor = "text-red-600";
    }
  }

  return (
    <Link
      to={`/teams/${team.id}`}
      className="flex flex-col items-center gap-1 hover:opacity-80 transition-opacity"
    >
      <TeamLogo
        size="md"
        teamId={team.id}
        alt={team.name}
        className="mx-auto"
      />
      <span className="text-[10px] sm:text-xs lg:text-sm font-semibold font-brand text-sky-600 text-center">
        {team.name}
      </span>
      <span className="text-[10px] sm:text-xs text-sky-600 text-center">
        {team.code}
      </span>
      {standing && (
        <span className={`text-[10px] sm:text-xs lg:text-sm font-medium ${wlColor}`}>
          {standing.wins}–{standing.losses}
        </span>
      )}
    </Link>
  );
}
