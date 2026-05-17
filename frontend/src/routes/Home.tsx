import GamesWidget from "../components/home/GamesWidget";
import RecentMagic from "../components/home/RecentMagic";
import StatLeaders from "../components/home/StatLeaders";
import Top10Standings from "../components/home/Top10Standings";
import PageContainer from "../components/layout/PageContainer";

export default function Home() {
  return (
    <PageContainer>
      <GamesWidget />
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-10 mt-8">
        <div className="flex flex-col gap-10">
          <StatLeaders />
          <Top10Standings />
        </div>
        <RecentMagic />
      </div>
    </PageContainer>
  );
}
