import { useEffect, useState } from "react";
import { usePlayerVsOpponent } from "../../hooks/usePlayerVsOpponent";
import { useTeamSchedule } from "../../hooks/useTeamSchedule";
import { useTeams } from "../../hooks/useTeams";
import type { PlayerDetail } from "../../types/players";
import EmptyState from "../ui/EmptyState";
import ErrorPage from "../ui/ErrorPage";
import LoadingPage from "../ui/LoadingPage";
import PlayerStatLineRow, { PlayerStatLineHeader } from "./PlayerStatLineRow";

type Props = { player: PlayerDetail };

export default function VsTeamTab({ player }: Props) {
  const teamId = player.team.id;
  const [selectedTeamId, setSelectedTeamId] = useState(0);

  const { data: schedule } = useTeamSchedule(teamId);
  const { data: allTeams } = useTeams();
  const { data: games, isLoading, error } = usePlayerVsOpponent(player.id, selectedTeamId);

  useEffect(() => {
    if (selectedTeamId !== 0 || !schedule) return;
    const { upcoming, recent } = schedule;
    let defaultOpp = 0;
    if (upcoming.length > 0) {
      const g = upcoming[0];
      defaultOpp = g.home_team_id !== teamId ? g.home_team_id : g.away_team_id;
    } else if (recent.length > 0) {
      const g = recent[0];
      defaultOpp = g.home_team_id !== teamId ? g.home_team_id : g.away_team_id;
    }
    if (defaultOpp > 0) setSelectedTeamId(defaultOpp);
  }, [schedule, teamId, selectedTeamId]);

  const otherTeams = (allTeams ?? [])
    .filter((t) => t.id !== teamId)
    .sort((a, b) => a.name.localeCompare(b.name));

  const teamMap = new Map(allTeams?.map((t) => [t.id, t.code]) ?? []);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex justify-center mt-2">
        <select
          value={selectedTeamId}
          onChange={(e) => setSelectedTeamId(Number(e.target.value))}
          className="border border-amber-500 rounded px-2 py-1 text-sm text-gray-900 bg-white"
        >
          <option value={0} disabled>
            Select opponent
          </option>
          {otherTeams.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name}
            </option>
          ))}
        </select>
      </div>

      {selectedTeamId === 0 ? (
        <EmptyState />
      ) : isLoading ? (
        <LoadingPage />
      ) : error ? (
        <ErrorPage />
      ) : !games || games.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="overflow-x-auto bg-white">
          <div className="overflow-y-auto">
            <PlayerStatLineHeader />
            {games.map((g) => (
              <PlayerStatLineRow
                key={g.game_id}
                game={g}
                teamCode={teamMap.get(g.opponent_team_id)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
