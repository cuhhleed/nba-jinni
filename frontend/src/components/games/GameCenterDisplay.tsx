import type { GamePreview, GameResult } from "../../types/games";

type Props = {
  game: GamePreview | GameResult;
};

export default function GameCenterDisplay({ game }: Props) {
  if (game.kind === "preview") {
    return (
      <div className="flex items-center justify-center">
        <span className="font-brand text-2xl sm:text-3xl lg:text-5xl text-sky-600">
          VS
        </span>
      </div>
    );
  }

  const homePoints = game.home_team_stat.points;
  const awayPoints = game.away_team_stat.points;

  let homeColor = "text-sky-600";
  let awayColor = "text-sky-600";

  if (homePoints > awayPoints) {
    homeColor = "text-green-500";
    awayColor = "text-red-600";
  } else if (awayPoints > homePoints) {
    homeColor = "text-red-600";
    awayColor = "text-green-500";
  }

  return (
    <div className="flex flex-col items-center justify-center gap-1">
      <div className="flex items-center gap-1 sm:gap-2">
        <span className={`font-brand text-xl sm:text-2xl lg:text-4xl ${homeColor}`}>
          {homePoints}
        </span>
        <span className="font-brand text-xs sm:text-sm lg:text-base text-gray-900">
          –
        </span>
        <span className={`font-brand text-xl sm:text-2xl lg:text-4xl ${awayColor}`}>
          {awayPoints}
        </span>
      </div>
      <span className="text-[10px] sm:text-xs text-sky-600">FINAL</span>
    </div>
  );
}
