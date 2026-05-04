import { useState } from "react";
import { useParams } from "react-router";
import PageContainer from "../components/layout/PageContainer";
import TeamStandingWidget from "../components/standings/TeamStandingWidget";
import GamesTab from "../components/teams/GamesTab";
import RosterTab from "../components/teams/RosterTab";
import StatsTab from "../components/teams/StatsTab";
import TeamLogo from "../components/teams/TeamLogo";
import CarpetBadge from "../components/ui/CarpetBadge";
import ErrorPage from "../components/ui/ErrorPage";
import LoadingPage from "../components/ui/LoadingPage";
import PillTabs from "../components/ui/PillTabs";
import { useTeamInfo } from "../hooks/useTeamInfo";

const TABS = [
  { id: "schedule", label: "Schedule" },
  { id: "roster", label: "Roster" },
];

export default function TeamDetail() {
  const { id } = useParams();
  const teamId = Number(id);
  const [activeTab, setActiveTab] = useState("schedule");

  const { data: teamInfo, isLoading, error } = useTeamInfo(teamId);
  if (isLoading) {
    return <LoadingPage />;
  } else if (error) {
    return <ErrorPage />;
  } else if (teamInfo) {
    return (
      <PageContainer>
        <div>
          <div className="team-block-container grid grid-cols-1">
            <CarpetBadge
              size="lg"
              className="team-badge flex-1 p-2 sm:p-3 lg:p-4 grid grid-cols-2 mx-2 lg:my-2"
            >
              <div className="team-container p-2 sm:p-3 lg:p-4 mx-6 rounded-lg grid grid-cols-1 content-center">
                <TeamLogo
                  size="lg"
                  teamId={teamId}
                  alt={teamInfo.name}
                  className="mx-auto mb-1 mt-6"
                ></TeamLogo>
                <h2 className="text-xs sm:text-sm lg:text-base font-semibold font-brand text-sky-600 text-center mt-4">
                  {teamInfo.name}
                  <h3 className="text-xs sm:text-sm font-light text-sky-600 text-center">
                    ({teamInfo.code})
                  </h3>
                </h2>
              </div>
              <TeamStandingWidget standing={teamInfo.standing} />
            </CarpetBadge>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3">
            <StatsTab />

            <div className="tab-window-container flex flex-col col-span-2 max-h-[44vh]">
              <div className="flex justify-center mt-6">
                <PillTabs
                  className="bg-gray-900"
                  tabs={TABS}
                  activeTab={activeTab}
                  onChange={setActiveTab}
                />
              </div>
              <div className="mt-6 flex-1 min-h-0 overflow-y-auto">
                {activeTab === "schedule" && <GamesTab />}
                {activeTab === "roster" && <RosterTab />}
              </div>
            </div>
          </div>
        </div>
      </PageContainer>
    );
  }
}
