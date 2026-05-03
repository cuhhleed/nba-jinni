import { Bars3Icon, XMarkIcon } from "@heroicons/react/24/outline";
import { useEffect, useState } from "react";
import { Link } from "react-router";
import SearchBar from "../ui/SearchBar";

const navLinks = (
  <ul className="flex flex-col gap-2 lg:flex-row lg:items-center lg:gap-6">
    <li>
      <Link
        to="/teams"
        className="text-sm font-medium font-brand text-sky-600 hover:text-amber-500"
      >
        Teams
      </Link>
    </li>
    <li>
      <Link
        to="/standings"
        className="text-sm font-medium font-brand text-sky-600 hover:text-amber-500"
      >
        Standings
      </Link>
    </li>
  </ul>
);

export default function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 1024) setMobileOpen(false);
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return (
    <>
      <nav className="sticky top-0 z-10 w-full bg-gray-900 border-b border-gray-700 px-4 py-3 lg:px-8">
        <div className="flex items-center justify-between">
          <Link
            to="/"
            className="font-semibold font-brand text-lg text-sky-600 hover:text-amber-500"
          >
            NBA Jinni
          </Link>

          <div className="hidden lg:flex flex-1 items-center gap-8 ml-8">
            {navLinks}
            <SearchBar />
          </div>

          <button
            className="lg:hidden"
            onClick={() => setMobileOpen(true)}
            aria-label="Open navigation"
          >
            <Bars3Icon className="h-6 w-6 text-sky-600 hover:text-amber-400" />
          </button>
        </div>
      </nav>

      {mobileOpen && (
        <div className="lg:hidden fixed inset-0 z-40">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setMobileOpen(false)}
          />
          <div className="absolute right-0 top-0 h-full w-72 bg-gray-900 flex flex-col p-6 gap-6">
            <button
              className="self-end"
              onClick={() => setMobileOpen(false)}
              aria-label="Close navigation"
            >
              <XMarkIcon className="h-6 w-6 text-sky-600 hover:text-amber-400" />
            </button>
            {navLinks}
            <div className="w-full">
              <SearchBar dark />
            </div>
          </div>
        </div>
      )}
    </>
  );
}
