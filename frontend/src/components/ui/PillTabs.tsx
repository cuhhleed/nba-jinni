type Tab<Id extends string> = {
  id: Id;
  label: string;
};

type Props<Id extends string> = {
  tabs: readonly Tab<Id>[];
  activeTab: Id;
  onChange: (id: Id) => void;
  className?: string;
  activeClassName?: string;
  inactiveClassName?: string;
};

export default function PillTabs<Id extends string>({
  tabs,
  activeTab,
  onChange,
  className = "",
  activeClassName = "bg-amber-500 text-gray-900 font-brand",
  inactiveClassName = "text-sky-600 hover:text-amber-500",
}: Props<Id>) {
  return (
    <div className={`inline-flex rounded-full ${className}`}>
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          onClick={() => onChange(tab.id)}
          className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors duration-200 ${
            tab.id === activeTab ? activeClassName : inactiveClassName
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
