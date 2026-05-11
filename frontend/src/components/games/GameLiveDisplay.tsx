import PlayerHeadshot from "../players/PlayerHeadshot";
import TeamLogo from "../teams/TeamLogo";
import FreshnessBadge from "../ui/FreshnessBadge";
import type { GameLive, PlayerLiveStat } from "../../types/games";

type Props = {
  game: GameLive;
};

/**
 * Strips the ISO 8601 duration wrapper from a minutes string returned by the
 * live endpoint (e.g. "PT12M34.00S" → "12:34"). Falls back to the raw value
 * if the string does not match the expected pattern.
 */
function formatMinutes(raw: string): string {
  const match = raw.match(/^PT(\d+)M([\d.]+)S$/);
  if (!match) return raw;
  const mins = match[1];
  const secs = Math.floor(Number(match[2])).toString().padStart(2, "0");
  return `${mins}:${secs}`;
}

type PlayerStatRowProps = {
  stat: PlayerLiveStat;
};

function PlayerStatRow({ stat }: PlayerStatRowProps) {
  return (
    <tr className="border-b border-gray-800 hover:bg-gray-800/40 transition-colors">
      <td className="py-2 px-2 flex items-center gap-2 min-w-[140px]">
        <PlayerHeadshot playerId={stat.player_id} size="sm" />
        <span className="text-xs sm:text-sm text-gray-200 whitespace-nowrap">
          {stat.first_name[0]}. {stat.last_name}
        </span>
      </td>
      <td className="py-2 px-2 text-center text-xs text-gray-400">
        {formatMinutes(stat.minutes)}
      </td>
      <td className="py-2 px-2 text-center text-xs text-gray-100 font-semibold">
        {stat.points}
      </td>
      <td className="py-2 px-2 text-center text-xs text-gray-300">{stat.rebounds}</td>
      <td className="py-2 px-2 text-center text-xs text-gray-300">{stat.assists}</td>
      <td className="py-2 px-2 text-center text-xs text-gray-300">
        {stat.fg_made}/{stat.fg_attempted}
      </td>
      <td className="py-2 px-2 text-center text-xs text-gray-300">
        {stat.three_made}/{stat.three_attempted}
      </td>
      <td className="py-2 px-2 text-center text-xs text-gray-300">
        {stat.ft_made}/{stat.ft_attempted}
      </td>
      <td className="py-2 px-2 text-center text-xs text-gray-300">{stat.steals}</td>
      <td className="py-2 px-2 text-center text-xs text-gray-300">{stat.blocks}</td>
      <td className="py-2 px-2 text-center text-xs text-gray-300">{stat.turnovers}</td>
    </tr>
  );
}

type PlayerStatTableProps = {
  stats: PlayerLiveStat[];
  teamName: string;
};

function PlayerStatTable({ stats, teamName }: PlayerStatTableProps) {
  return (
    <div className="overflow-x-auto mt-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-1 px-2">
        {teamName}
      </p>
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="border-b border-gray-700">
            <th className="py-1 px-2 text-xs text-gray-500 font-medium min-w-[140px]">
              Player
            </th>
            <th className="py-1 px-2 text-xs text-gray-500 font-medium text-center">MIN</th>
            <th className="py-1 px-2 text-xs text-gray-500 font-medium text-center">PTS</th>
            <th className="py-1 px-2 text-xs text-gray-500 font-medium text-center">REB</th>
            <th className="py-1 px-2 text-xs text-gray-500 font-medium text-center">AST</th>
            <th className="py-1 px-2 text-xs text-gray-500 font-medium text-center">FG</th>
            <th className="py-1 px-2 text-xs text-gray-500 font-medium text-center">3P</th>
            <th className="py-1 px-2 text-xs text-gray-500 font-medium text-center">FT</th>
            <th className="py-1 px-2 text-xs text-gray-500 font-medium text-center">STL</th>
            <th className="py-1 px-2 text-xs text-gray-500 font-medium text-center">BLK</th>
            <th className="py-1 px-2 text-xs text-gray-500 font-medium text-center">TO</th>
          </tr>
        </thead>
        <tbody>
          {stats.map((stat) => (
            <PlayerStatRow key={stat.player_id} stat={stat} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function GameLiveDisplay({ game }: Props) {
  const homeScore = game.home_score;
  const awayScore = game.away_score;

  let homeScoreColor = "text-sky-500";
  let awayScoreColor = "text-sky-500";
  if (homeScore > awayScore) {
    homeScoreColor = "text-green-400";
    awayScoreColor = "text-red-400";
  } else if (awayScore > homeScore) {
    homeScoreColor = "text-red-400";
    awayScoreColor = "text-green-400";
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Score header — mirrors GameBanner + GameCenterDisplay visual hierarchy */}
      <div className="flex items-center justify-center gap-4 sm:gap-8 py-4">
        {/* Home team */}
        <div className="flex flex-col items-center gap-1">
          <TeamLogo teamId={game.home_team.id} size="md" />
          <span className="text-xs sm:text-sm text-gray-400 font-medium">
            {game.home_team.code}
          </span>
        </div>

        {/* Scores + game status */}
        <div className="flex flex-col items-center gap-1">
          <div className="flex items-center gap-2 sm:gap-3">
            <span className={`font-brand text-3xl sm:text-4xl lg:text-5xl ${homeScoreColor}`}>
              {homeScore}
            </span>
            <span className="font-brand text-base sm:text-lg text-gray-500">–</span>
            <span className={`font-brand text-3xl sm:text-4xl lg:text-5xl ${awayScoreColor}`}>
              {awayScore}
            </span>
          </div>
          <span className="text-xs sm:text-sm text-amber-400 font-semibold uppercase tracking-wide">
            {game.game_status_text}
          </span>
          {game.game_clock && (
            <span className="text-[10px] sm:text-xs text-gray-500">
              {game.game_clock}
            </span>
          )}
        </div>

        {/* Away team */}
        <div className="flex flex-col items-center gap-1">
          <TeamLogo teamId={game.away_team.id} size="md" />
          <span className="text-xs sm:text-sm text-gray-400 font-medium">
            {game.away_team.code}
          </span>
        </div>
      </div>

      {/* Freshness badge — only visible when cache is stale */}
      <div className="flex justify-center">
        <FreshnessBadge
          isStale={game.is_stale}
          lastUpdatedAt={game.last_updated_at}
          size="sm"
        />
      </div>

      {/* Player stat tables */}
      <div className="flex flex-col gap-8">
        <PlayerStatTable
          stats={game.home_player_stats}
          teamName={game.home_team.name}
        />
        <PlayerStatTable
          stats={game.away_player_stats}
          teamName={game.away_team.name}
        />
      </div>
    </div>
  );
}
