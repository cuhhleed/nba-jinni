import { useState } from "react";
import { useParams } from "react-router";
import PageContainer from "../components/layout/PageContainer";
import Last5GamesTab from "../components/players/Last5GamesTab";
import PlayerBannerInfo from "../components/players/PlayerBannerInfo";
import PlayerStatRankingsWidget from "../components/players/PlayerStatRankingsWidget";
import PlayerStatsTab from "../components/players/PlayerStatsTab";
import VsTeamTab from "../components/players/VsTeamTab";
import CarpetBadge from "../components/ui/CarpetBadge";
import EmptyState from "../components/ui/EmptyState";
import ErrorPage from "../components/ui/ErrorPage";
import LoadingPage from "../components/ui/LoadingPage";
import PillTabs from "../components/ui/PillTabs";
import { usePlayerInfo } from "../hooks/usePlayerInfo";

type PlayerTabId = "last5" | "vs";

const TABS: { id: PlayerTabId; label: string }[] = [
  { id: "last5", label: "Last 5 Games" },
  { id: "vs", label: "VS" },
];

export default function PlayerDetail() {
  const { id } = useParams();
  const playerId = Number(id);
  const [activeTab, setActiveTab] = useState<PlayerTabId>("last5");

  const { data: player, isLoading, error } = usePlayerInfo(playerId);

  if (isLoading) return <LoadingPage />;
  if (error) return <ErrorPage />;
  if (!player) return <EmptyState />;

  return (
    <PageContainer>
      <CarpetBadge
        size="lg"
        className="p-2 sm:p-3 lg:p-4 grid grid-cols-2 mx-2 lg:my-2"
      >
        <PlayerBannerInfo />
        <PlayerStatRankingsWidget />
      </CarpetBadge>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mt-4">
        <PlayerStatsTab />
        <div className="col-span-2 flex flex-col mt-8">
          <div className="flex justify-center">
            <PillTabs
              className="bg-gray-900"
              tabs={TABS}
              activeTab={activeTab}
              onChange={setActiveTab}
            />
          </div>
          <div className="mt-4">
            {activeTab === "last5" && <Last5GamesTab playerId={playerId} />}
            {activeTab === "vs" && <VsTeamTab player={player} />}
          </div>
        </div>
      </div>
    </PageContainer>
  );
}
