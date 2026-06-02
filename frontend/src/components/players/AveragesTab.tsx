import { useState } from "react";
import PillTabs from "../ui/PillTabs";
import PlayerPlayoffStatsTab from "./PlayerPlayoffStatsTab";
import PlayerStatsTab from "./PlayerStatsTab";

type AveragesTabId = "regular" | "playoff";

const TABS: { id: AveragesTabId; label: string }[] = [
  { id: "regular", label: "Regular Season" },
  { id: "playoff", label: "Playoffs" },
];

export default function AveragesTab() {
  const [activeTab, setActiveTab] = useState("regular");

  return (
    <div className="mt-8 flex flex-col justify-center">
      <div className="flex justify-center">
        <PillTabs
          className="bg-gray-900"
          tabs={TABS}
          activeTab={activeTab}
          onChange={setActiveTab}
        />
      </div>
      <div className="grid grid-cols-1 justify-center h-full w-full">
        <div className="mt-6 flex-1 min-h-0 overflow-y-auto">
          {activeTab === "regular" && <PlayerStatsTab />}
          {activeTab === "playoff" && <PlayerPlayoffStatsTab />}
        </div>
      </div>
    </div>
  );
}
