import {
  Combobox,
  ComboboxInput,
  ComboboxOption,
  ComboboxOptions,
} from "@headlessui/react";
import { MagnifyingGlassIcon } from "@heroicons/react/24/outline";
import { useState } from "react";
import { useNavigate } from "react-router";
import { usePlayers } from "../../hooks/usePlayers";
import type { Player } from "../../types/players";
import ErrorState from "./ErrorState";
import LoadingState from "./LoadingState";

const MAX_SUGGESTIONS = 8;

export default function SearchBar({ dark = false }: { dark?: boolean }) {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();
  const { data: allPlayers, isLoading, error } = usePlayers();

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState message="Could not load players." />;

  const suggestions =
    !allPlayers || query.trim().length === 0
      ? []
      : allPlayers
          .filter((p) =>
            `${p.first_name} ${p.last_name}`.toLowerCase().includes(query.toLowerCase())
          )
          .slice(0, MAX_SUGGESTIONS);

  function handleSelect(player: Player | null) {
    if (player) navigate(`/players/${player.id}`);
  }

  function handleSearch() {
    const q = query.trim();
    if (q.length < 2) return;
    navigate(`/search?q=${encodeURIComponent(q)}`);
  }

  const borderColor = dark ? "border-gray-600" : "border-gray-300";

  return (
    <div className="flex flex-1 items-stretch">
      <div className="flex-1">
        <Combobox onChange={handleSelect}>
          <ComboboxInput
            placeholder="Search players..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && suggestions.length === 0) handleSearch();
            }}
            className={[
              "w-full border rounded-l-md px-3 py-1.5 text-sm focus:outline-none focus:border-sky-600",
              borderColor,
              dark
                ? "bg-gray-800 text-gray-100 placeholder-gray-400"
                : "bg-white text-gray-900",
            ].join(" ")}
          />
          <ComboboxOptions
            anchor="bottom start"
            className="z-50 w-[var(--input-width)] max-h-60 overflow-auto rounded-md bg-white border border-gray-200 shadow-lg empty:hidden text-sm"
          >
            {suggestions.map((player) => (
              <ComboboxOption
                key={player.id}
                value={player}
                className="cursor-pointer px-4 py-2 text-gray-900 data-focus:bg-sky-50 data-focus:text-sky-700 hover:bg-amber-500"
              >
                {player.first_name} {player.last_name}
              </ComboboxOption>
            ))}
          </ComboboxOptions>
        </Combobox>
      </div>
      <button
        onClick={handleSearch}
        disabled={query.trim().length < 2}
        aria-label="Search"
        className={[
          "border border-l-0 rounded-r-md px-3 bg-sky-600",
          "hover:bg-amber-500",
          "disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-sky-600",
          borderColor,
        ].join(" ")}
      >
        <MagnifyingGlassIcon className="h-4 w-4 text-gray-900" />
      </button>
    </div>
  );
}
