import { Bars3Icon, MagnifyingGlassIcon, XMarkIcon } from "@heroicons/react/24/outline";
import { useEffect, useState } from "react";
import { Link } from "react-router";

const navLinks = (
  <ul className="flex flex-col gap-2 lg:flex-row lg:items-center lg:gap-6">
    <li>
      <Link
        to="/teams"
        className="text-sm font-medium font-brand text-sky-500 hover:text-amber-500"
      >
        Teams
      </Link>
    </li>
    <li>
      <Link
        to="/standings"
        className="text-sm font-medium font-brand text-sky-500 hover:text-amber-500"
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
            className="font-semibold font-brand text-lg text-sky-500 hover:text-amber-400"
          >
            NBA Jinni
          </Link>

          <div className="hidden lg:flex flex-1 items-center gap-8 ml-8">
            {navLinks}
            <div className="flex flex-1 items-stretch">
              <input
                type="search"
                placeholder="Search players..."
                className="flex-1 border border-gray-300 rounded-l-md px-3 py-1.5 text-sm focus:outline-none focus:border-blue-500"
              />
              <button className="border border-l-0 border-gray-300 rounded-r-md px-3 bg-sky-500 hover:bg-amber-500">
                <MagnifyingGlassIcon className="h-4 w-4 text-gray-900" />
              </button>
            </div>
          </div>

          <button
            className="lg:hidden"
            onClick={() => setMobileOpen(true)}
            aria-label="Open navigation"
          >
            <Bars3Icon className="h-6 w-6 text-sky-500 hover:text-amber-400" />
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
              <XMarkIcon className="h-6 w-6 text-sky-500 hover:text-amber-400" />
            </button>
            {navLinks}
            <div className="flex items-stretch">
              <input
                type="search"
                placeholder="Search players..."
                className="flex-1 border border-gray-600 bg-gray-800 text-gray-100 placeholder-gray-400 rounded-l-md px-3 py-1.5 text-sm focus:outline-none focus:border-sky-500"
              />
              <button className="border border-l-0 border-gray-600 rounded-r-md px-3 bg-sky-500 hover:bg-amber-500">
                <MagnifyingGlassIcon className="h-4 w-4 text-gray-900" />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
