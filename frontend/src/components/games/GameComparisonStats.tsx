import { useState } from "react";
import type { GameLive, GamePreview, GameResult } from "../../types/games";
import { useTeamSeasonPlayoffAverage } from "../../hooks/useTeamSeasonPlayoffAverage";
import EmptyState from "../ui/EmptyState";
import PillTabs from "../ui/PillTabs";
import PairedStatBubble from "./PairedStatBubble";

type Props = {
  game: GamePreview | GameResult | GameLive;
};

type StatDef = {
  label: string;
  key: "points" | "rebounds" | "assists" | "steals" | "blocks" | "turnovers" | "fg_pct" | "three_pct" | "ft_pct";
  lowerIsBetter?: boolean;
  pct?: boolean; // multiply × 100 before display
};

const STAT_DEFS: StatDef[] = [
  { label: "PTS", key: "points" },
  { label: "REB", key: "rebounds" },
  { label: "AST", key: "assists" },
  { label: "STL", key: "steals" },
  { label: "BLK", key: "blocks" },
  { label: "TO",  key: "turnovers", lowerIsBetter: true },
  { label: "FG%", key: "fg_pct", pct: true },
  { label: "3P%", key: "three_pct", pct: true },
  { label: "FT%", key: "ft_pct", pct: true },
];

const AVERAGE_TABS = [
  { id: "playoffs" as const, label: "Playoffs" },
  { id: "regular" as const, label: "Regular" },
] as const;

type AverageTab = "playoffs" | "regular";

export default function GameComparisonStats({ game }: Props) {
  // Default to "playoffs" tab when the game is a playoff game. For regular games,
  // this state is unused since the toggle is not rendered.
  const [activeTab, setActiveTab] = useState<AverageTab>("playoffs");

  const isPlayoffPreview = game.kind === "preview" && game.game_type === "playoff";

  // Playoff averages are only fetched when the game is a playoff preview.
  const homePlayoffAvg = useTeamSeasonPlayoffAverage(
    isPlayoffPreview ? game.home_team_id : 0
  );
  const awayPlayoffAvg = useTeamSeasonPlayoffAverage(
    isPlayoffPreview ? game.away_team_id : 0
  );

  if (game.kind === "preview") {
    const homeRegularAvg = game.home_team.season_averages[0];
    const awayRegularAvg = game.away_team.season_averages[0];

    // For playoff preview games: show the Regular/Playoffs toggle.
    if (isPlayoffPreview) {
      const showPlayoffs = activeTab === "playoffs";
      const homeAvg = showPlayoffs ? homePlayoffAvg.data : homeRegularAvg;
      const awayAvg = showPlayoffs ? awayPlayoffAvg.data : awayRegularAvg;
      const isLoading = showPlayoffs && (homePlayoffAvg.isLoading || awayPlayoffAvg.isLoading);

      return (
        <div className="flex flex-col my-4 sm:my-6 lg:my-8">
          <div className="flex flex-col items-center mb-3 gap-2">
            <h2 className="text-center text-[10px] sm:text-xs lg:text-sm text-gray-900 font-medium">
              Season Averages
            </h2>
            <PillTabs
              tabs={AVERAGE_TABS}
              activeTab={activeTab}
              onChange={setActiveTab}
            />
          </div>
          {isLoading ? (
            <div className="text-center text-xs text-gray-500 py-4">Loading…</div>
          ) : !homeAvg || !awayAvg ? (
            <EmptyState />
          ) : (
            STAT_DEFS.map(({ label, key, lowerIsBetter, pct }) => {
              const homeVal = pct ? homeAvg[key] * 100 : homeAvg[key];
              const awayVal = pct ? awayAvg[key] * 100 : awayAvg[key];
              return (
                <PairedStatBubble
                  key={label}
                  label={label}
                  homeValue={homeVal}
                  awayValue={awayVal}
                  lowerIsBetter={lowerIsBetter}
                />
              );
            })
          )}
        </div>
      );
    }

    // Regular game preview — no toggle, existing behaviour.
    if (!homeRegularAvg || !awayRegularAvg) {
      return <EmptyState />;
    }

    return (
      <div className="flex flex-col my-4 sm:my-6 lg:my-8">
        <h2 className="text-center text-[10px] sm:text-xs lg:text-sm text-gray-900 font-medium mb-2">
          Season Averages
        </h2>
        {STAT_DEFS.map(({ label, key, lowerIsBetter, pct }) => {
          const homeVal = pct ? homeRegularAvg[key] * 100 : homeRegularAvg[key];
          const awayVal = pct ? awayRegularAvg[key] * 100 : awayRegularAvg[key];
          return (
            <PairedStatBubble
              key={label}
              label={label}
              homeValue={homeVal}
              awayValue={awayVal}
              lowerIsBetter={lowerIsBetter}
            />
          );
        })}
      </div>
    );
  }

  // result / live mode — use per-game team stats
  const homeStat = game.home_team_stat;
  const awayStat = game.away_team_stat;
  const heading = game.kind === "live" ? "Live Game Stats" : "Game Stats";

  return (
    <div className="flex flex-col my-4 sm:my-6 lg:my-8">
      <h2 className="text-center text-[10px] sm:text-xs lg:text-sm text-gray-900 font-medium mb-2">
        {heading}
      </h2>
      {STAT_DEFS.map(({ label, key, lowerIsBetter, pct }) => {
        const homeVal = pct ? homeStat[key] * 100 : homeStat[key];
        const awayVal = pct ? awayStat[key] * 100 : awayStat[key];
        return (
          <PairedStatBubble
            key={label}
            label={label}
            homeValue={homeVal}
            awayValue={awayVal}
            lowerIsBetter={lowerIsBetter}
          />
        );
      })}
    </div>
  );
}
