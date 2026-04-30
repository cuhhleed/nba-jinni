type Tab = {
  id: string;
  label: string;
};

type Props = {
  tabs: Tab[];
  activeTab: string;
  onChange: (id: string) => void;
  className?: string;
};

export default function PillTabs({ tabs, activeTab, onChange, className = "" }: Props) {
  return (
    <div className={`inline-flex bg-gray-900 rounded-full p-1 ${className}`}>
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors duration-200 ${
            tab.id === activeTab
              ? "bg-amber-500 text-gray-900 font-brand"
              : "text-sky-500 hover:text-amber-500"
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
