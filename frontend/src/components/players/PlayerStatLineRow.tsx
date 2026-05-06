import { Link } from "react-router";
import type { PlayerGameStatWithContext } from "../../types/players";
import TeamLogo from "../teams/TeamLogo";

type Props = {
  game: PlayerGameStatWithContext;
  teamCode: string | undefined;
};

const COL_GRID =
  "grid w-fit sm:w-full lg:w-full grid-cols-[5rem_3rem_2.5rem_2.5rem_2.5rem_2.5rem_2.5rem_2.5rem_3rem_3rem_3rem_3rem] sm:grid-cols-[1fr_3rem_2.5rem_2.5rem_2.5rem_2.5rem_2.5rem_2.5rem_3rem_3rem_3rem_3rem]";
const CELL = "text-xs text-gray-900 text-center self-center px-1";

export function PlayerStatLineHeader() {
  return (
    <div
      className={`${COL_GRID} sticky top-0 z-10 bg-gray-900 border border-amber-500 px-2 py-1.5 divide-x divide-amber-500 w-fit sm:w-full lg:w-full`}
    >
      {[
        "DATE",
        "OPP",
        "MIN",
        "PTS",
        "REB",
        "AST",
        "STL",
        "BLK",
        "FG%",
        "3P%",
        "FT%",
        "+/-",
      ].map((h) => (
        <span
          key={h}
          className="text-[10px] font-brand text-sky-600 uppercase tracking-wide text-center px-1"
        >
          {h}
        </span>
      ))}
    </div>
  );
}

export default function PlayerStatLineRow({ game, teamCode }: Props) {
  const plusMinusClass =
    game.plus_minus > 0
      ? "text-xs text-green-500 text-center self-center px-1"
      : game.plus_minus < 0
        ? "text-xs text-red-600 text-center self-center px-1"
        : CELL;

  return (
    <Link
      to={`/games/${game.game_id}`}
      className={`${COL_GRID} bg-white border-b border-b-amber-500/20 px-2 py-1.5 hover:bg-amber-500/10 transition-colors divide-x divide-amber-500/20`}
    >
      <span className={CELL}>{game.game_date}</span>
      <span className="flex items-center justify-center self-center px-1">
        <TeamLogo
          size="sm"
          teamId={game.opponent_team_id}
          alt={teamCode}
          className="shrink-0"
        />
      </span>
      <span className={CELL}>{game.min}</span>
      <span className={CELL}>{game.points}</span>
      <span className={CELL}>{game.tot_reb}</span>
      <span className={CELL}>{game.asts}</span>
      <span className={CELL}>{game.stls}</span>
      <span className={CELL}>{game.blks}</span>
      <span className={CELL}>{(game.fgp * 100).toFixed(0)}%</span>
      <span className={CELL}>{(game.tpp * 100).toFixed(0)}%</span>
      <span className={CELL}>{(game.ftp * 100).toFixed(0)}%</span>
      <span className={plusMinusClass}>
        {game.plus_minus > 0 ? `+${game.plus_minus}` : game.plus_minus}
      </span>
    </Link>
  );
}
