import type { GameResult } from "../../../types/games";
import { useGameBoxScore } from "../../../hooks/useGameBoxScore";
import EmptyState from "../../ui/EmptyState";
import ErrorPage from "../../ui/ErrorPage";
import LoadingPage from "../../ui/LoadingPage";
import PlayerBoxScoreRow, { BoxScoreHeader } from "./PlayerBoxScoreRow";

type Props = {
  game: GameResult;
};

export default function BoxScoreTab({ game }: Props) {
  const { data: players, isLoading, error } = useGameBoxScore(game.id);

  if (isLoading) return <LoadingPage />;
  if (error) return <ErrorPage />;
  if (!players || players.length === 0) return <EmptyState />;

  // Partition by team — backend already orders by team_id, points desc.
  const homePlayers = players.filter((p) => p.team_id === game.home_team_id);
  const awayPlayers = players.filter((p) => p.team_id === game.away_team_id);

  return (
    <div className="flex flex-col gap-6 overflow-x-auto">
      <section>
        <h3 className="inline-block text-[10px] sm:text-xs lg:text-sm font-brand text-sky-600 bg-gray-900 border-t border-l border-r border-amber-500 px-2 py-0.5 rounded-t ml-1">
          {game.home_team.code}
        </h3>
        <BoxScoreHeader />
        {homePlayers.map((p) => (
          <PlayerBoxScoreRow key={p.player_id} player={p} />
        ))}
      </section>

      <section>
        <h3 className="inline-block text-[10px] sm:text-xs lg:text-sm font-brand text-sky-600 bg-gray-900 border-t border-l border-r border-amber-500 px-2 py-0.5 rounded-t ml-1">
          {game.away_team.code}
        </h3>
        <BoxScoreHeader />
        {awayPlayers.map((p) => (
          <PlayerBoxScoreRow key={p.player_id} player={p} />
        ))}
      </section>
    </div>
  );
}
