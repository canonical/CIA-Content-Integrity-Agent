import type { AuditLogEntry } from "../api/types";

export function AuditLogTab({ entries }: { entries: AuditLogEntry[] }) {
  if (entries.length === 0) return <p className="text-gray-500 text-center py-8">No audit log entries.</p>;
  return (
    <div className="overflow-auto border rounded">
      <table className="w-full text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="text-left px-4 py-2 font-medium text-gray-600 w-44">Timestamp</th>
            <th className="text-left px-4 py-2 font-medium text-gray-600 w-32">Agent</th>
            <th className="text-left px-4 py-2 font-medium text-gray-600 w-40">Action</th>
            <th className="text-left px-4 py-2 font-medium text-gray-600">Input</th>
            <th className="text-left px-4 py-2 font-medium text-gray-600">Output</th>
            <th className="text-left px-4 py-2 font-medium text-gray-600 w-20">Conf</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((e, i) => (
            <tr key={i} className="border-t hover:bg-gray-50">
              <td className="px-4 py-2 text-xs text-gray-500">{e.timestamp}</td>
              <td className="px-4 py-2 text-xs font-medium">{e.agent_name}</td>
              <td className="px-4 py-2 text-xs">{e.action}</td>
              <td className="px-4 py-2 text-xs text-gray-600 break-all">{e.input_summary}</td>
              <td className="px-4 py-2 text-xs text-gray-600 break-all">{e.output_summary}</td>
              <td className="px-4 py-2 text-xs">{e.confidence !== null ? (e.confidence * 100).toFixed(0) + "%" : "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}