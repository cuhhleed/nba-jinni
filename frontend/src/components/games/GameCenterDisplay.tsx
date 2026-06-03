import type { GameLive, GamePreview, GameResult } from "../../types/games";

type Props = {
  game: GamePreview | GameResult | GameLive;
};

function scoreColors(homePoints: number, awayPoints: number) {
  if (homePoints > awayPoints) return ["text-green-500", "text-red-600"] as const;
  if (awayPoints > homePoints) return ["text-red-600", "text-green-500"] as const;
  return ["text-sky-600", "text-sky-600"] as const;
}

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

  if (game.kind === "live") {
    const [homeColor, awayColor] = scoreColors(game.home_score, game.away_score);
    return (
      <div className="flex flex-col items-center justify-center gap-1">
        <div className="flex items-center gap-1 sm:gap-2">
          <span className={`font-brand text-xl sm:text-2xl lg:text-4xl ${homeColor}`}>
            {game.home_score}
          </span>
          <span className="font-brand text-xs sm:text-sm lg:text-base text-gray-900">
            –
          </span>
          <span className={`font-brand text-xl sm:text-2xl lg:text-4xl ${awayColor}`}>
            {game.away_score}
          </span>
        </div>
        {game.is_final ? (
          <>
            <span className="text-[10px] sm:text-xs font-semibold uppercase tracking-wide text-sky-600">
              FINAL
            </span>
            <span className="text-[9px] sm:text-[10px] italic text-gray-700">
              Official box score syncing…
            </span>
          </>
        ) : (
          <>
            <span className="text-[10px] sm:text-xs font-semibold uppercase tracking-wide text-amber-600">
              {game.game_status_text}
            </span>
          </>
        )}
      </div>
    );
  }

  const [homeColor, awayColor] = scoreColors(
    game.home_team_stat.points,
    game.away_team_stat.points
  );

  return (
    <div className="flex flex-col items-center justify-center gap-1">
      <div className="flex items-center gap-1 sm:gap-2">
        <span className={`font-brand text-xl sm:text-2xl lg:text-4xl ${homeColor}`}>
          {game.home_team_stat.points}
        </span>
        <span className="font-brand text-xs sm:text-sm lg:text-base text-gray-900">
          –
        </span>
        <span className={`font-brand text-xl sm:text-2xl lg:text-4xl ${awayColor}`}>
          {game.away_team_stat.points}
        </span>
      </div>
      <span className="text-[10px] sm:text-xs text-sky-600">FINAL</span>
    </div>
  );
}
