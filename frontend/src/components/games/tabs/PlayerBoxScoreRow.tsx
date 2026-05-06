import { Link } from "react-router";
import type { PlayerGameBoxScore } from "../../../types/games";

type Props = {
  player: PlayerGameBoxScore;
};

const COL_GRID =
  "grid w-fit sm:w-full lg:w-full grid-cols-[9rem_2.5rem_2.5rem_2.5rem_2.5rem_2.5rem_2.5rem_3rem_3rem_3rem_3rem] sm:grid-cols-[1fr_2.5rem_2.5rem_2.5rem_2.5rem_2.5rem_2.5rem_3rem_3rem_3rem_3rem]";
const CELL = "text-xs text-gray-900 text-center self-center px-1";

export function BoxScoreHeader() {
  return (
    <div
      className={`${COL_GRID} sticky top-0 z-10 bg-gray-900 border border-amber-500 px-2 py-1.5 divide-x divide-amber-500 w-fit sm:w-full lg:w-full`}
    >
      {["PLAYER", "MIN", "PTS", "REB", "AST", "STL", "BLK", "FG%", "3P%", "FT%", "+/-"].map(
        (h) => (
          <span
            key={h}
            className="text-[10px] font-brand text-sky-600 uppercase tracking-wide text-center px-1"
          >
            {h}
          </span>
        )
      )}
    </div>
  );
}

export default function PlayerBoxScoreRow({ player }: Props) {
  const plusMinusClass =
    player.plus_minus > 0
      ? "text-xs text-green-500 text-center self-center px-1"
      : player.plus_minus < 0
        ? "text-xs text-red-600 text-center self-center px-1"
        : CELL;

  return (
    <div
      className={`${COL_GRID} bg-white border-b border-b-amber-500/20 px-2 py-1.5 divide-x divide-amber-500/20`}
    >
      <Link
        to={`/players/${player.player_id}`}
        className={`${CELL} hover:text-amber-500 transition-colors`}
      >
        {player.first_name} {player.last_name}
      </Link>
      <span className={CELL}>{player.min}</span>
      <span className={CELL}>{player.points}</span>
      <span className={CELL}>{player.tot_reb}</span>
      <span className={CELL}>{player.asts}</span>
      <span className={CELL}>{player.stls}</span>
      <span className={CELL}>{player.blks}</span>
      <span className={CELL}>{(player.fgp * 100).toFixed(0)}%</span>
      <span className={CELL}>{(player.tpp * 100).toFixed(0)}%</span>
      <span className={CELL}>{(player.ftp * 100).toFixed(0)}%</span>
      <span className={plusMinusClass}>
        {player.plus_minus > 0 ? `+${player.plus_minus}` : player.plus_minus}
      </span>
    </div>
  );
}