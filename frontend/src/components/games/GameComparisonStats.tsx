import type { GameDetailResponse } from "../../types/games";
import EmptyState from "../ui/EmptyState";
import PairedStatBubble from "./PairedStatBubble";

type Props = {
  game: GameDetailResponse;
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

export default function GameComparisonStats({ game }: Props) {
  if (game.kind === "preview") {
    const homeAvg = game.home_team.season_averages[0];
    const awayAvg = game.away_team.season_averages[0];

    if (!homeAvg || !awayAvg) {
      return <EmptyState />;
    }

    return (
      <div className="flex flex-col my-4 sm:my-6 lg:my-8">
        <h2 className="text-center text-[10px] sm:text-xs lg:text-sm text-gray-900 font-medium mb-2">
          Season Averages
        </h2>
        {STAT_DEFS.map(({ label, key, lowerIsBetter, pct }) => {
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
        })}
      </div>
    );
  }

  // result mode — use per-game team stats
  const homeStat = game.home_team_stat;
  const awayStat = game.away_team_stat;

  return (
    <div className="flex flex-col my-4 sm:my-6 lg:my-8">
      <h2 className="text-center text-[10px] sm:text-xs lg:text-sm text-gray-900 font-medium mb-2">
        Game Stats
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
