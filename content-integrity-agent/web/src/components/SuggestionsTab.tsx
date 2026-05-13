import type { FixSuggestion } from "../api/types";

export function SuggestionsTab({ suggestions }: { suggestions: Record<string, FixSuggestion[]> }) {
  const allSuggestions = Object.values(suggestions).flat();
  if (allSuggestions.length === 0) return <p className="text-gray-500 text-center py-8">No suggestions generated.</p>;
  return (
    <div className="overflow-auto border rounded">
      <table className="w-full text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="text-left px-4 py-2 font-medium text-gray-600">Original URL</th>
            <th className="text-left px-4 py-2 font-medium text-gray-600">Suggested URL</th>
            <th className="text-left px-4 py-2 font-medium text-gray-600 w-32">Confidence</th>
            <th className="text-left px-4 py-2 font-medium text-gray-600">Explanation</th>
          </tr>
        </thead>
        <tbody>
          {allSuggestions.map((s, i) => (
            <tr key={i} className="border-t hover:bg-gray-50">
              <td className="px-4 py-2 font-mono text-xs break-all">{s.original_url}</td>
              <td className="px-4 py-2 font-mono text-xs break-all text-green-700">{s.suggested_url || "—"}</td>
              <td className="px-4 py-2">
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div className={`h-2 rounded-full ${s.confidence >= 0.9 ? "bg-green-500" : s.confidence >= 0.6 ? "bg-yellow-500" : "bg-red-400"}`} style={{ width: `${Math.round(s.confidence * 100)}%` }} />
                  </div>
                  <span className="text-xs text-gray-600 w-10">{(s.confidence * 100).toFixed(0)}%</span>
                </div>
              </td>
              <td className="px-4 py-2 text-gray-600 text-xs">{s.suggestion_text || s.reasoning}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}