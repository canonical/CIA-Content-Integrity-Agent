import { useState } from "react";
import type { SitemapUrl } from "../api/types";

interface Props {
  urls: SitemapUrl[];
  onScan: (url: string) => void;
  scanningUrl: string | null;
}

export function UrlTable({ urls, onScan, scanningUrl }: Props) {
  const [search, setSearch] = useState("");
  const filtered = urls.filter((u) => !search || u.url.toLowerCase().includes(search.toLowerCase()));

  return (
    <div>
      <input className="border rounded px-3 py-2 text-sm w-full max-w-md mb-4" placeholder="Filter URLs..." value={search} onChange={(e) => setSearch(e.target.value)} />
      <div className="overflow-auto border rounded max-h-[70vh]">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 sticky top-0">
            <tr>
              <th className="text-left px-4 py-2 font-medium text-gray-600">URL</th>
              <th className="text-left px-4 py-2 font-medium text-gray-600 w-40">Last Modified</th>
              <th className="text-right px-4 py-2 font-medium text-gray-600 w-24">Action</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((u, i) => (
              <tr key={i} className="border-t hover:bg-gray-50">
                <td className="px-4 py-2 font-mono text-xs break-all">{u.url}</td>
                <td className="px-4 py-2 text-gray-500 text-xs">{u.lastmod ? new Date(u.lastmod).toLocaleDateString() : "—"}</td>
                <td className="px-4 py-2 text-right">
                  <button onClick={() => onScan(u.url)} disabled={scanningUrl !== null}
                    className={`text-xs px-3 py-1 rounded ${scanningUrl === u.url ? "bg-gray-200 text-gray-500" : "bg-indigo-50 text-indigo-700 hover:bg-indigo-100"}`}>
                    {scanningUrl === u.url ? "Scanning..." : "Scan"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && <p className="text-center text-gray-400 py-8 text-sm">No URLs found</p>}
      </div>
      <p className="text-xs text-gray-400 mt-2">{filtered.length} URLs shown</p>
    </div>
  );
}