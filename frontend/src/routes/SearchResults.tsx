import { Link, useSearchParams } from "react-router";
import PageContainer from "../components/layout/PageContainer";
import PlayerHeadshot from "../components/players/PlayerHeadshot";
import CarpetBadge from "../components/ui/CarpetBadge";
import EmptyState from "../components/ui/EmptyState";
import ErrorPage from "../components/ui/ErrorPage";
import LoadingPage from "../components/ui/LoadingPage";
import { usePlayerSearch } from "../hooks/usePlayerSearch";

export default function SearchResults() {
  const [searchParams] = useSearchParams();
  const q = searchParams.get("q") ?? "";
  const { data: players, isLoading, error } = usePlayerSearch(q);

  if (isLoading) return <LoadingPage />;
  if (error) return <ErrorPage />;

  return (
    <PageContainer>
      <h1 className="text-2xl text-center text-gray-900 font-semibold font-brand mb-1">
        Player Search
      </h1>
      <p className="text-center text-sm text-gray-500 mb-6">
        Results for:{" "}
        <span className="text-sky-600 font-medium">&ldquo;{q}&rdquo;</span>
      </p>

      {!players || players.length === 0 ? (
        <EmptyState message={`No players found for "${q}".`} />
      ) : (
        <div className="grid grid-cols-3 gap-2 sm:gap-3 lg:gap-4">
          {players.map((player) => (
            <CarpetBadge
              key={player.id}
              size="sm"
              className="p-2 sm:p-3 lg:p-4 grid grid-cols-1 text-center hover:bg-amber-500 m-2"
              hoverable
            >
              <Link to={`/players/${player.id}`}>
                <PlayerHeadshot
                  playerId={player.id}
                  alt={`${player.first_name} ${player.last_name}`}
                  className="mx-auto mb-1 sm:mb-2"
                />
                <h2 className="text-xs sm:text-sm lg:text-base font-semibold font-brand text-sky-500">
                  {player.first_name} {player.last_name}
                </h2>
              </Link>
            </CarpetBadge>
          ))}
        </div>
      )}
    </PageContainer>
  );
}
