import { useState } from "react";
import { Link } from "react-router";
import PageContainer from "../components/layout/PageContainer";
import TeamLogo from "../components/teams/TeamLogo";
import CarpetBadge from "../components/ui/CarpetBadge";
import EmptyState from "../components/ui/EmptyState";
import ErrorPage from "../components/ui/ErrorPage";
import LoadingPage from "../components/ui/LoadingPage";
import PillTabs from "../components/ui/PillTabs";
import { useStandings } from "../hooks/useStandings";
import { useTeams } from "../hooks/useTeams";
import type { Standing } from "../types/teams";

type TabId = "east" | "west" | "all";

const TABS: { id: TabId; label: string }[] = [
  { id: "east", label: "East" },
  { id: "west", label: "West" },
  { id: "all", label: "All" },
];

const COL_GRID =
  "grid w-max sm:w-full lg:w-full grid-cols-[2rem_1fr_4.5rem_3.5rem_4.5rem_4.5rem_4.5rem_4rem_4rem_3rem] lg:grid-cols-[3rem_1fr_6rem_5rem_6rem_6rem_6rem_5.5rem_5.5rem_4.5rem]";

const HEADERS = ["RNK", "TEAM", "W/L", "W%", "HM", "AW", "L10", "PPG", "OPPG", "STRK"];

const CELL = "text-xs lg:text-sm text-gray-900 text-center self-center";

// NBA playoff structure: top 6 advance directly, 7–10 enter play-in
const PLAYOFF_CUTOFF = 6;
const PLAY_IN_CUTOFF = 10;

function rankColor(rank: number) {
  if (rank <= PLAYOFF_CUTOFF) return "text-green-500";
  if (rank <= PLAY_IN_CUTOFF) return "text-gray-900";
  return "text-red-600";
}

function formatWinPct(pct: number) {
  return pct.toFixed(3).replace(/^0/, "");
}

function StandingRow({
  standing,
  teamCode,
  rank,
  rankClassName,
}: {
  standing: Standing;
  teamCode: string | undefined;
  rank: number;
  rankClassName: string;
}) {
  return (
    <div
      className={`${COL_GRID} bg-white border-b border-b-amber-500/20 px-2 py-1.5 lg:py-2.5 divide-x divide-amber-500/20`}
    >
      <span
        className={`text-xs lg:text-sm font-semibold text-center self-center ${rankClassName}`}
      >
        {rank}
      </span>
      <Link
        to={`/teams/${standing.team_id}`}
        className="flex items-center gap-1.5 px-1 text-gray-900 hover:text-amber-500 transition-colors text-xs lg:text-sm"
      >
        <TeamLogo
          size="sm"
          teamId={standing.team_id}
          alt={teamCode}
          className="shrink-0"
        />
        <span className="text-xs font-brand">{teamCode ?? "—"}</span>
      </Link>
      <span className={CELL}>
        {standing.wins}-{standing.losses}
      </span>
      <span className={CELL}>{formatWinPct(standing.win_pct)}</span>
      <span className={CELL}>
        {standing.wins_home}-{standing.losses_home}
      </span>
      <span className={CELL}>
        {standing.wins_away}-{standing.losses_away}
      </span>
      <span className={CELL}>
        {standing.win_L10}-{standing.loss_L10}
      </span>
      <span className={CELL}>{standing.points_pg.toFixed(1)}</span>
      <span className={CELL}>{standing.opp_points_pg.toFixed(1)}</span>
      <span
        className={`text-xs lg:text-sm text-center self-center ${standing.streak > 0 ? "text-green-500" : standing.streak < 0 ? "text-red-600" : "text-gray-400"}`}
      >
        {standing.streak}
      </span>
    </div>
  );
}

export default function Standings() {
  const [activeTab, setActiveTab] = useState<TabId>("east");
  const {
    data: standings,
    isLoading: standingsLoading,
    error: standingsError,
  } = useStandings();
  const { data: teams, isLoading: teamsLoading, error: teamsError } = useTeams();

  if (standingsLoading || teamsLoading) return <LoadingPage />;
  if (standingsError || teamsError) return <ErrorPage />;
  if (!standings || !teams) return null;
  if (standings.length === 0) return <EmptyState />;

  const teamMap = new Map(teams.map((t) => [t.id, t.code]));
  const season = standings[0].season;
  const isAll = activeTab === "all";
  const filtered = isAll
    ? [...standings].sort(
        (a, b) => b.win_pct - a.win_pct || b.wins - a.wins || a.team_id - b.team_id
      )
    : standings.filter((s) => s.conference.toLowerCase() === activeTab);

  return (
    <PageContainer>
      <CarpetBadge className="p-4 flex flex-col items-center gap-3">
        <div className="text-center">
          <h1 className="text-2xl font-brand text-sky-600">NBA Standings</h1>
          {season && <p className="text-xs text-amber-500 mt-0.5">{season}</p>}
        </div>
        <PillTabs
          tabs={TABS}
          activeTab={activeTab}
          onChange={setActiveTab}
          className="bg-sky-600"
          activeClassName="bg-amber-500 text-gray-900 font-brand"
          inactiveClassName="text-gray-900 bg-sky-600 hover:text-amber-500"
        />
      </CarpetBadge>

      <div className="mt-8 overflow-x-auto bg-white">
        <div className="overflow-y-auto max-h-[70vh]">
          <div
            className={`${COL_GRID} sticky top-0 z-10 bg-gray-900 border border-amber-500 px-2 py-1.5 divide-x divide-amber-500`}
          >
            {HEADERS.map((label) => (
              <span
                key={label}
                className="text-[10px] lg:text-xs font-brand text-sky-600 uppercase tracking-wide text-center px-1"
              >
                {label}
              </span>
            ))}
          </div>

          {filtered.map((s, i) => (
            <StandingRow
              key={s.team_id}
              standing={s}
              teamCode={teamMap.get(s.team_id)}
              rank={isAll ? i + 1 : s.conference_rank}
              rankClassName={isAll ? "text-gray-900" : rankColor(s.conference_rank)}
            />
          ))}
        </div>
      </div>
    </PageContainer>
  );
}
