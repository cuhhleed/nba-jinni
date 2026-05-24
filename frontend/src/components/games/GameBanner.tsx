import type { GamePreview, GameResult } from "../../types/games";
import CarpetBadge from "../ui/CarpetBadge";
import GameCenterDisplay from "./GameCenterDisplay";
import TeamGameBadge from "./TeamGameBadge";

type Props = {
  game: GamePreview | GameResult;
};

export default function GameBanner({ game }: Props) {
  return (
    <CarpetBadge size="lg" className="p-2 sm:p-3 lg:p-4 mx-2 lg:my-2">
      <div className="grid grid-cols-3 items-center">
        <TeamGameBadge team={game.home_team} />
        <GameCenterDisplay game={game} />
        <TeamGameBadge team={game.away_team} />
      </div>
      <div className="mt-2 text-center text-[10px] sm:text-xs lg:text-sm text-sky-600">
        @{game.home_team.code}
      </div>
    </CarpetBadge>
  );
}
