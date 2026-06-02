import { NavLink, Outlet } from "react-router-dom";

const navClass = ({ isActive }: { isActive: boolean }) =>
  [
    "rounded-lg px-4 py-2 text-sm font-medium transition-colors",
    isActive
      ? "bg-indigo-500/20 text-indigo-200"
      : "text-slate-400 hover:bg-slate-800 hover:text-slate-100",
  ].join(" ");

export function Layout() {
  return (
    <div className="flex min-h-screen">
      <aside className="flex w-56 shrink-0 flex-col border-r border-slate-800 bg-slate-900/80 p-4">
        <div className="mb-8 px-2">
          <p className="text-xs font-semibold uppercase tracking-wider text-indigo-400">
            PDF Vector
          </p>
          <h1 className="mt-1 text-lg font-semibold text-white">Doc Chat</h1>
        </div>
        <nav className="flex flex-col gap-1">
          <NavLink to="/" end className={navClass}>
            Upload
          </NavLink>
          <NavLink to="/chat" className={navClass}>
            Chat
          </NavLink>
        </nav>
      </aside>
      <main className="flex flex-1 flex-col overflow-hidden">
        <Outlet />
      </main>
    </div>
  );
}
