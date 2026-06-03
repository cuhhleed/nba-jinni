import type { GameLive } from "../../../types/games";
import EmptyState from "../../ui/EmptyState";
import LivePlayerBoxScoreRow from "./LivePlayerBoxScoreRow";
import { BoxScoreHeader } from "./PlayerBoxScoreRow";

type Props = {
  game: GameLive;
};

export default function LiveBoxScoreTab({ game }: Props) {
  const home = [...game.home_player_stats].sort((a, b) => b.points - a.points);
  const away = [...game.away_player_stats].sort((a, b) => b.points - a.points);

  if (home.length === 0 && away.length === 0) return <EmptyState />;

  return (
    <div className="flex flex-col gap-6 overflow-x-auto">
      <section>
        <h3 className="inline-block text-[10px] sm:text-xs lg:text-sm font-brand text-sky-600 bg-gray-900 border-t border-l border-r border-amber-500 px-2 py-0.5 rounded-t ml-1">
          {game.home_team.code}
        </h3>
        <BoxScoreHeader />
        {home.map((p) => (
          <LivePlayerBoxScoreRow key={p.player_id} player={p} />
        ))}
      </section>

      <section>
        <h3 className="inline-block text-[10px] sm:text-xs lg:text-sm font-brand text-sky-600 bg-gray-900 border-t border-l border-r border-amber-500 px-2 py-0.5 rounded-t ml-1">
          {game.away_team.code}
        </h3>
        <BoxScoreHeader />
        {away.map((p) => (
          <LivePlayerBoxScoreRow key={p.player_id} player={p} />
        ))}
      </section>
    </div>
  );
}
