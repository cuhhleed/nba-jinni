import { useParams } from "react-router";
import logoPlaceholder from "../assets/logo-placeholder-2.svg";
import PageContainer from "../components/layout/PageContainer";
import TeamStandingWidget from "../components/standings/TeamStandingWidget";
import StatsTab from "../components/teams/StatsTab";
import CornerFrame from "../components/ui/CornerFrame";
import ErrorPage from "../components/ui/ErrorPage";
import LoadingPage from "../components/ui/LoadingPage";
import { useTeamInfo } from "../hooks/useTeamInfo";

export default function TeamDetail() {
  const { id } = useParams();
  const teamId = Number(id);

  const { data: teamInfo, isLoading, error } = useTeamInfo(teamId);
  if (isLoading) {
    return <LoadingPage />;
  } else if (error) {
    return <ErrorPage />;
  } else if (teamInfo) {
    const teamInfoBlock = (
      <PageContainer>
        <div>
          <div className="team-block-container grid grid-cols-2 bg-sky-500">
            <CornerFrame className="team-badge flex-1 p-2 sm:p-3 lg:p-4 grid grid-cols-1 bg-gray-900 border border-amber-800">
              <img
                src={logoPlaceholder}
                alt={`${teamInfo.name} logo`}
                className="w-16 h-16 sm:w-20 sm:h-20 lg:w-24 lg:h-20 mx-auto mb-1 mt-6"
              />
              <h2 className="text-xs sm:text-sm lg:text-base font-semibold font-brand text-amber-400 text-center mt-4">
                {teamInfo.name}
                <h3 className="text-xs sm:text-sm font-light text-amber-400 text-center">
                  ({teamInfo.code})
                </h3>
              </h2>
            </CornerFrame>
            <TeamStandingWidget standing={teamInfo.standing} />
          </div>
          <StatsTab />
        </div>
      </PageContainer>
    );

    return teamInfoBlock;
  }
}
