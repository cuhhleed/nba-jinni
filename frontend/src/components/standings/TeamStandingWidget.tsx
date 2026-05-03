import type { Standing } from "../../types/teams";
import StatBubble from "../ui/StatBubble";

type Props = {
  standing: Standing | null;
};

export default function TeamStandingWidget({ standing }: Props) {
  let recordValueColor = "text-sky-600 group-hover:text-amber-500";
  let lastTenValueColor = "text-sky-600 group-hover:text-amber-500";
  let rankValueColor = "text-sky-600 group-hover:text-amber-500";
  let gamesBehindValueColor = "text-green-500 group-hover:text-amber-500";

  if (standing?.wins != null && standing.losses != null) {
    if (standing.wins > standing.losses) {
      recordValueColor = "text-green-500 group-hover:text-amber-500";
    } else if (standing.wins < standing.losses) {
      recordValueColor = "text-red-500 group-hover:text-amber-500";
    }
  }

  if (standing?.win_L10 != null && standing.loss_L10 != null) {
    if (standing?.win_L10 > standing?.loss_L10) {
      lastTenValueColor = "text-green-500 group-hover:text-amber-500";
    } else if (standing.win_L10 < standing.loss_L10) {
      lastTenValueColor = "text-red-500 group-hover:text-amber-500";
    }
  }

  if (standing?.conference_rank) {
    if (standing?.conference_rank <= 6) {
      rankValueColor = "text-green-500 group-hover:text-amber-500";
    } else if (standing.conference_rank >= 11) {
      rankValueColor = "text-red-500 group-hover:text-amber-500";
    }
  }

  if (standing?.games_behind != null) {
    if (standing?.games_behind > 0) {
      gamesBehindValueColor = "text-red-500 group-hover:text-amber-500";
    }
  }

  return (
    <div className="team-standing-container p-2 sm:p-3 lg:p-4 rounded-lg grid grid-cols-2 group">
      <h3 className="text-center text-[10px] sm:text-xl lg:text-2xl font-brand text-sky-600 col-span-2">
        {standing?.season} Standing
      </h3>
      <StatBubble
        size="lg"
        bubble={false}
        labelColor="text-sky-600 group-hover:text-amber-500"
        valueColor={recordValueColor}
        value={standing?.wins + "-" + standing?.losses}
        label="Record"
      />
      <StatBubble
        size="lg"
        bubble={false}
        labelColor="text-sky-600 group-hover:text-amber-500"
        valueColor={rankValueColor}
        value={standing?.conference_rank}
        label="Rank"
        sublabel={standing?.conference}
      />
      <StatBubble
        size="lg"
        bubble={false}
        labelColor="text-sky-600 group-hover:text-amber-500"
        valueColor={lastTenValueColor}
        value={standing?.win_L10 + "-" + standing?.loss_L10}
        label="L10"
      />
      <StatBubble
        size="lg"
        bubble={false}
        labelColor="text-sky-600 group-hover:text-amber-500"
        valueColor={gamesBehindValueColor}
        value={standing?.games_behind}
        label="GB"
      />
    </div>
  );
}
