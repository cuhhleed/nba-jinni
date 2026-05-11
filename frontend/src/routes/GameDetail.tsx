import { useState } from "react";
import { useParams } from "react-router";
import GameBanner from "../components/games/GameBanner";
import GameComparisonStats from "../components/games/GameComparisonStats";
import BoxScoreTab from "../components/games/tabs/BoxScoreTab";
import H2HTab from "../components/games/tabs/H2HTab";
import PreviewLast5Tab from "../components/games/tabs/PreviewLast5Tab";
import PageContainer from "../components/layout/PageContainer";
import EmptyState from "../components/ui/EmptyState";
import ErrorPage from "../components/ui/ErrorPage";
import LoadingPage from "../components/ui/LoadingPage";
import PillTabs from "../components/ui/PillTabs";
import GameLiveDisplay from "../components/games/GameLiveDisplay";
import { useGameDetail } from "../hooks/useGameDetail";
import type { GamePreview, GameResult } from "../types/games";

const PREVIEW_TABS = [
  { id: "h2h", label: "H2H" },
  { id: "last5", label: "Last 5 Games" },
] as const;

const RESULT_TABS = [
  { id: "box", label: "Box Score" },
  { id: "h2h", label: "H2H" },
] as const;

type PreviewTabId = (typeof PREVIEW_TABS)[number]["id"];
type ResultTabId = (typeof RESULT_TABS)[number]["id"];

function PreviewTabContent({
  game,
  activeTab,
}: {
  game: GamePreview;
  activeTab: PreviewTabId;
}) {
  switch (activeTab) {
    case "h2h":
      return (
        <H2HTab
          homeTeamId={game.home_team_id}
          awayTeamId={game.away_team_id}
        />
      );
    case "last5":
      return <PreviewLast5Tab game={game} />;
  }
}

function ResultTabContent({
  game,
  activeTab,
}: {
  game: GameResult;
  activeTab: ResultTabId;
}) {
  switch (activeTab) {
    case "box":
      return <BoxScoreTab game={game} />;
    case "h2h":
      return (
        <H2HTab
          homeTeamId={game.home_team_id}
          awayTeamId={game.away_team_id}
        />
      );
  }
}

export default function GameDetail() {
  const { id } = useParams();
  const gameId = id ?? "";

  const [previewTab, setPreviewTab] = useState<PreviewTabId>("h2h");
  const [resultTab, setResultTab] = useState<ResultTabId>("box");

  const { data: game, isLoading, error } = useGameDetail(gameId);

  if (isLoading) return <LoadingPage />;
  if (error) return <ErrorPage />;
  if (!game) return <EmptyState />;

  if (game.kind === "live") {
    return (
      <PageContainer>
        <GameLiveDisplay game={game} />
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <GameBanner game={game} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mt-4">
        <GameComparisonStats game={game} />

        <div className="col-span-2 flex flex-col mt-8">
          <div className="flex justify-center">
            {game.kind === "preview" ? (
              <PillTabs
                className="bg-gray-900"
                tabs={PREVIEW_TABS}
                activeTab={previewTab}
                onChange={setPreviewTab}
              />
            ) : (
              <PillTabs
                className="bg-gray-900"
                tabs={RESULT_TABS}
                activeTab={resultTab}
                onChange={setResultTab}
              />
            )}
          </div>
          <div className="mt-4">
            {game.kind === "preview" ? (
              <PreviewTabContent game={game} activeTab={previewTab} />
            ) : (
              <ResultTabContent game={game} activeTab={resultTab} />
            )}
          </div>
        </div>
      </div>
    </PageContainer>
  );
}
