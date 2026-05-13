import type { LinkFailure } from "../api/types";

const severityColors: Record<string, string> = {
  critical_404: "bg-red-100 text-red-700", timeout: "bg-yellow-100 text-yellow-700",
  redirect_chain: "bg-orange-100 text-orange-700", soft_404: "bg-yellow-100 text-yellow-700", unknown: "bg-gray-100 text-gray-700",
};

export function BrokenLinksTab({ failures }: { failures: LinkFailure[] }) {
  if (failures.length === 0) return <p className="text-gray-500 text-center py-8">No broken links found!</p>;
  return (
    <div className="overflow-auto border rounded">
      <table className="w-full text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="text-left px-4 py-2 font-medium text-gray-600">Broken URL</th>
            <th className="text-left px-4 py-2 font-medium text-gray-600">Source Page</th>
            <th className="text-left px-4 py-2 font-medium text-gray-600 w-20">Status</th>
            <th className="text-left px-4 py-2 font-medium text-gray-600 w-32">Severity</th>
          </tr>
        </thead>
        <tbody>
          {failures.map((f, i) => (
            <tr key={i} className="border-t hover:bg-gray-50">
              <td className="px-4 py-2 font-mono text-xs break-all">{f.broken_url}</td>
              <td className="px-4 py-2 font-mono text-xs break-all">{f.source_page}</td>
              <td className="px-4 py-2 text-gray-600">{f.status_code || "—"}</td>
              <td className="px-4 py-2"><span className={`text-xs px-2 py-0.5 rounded ${severityColors[f.severity] || "bg-gray-100"}`}>{f.severity}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}