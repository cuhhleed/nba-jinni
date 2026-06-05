import type { PlayoffMetadata } from "../../types/games";

type Props = {
  playoff_metadata: PlayoffMetadata | null;
};

/**
 * Renders two text lines for a playoff game:
 *   1. Round + game number label  (e.g. "Western Conference Finals · Game 7")
 *   2. Series record              (e.g. "Series tied 3-3") — hidden when null/empty
 *
 * Returns null when playoff_metadata is absent.
 * Placement within the layout is controlled by the parent.
 */
export default function PlayoffSeriesBanner({ playoff_metadata }: Props) {
  if (!playoff_metadata) return null;

  const round = playoff_metadata.round_label?.trim() || "Playoffs";
  const gameLabel = `${round} · Game ${playoff_metadata.series_game_number}`;

  return (
    <>
      <p className="text-[10px] sm:text-xs uppercase tracking-widest text-amber-500">
        {gameLabel}
      </p>
      {playoff_metadata.series_record && (
        <p className="text-[10px] sm:text-xs text-gray-400">
          {playoff_metadata.series_record}
        </p>
      )}
    </>
  );
}
