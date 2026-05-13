import type { Scan } from "../api/types";

export function ScanProgress({ scan }: { scan: Scan }) {
  const statusColors: Record<string, string> = {
    pending: "bg-gray-200 text-gray-700", crawling: "bg-blue-100 text-blue-700", analyzing: "bg-yellow-100 text-yellow-700",
    complete: "bg-green-100 text-green-700", failed: "bg-red-100 text-red-700", cancelled: "bg-gray-100 text-gray-500",
  };
  return (
    <div className="bg-white rounded-lg border p-4 mb-6">
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-sm text-gray-700">{scan.route_url}</span>
        <span className={`text-xs font-medium px-2 py-1 rounded ${statusColors[scan.status] || "bg-gray-200"}`}>{scan.status.replace(/_/g, " ")}</span>
      </div>
      {scan.current_agent && <p className="text-sm text-gray-500 mb-2">Running {scan.current_agent}...</p>}
      <div className="w-full bg-gray-200 rounded-full h-2"><div className="bg-indigo-600 h-2 rounded-full transition-all duration-300" style={{ width: `${scan.progress}%` }} /></div>
      <p className="text-xs text-gray-400 mt-1">{scan.progress}%</p>
      {scan.error_message && <p className="text-sm text-red-600 mt-2">Error: {scan.error_message}</p>}
    </div>
  );
}