import { Link } from "react-router";
import logoPlaceholder from "../assets/logo-placeholder.svg";
import PageContainer from "../components/layout/PageContainer";
import ErrorPage from "../components/ui/ErrorPage";
import LoadingPage from "../components/ui/LoadingPage";
import { useTeams } from "../hooks/useTeams";

export default function Teams() {
  const { data: teams, isLoading, error } = useTeams();

  if (isLoading) {
    return <LoadingPage />;
  } else if (error) {
    return <ErrorPage />;
  } else if (teams) {
    const eastern = teams.filter((t) => t.conference === "East");
    const western = teams.filter((t) => t.conference === "West");

    const renderGrid = (conferenceTeams: typeof teams) => (
      <div className="grid grid-cols-3 gap-2 sm:gap-3 lg:gap-4">
        {conferenceTeams.map((team) => (
          <Link
            to={`/teams/${team.id}`}
            key={team.id}
            className="team-badge p-2 sm:p-3 lg:p-4 grid grid-cols-1 border rounded-xl text-center bg-white hover:bg-amber-400 hover:shadow-lg hover:scale-105 transition-all"
          >
            <img
              src={logoPlaceholder}
              alt={`${team.name} logo`}
              className="w-8 h-8 sm:w-12 sm:h-12 lg:w-16 lg:h-16 mx-auto mb-1 sm:mb-2"
            />
            <h2 className="text-xs sm:text-sm lg:text-base font-semibold font-brand text-gray-900">
              {team.name}
            </h2>
            <h3 className="text-xs sm:text-sm font-light text-gray-900">
              ({team.code})
            </h3>
          </Link>
        ))}
      </div>
    );

    return (
      <PageContainer>
        <h1 className="text-2xl text-center text-gray-900 font-semibold font-brand mb-4">
          NBA Teams
        </h1>
        <section className="mb-10">
          <h2 className="text-xl font-semibold font-brand mb-4">Eastern Conference</h2>
          {renderGrid(eastern)}
        </section>
        <section>
          <h2 className="text-xl font-semibold font-brand mb-4">Western Conference</h2>
          {renderGrid(western)}
        </section>
      </PageContainer>
    );
  }
}
