import { Link } from "react-router";
import type { PlayerLiveStat } from "../../../types/games";
import { CELL, COL_GRID } from "./PlayerBoxScoreRow";

type Props = {
  player: PlayerLiveStat;
};

function formatMinutes(raw: string): string {
  const match = raw.match(/^PT(\d+)M([\d.]+)S$/);
  if (!match) return raw;
  return `${match[1]}:${Math.floor(Number(match[2])).toString().padStart(2, "0")}`;
}

function pct(made: number, attempted: number): string {
  if (!attempted) return "0%";
  return `${Math.round((made / attempted) * 100)}%`;
}

export default function LivePlayerBoxScoreRow({ player }: Props) {
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
      <span className={CELL}>{formatMinutes(player.minutes)}</span>
      <span className={CELL}>{player.points}</span>
      <span className={CELL}>{player.rebounds}</span>
      <span className={CELL}>{player.assists}</span>
      <span className={CELL}>{player.steals}</span>
      <span className={CELL}>{player.blocks}</span>
      <span className={CELL}>{pct(player.fg_made, player.fg_attempted)}</span>
      <span className={CELL}>{pct(player.three_made, player.three_attempted)}</span>
      <span className={CELL}>{pct(player.ft_made, player.ft_attempted)}</span>
      <span className={CELL}>—</span>
    </div>
  );
}
