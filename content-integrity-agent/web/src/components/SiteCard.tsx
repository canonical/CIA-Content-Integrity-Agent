import type { Site } from "../api/types";
import { useNavigate } from "react-router-dom";

export function SiteCard({ site, onDelete }: { site: Site; onDelete: () => void }) {
  const navigate = useNavigate();
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-sm transition-shadow">
      <div className="flex items-start justify-between">
        <div className="cursor-pointer flex-1" onClick={() => navigate(`/sites/${site.id}`)}>
          <h3 className="font-semibold text-gray-900">{site.name}</h3>
          <p className="text-sm text-gray-500 mt-1">{site.base_url}</p>
          {site.last_scanned_at && (
            <p className="text-xs text-gray-400 mt-2">Last scanned: {new Date(site.last_scanned_at).toLocaleDateString()}</p>
          )}
        </div>
        <button onClick={(e) => { e.stopPropagation(); onDelete(); }} className="text-gray-400 hover:text-red-500 text-sm ml-2">Delete</button>
      </div>
    </div>
  );
}