import type { Standing } from "../../types/teams";
import StatBubble from "../ui/StatBubble";

type Props = {
  standing: Standing | null;
};

export default function TeamStandingWidget({ standing }: Props) {
  return (
    <div className="team-standing-container p-2 sm:p-3 lg:p-4 rounded-lg grid grid-cols-2 group">
      <h3 className="text-center text-[10px] sm:text-xl lg:text-2xl font-brand text-sky-600 col-span-2">
        {standing?.season} Standing
      </h3>
      <StatBubble
        size="lg"
        bubble={false}
        labelColor="text-sky-600 group-hover:text-amber-500"
        value={standing?.wins + "-" + standing?.losses}
        label="Record"
      />
      <StatBubble
        size="lg"
        bubble={false}
        labelColor="text-sky-600 group-hover:text-amber-500"
        value={standing?.conference_rank}
        label="Rank"
        sublabel={standing?.conference}
      />
      <StatBubble
        size="lg"
        bubble={false}
        labelColor="text-sky-600 group-hover:text-amber-500"
        value={standing?.win_L10 + "-" + standing?.loss_L10}
        label="L10"
      />
      <StatBubble
        size="lg"
        bubble={false}
        labelColor="text-sky-600 group-hover:text-amber-500"
        value={standing?.games_behind}
        label="GB"
      />
    </div>
  );
}
