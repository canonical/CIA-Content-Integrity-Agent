import { NavLink, Outlet } from "react-router-dom";

export function Layout() {
  return (
    <div className="flex h-screen bg-gray-50">
      <nav className="w-56 bg-white border-r border-gray-200 p-4 flex flex-col">
        <h1 className="text-lg font-bold text-gray-900 mb-6">CIA Dashboard</h1>
        <div className="flex flex-col gap-1">
          <NavLink to="/" className={({ isActive }) =>
            `px-3 py-2 rounded text-sm font-medium ${isActive ? "bg-indigo-50 text-indigo-700" : "text-gray-600 hover:bg-gray-100"}`
          }>Sites</NavLink>
          <NavLink to="/scans" className={({ isActive }) =>
            `px-3 py-2 rounded text-sm font-medium ${isActive ? "bg-indigo-50 text-indigo-700" : "text-gray-600 hover:bg-gray-100"}`
          }>Recent Scans</NavLink>
        </div>
      </nav>
      <main className="flex-1 overflow-auto p-6"><Outlet /></main>
    </div>
  );
}