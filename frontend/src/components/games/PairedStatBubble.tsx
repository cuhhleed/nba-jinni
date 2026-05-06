import StatBubble from "../ui/StatBubble";

type Props = {
  label: string;
  homeValue: number;
  awayValue: number;
  format?: (v: number) => string;
  lowerIsBetter?: boolean;
};

const DEFAULT_COLOR = "text-sky-600";
const WIN_COLOR = "text-green-500";
const LOSS_COLOR = "text-red-600";

export default function PairedStatBubble({
  label,
  homeValue,
  awayValue,
  format = (v) => v.toFixed(1),
  lowerIsBetter = false,
}: Props) {
  let homeColor = DEFAULT_COLOR;
  let awayColor = DEFAULT_COLOR;

  if (homeValue !== awayValue) {
    const homeWins = lowerIsBetter ? homeValue < awayValue : homeValue > awayValue;
    homeColor = homeWins ? WIN_COLOR : LOSS_COLOR;
    awayColor = homeWins ? LOSS_COLOR : WIN_COLOR;
  }

  return (
    <div className="grid grid-cols-3 items-center">
      <StatBubble
        bubble
        value={format(homeValue)}
        valueColor={homeColor}
        className="m-1"
      />
      <span className="text-center text-[10px] text-gray-900 font-medium">{label}</span>
      <StatBubble
        bubble
        value={format(awayValue)}
        valueColor={awayColor}
        className="m-1"
      />
    </div>
  );
}
