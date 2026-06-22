import { useState, useEffect } from "react";
import { NavLink, Outlet } from "react-router-dom";
import {
  Menu,
  X,
  Upload,
  LayoutDashboard,
  List,
  IndianRupee,
  Moon,
  Sun,
  Settings,
} from "lucide-react";
import PrivacyBanner from "./PrivacyBanner";
import SettingsPanel from "./SettingsPanel";

const navItems = [
  { to: "/", label: "Upload", icon: Upload },
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/transactions", label: "Transactions", icon: List },
];

function useDarkMode() {
  const [dark, setDark] = useState(() => {
    const saved = localStorage.getItem("rupeeradar-theme");
    if (saved) return saved === "dark";
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  });

  useEffect(() => {
    const root = document.documentElement;
    if (dark) {
      root.classList.add("dark");
      root.style.colorScheme = "dark";
    } else {
      root.classList.remove("dark");
      root.style.colorScheme = "light";
    }
    localStorage.setItem("rupeeradar-theme", dark ? "dark" : "light");
  }, [dark]);

  return [dark, () => setDark((d) => !d)] as const;
}

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [dark, toggleDark] = useDarkMode();
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [offline, setOffline] = useState(!navigator.onLine);

  useEffect(() => {
    const onOff = () => setOffline(true);
    const onOn = () => setOffline(false);
    window.addEventListener("offline", onOff);
    window.addEventListener("online", onOn);
    return () => {
      window.removeEventListener("offline", onOff);
      window.removeEventListener("online", onOn);
    };
  }, []);

  useEffect(() => {
    const handler = () => setSettingsOpen(true);
    window.addEventListener("open-settings", handler);
    return () => window.removeEventListener("open-settings", handler);
  }, []);

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50 text-gray-900 dark:bg-gray-950 dark:text-gray-100">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-30 flex w-64 flex-col bg-gray-900 text-white transition-transform duration-200 lg:static lg:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center gap-3 px-6 py-5 border-b border-gray-700">
          <IndianRupee className="h-7 w-7 text-emerald-400" />
          <span className="text-xl font-bold tracking-tight">RupeeRadar</span>
        </div>

        <nav className="flex-1 space-y-1 px-3 py-4">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-emerald-600 text-white"
                    : "text-gray-300 hover:bg-gray-800 hover:text-white"
                }`
              }
            >
              <item.icon className="h-5 w-5" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* Dark mode toggle at bottom of sidebar */}
        <div className="border-t border-gray-700 px-4 py-2 space-y-1">
          <button
            onClick={() => setSettingsOpen(true)}
            className="flex w-full items-center gap-3 rounded-lg px-4 py-2 text-sm text-gray-400 hover:bg-gray-800 hover:text-white transition-colors"
          >
            <Settings className="h-4 w-4" />
            <span>Settings</span>
          </button>
          <button
            onClick={toggleDark}
            className="flex w-full items-center gap-3 rounded-lg px-4 py-2 text-sm text-gray-400 hover:bg-gray-800 hover:text-white transition-colors"
          >
            {dark ? (
              <Sun className="h-4 w-4 text-amber-400" />
            ) : (
              <Moon className="h-4 w-4 text-gray-400" />
            )}
            <span>{dark ? "Light Mode" : "Dark Mode"}</span>
          </button>
        </div>

        <div className="border-t border-gray-700 px-6 py-4">
          <p className="text-xs text-gray-500">RupeeRadar v1.0</p>
        </div>
      </aside>

      {/* Main content area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top header bar (mobile) */}
        <header className="flex items-center gap-3 border-b border-gray-200 bg-white px-4 py-3 dark:border-gray-800 dark:bg-gray-900 lg:hidden">
          <button
            onClick={() => setSidebarOpen(true)}
            className="rounded-lg p-1.5 text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
            aria-label="Open menu"
          >
            {sidebarOpen ? (
              <X className="h-5 w-5" />
            ) : (
              <Menu className="h-5 w-5" />
            )}
          </button>
          <div className="flex items-center gap-2">
            <IndianRupee className="h-5 w-5 text-emerald-500" />
            <span className="font-semibold text-gray-800 dark:text-gray-200">RupeeRadar</span>
          </div>
          <button
            onClick={toggleDark}
            className="ml-auto rounded-lg p-1.5 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800"
            aria-label="Toggle dark mode"
          >
            {dark ? (
              <Sun className="h-4 w-4 text-amber-400" />
            ) : (
              <Moon className="h-4 w-4" />
            )}
          </button>
        </header>

        {/* Page content */}
        {/* Offline banner */}
        {offline && (
          <div className="flex items-center justify-center gap-2 bg-amber-500 px-4 py-1.5 text-xs font-medium text-white">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-white/60" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-white" />
            </span>
            You are offline. Some features may be unavailable.
          </div>
        )}

        <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>

      {/* Privacy banner & settings */}
      <PrivacyBanner />
      <SettingsPanel open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  );
}
