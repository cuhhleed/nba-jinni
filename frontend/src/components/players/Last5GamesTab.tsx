import { usePlayerLast5Games } from "../../hooks/usePlayerLast5Games";
import { useTeams } from "../../hooks/useTeams";
import EmptyState from "../ui/EmptyState";
import ErrorPage from "../ui/ErrorPage";
import LoadingPage from "../ui/LoadingPage";
import PlayerStatLineRow, { PlayerStatLineHeader } from "./PlayerStatLineRow";

type Props = { playerId: number };

export default function Last5GamesTab({ playerId }: Props) {
  const { data: games, isLoading, error } = usePlayerLast5Games(playerId);
  const { data: teams } = useTeams();

  if (isLoading) return <LoadingPage />;
  if (error) return <ErrorPage />;
  if (!games || games.length === 0) return <EmptyState />;

  const teamMap = new Map(teams?.map((t) => [t.id, t.code]) ?? []);

  return (
    <div className="overflow-x-auto bg-white">
      <div className="overflow-y-auto">
        <PlayerStatLineHeader />
        {games.map((g) => (
          <PlayerStatLineRow key={g.game_id} game={g} teamCode={teamMap.get(g.opponent_team_id)} />
        ))}
      </div>
    </div>
  );
}
