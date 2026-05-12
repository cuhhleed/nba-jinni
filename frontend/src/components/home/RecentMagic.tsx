import { useRecentTopPerformances } from "../../hooks/useRecentTopPerformances";
import ErrorState from "../ui/ErrorState";
import LoadingState from "../ui/LoadingState";
import RecentMagicCard from "./RecentMagicCard";

export default function RecentMagic() {
  const { data: performances, isLoading, error } = useRecentTopPerformances();

  return (
    <div>
      <h2 className="text-2xl font-bold text-amber-500 text-center mb-4">
        Recent Magic
      </h2>

      {isLoading && (
        <div className="flex justify-center py-6">
          <LoadingState />
        </div>
      )}
      {error && !isLoading && (
        <div className="flex justify-center py-6">
          <ErrorState />
        </div>
      )}
      {!isLoading && !error && performances?.length === 0 && (
        <p className="text-sm text-gray-400">
          No standout performances in the last two days.
        </p>
      )}
      {!isLoading && !error && performances && performances.length > 0 && (
        <div className="flex flex-col gap-4">
          {performances.map((p) => (
            <RecentMagicCard key={`${p.player_id}-${p.game_id}`} performance={p} />
          ))}
        </div>
      )}
    </div>
  );
}
