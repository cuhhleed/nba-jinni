import StatBubble from "../ui/StatBubble";

export default function PlayerStatRankingsWidget() {
  return (
    <div className="p-2 sm:p-3 lg:p-4 rounded-lg grid grid-cols-3 group">
      <h3 className="col-span-3 text-center font-brand text-sky-600">
        Stat Rankings (Coming Soon){" "}
      </h3>
      <StatBubble size="lg" bubble={false} value="—" label="PTS" />
      <StatBubble size="lg" bubble={false} value="—" label="REB" />
      <StatBubble size="lg" bubble={false} value="—" label="AST" />
      <StatBubble size="lg" bubble={false} value="—" label="STL" />
      <StatBubble size="lg" bubble={false} value="—" label="BLK" />
    </div>
  );
}
