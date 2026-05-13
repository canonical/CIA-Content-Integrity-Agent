import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "../api/client";
import { UrlTable } from "../components/UrlTable";

export function SitemapPage() {
  const { siteId } = useParams<{ siteId: string }>();
  const navigate = useNavigate();
  const [scanningUrl, setScanningUrl] = useState<string | null>(null);
  const numericId = Number(siteId);

  const { data: site, isLoading: siteLoading } = useQuery({ queryKey: ["site", numericId], queryFn: () => api.sites.get(numericId), enabled: !isNaN(numericId) });
  const { data: urls = [], isLoading: urlsLoading, error: urlsError } = useQuery({ queryKey: ["sitemap", numericId], queryFn: () => api.sitemaps.getUrls(numericId), enabled: !isNaN(numericId) });
  const scanMutation = useMutation({ mutationFn: (routeUrl: string) => api.scans.create({ site_id: numericId, route_url: routeUrl }), onSuccess: (scan) => navigate(`/scans/${scan.id}`) });

  if (siteLoading) return <p className="text-gray-500">Loading site...</p>;

  return (
    <div>
      <button onClick={() => navigate("/")} className="text-sm text-indigo-600 hover:underline mb-2">&larr; Back to Sites</button>
      <h2 className="text-xl font-semibold text-gray-900">{site?.name}</h2>
      <p className="text-sm text-gray-500">{site?.base_url}</p>
      {urlsError && <div className="bg-red-50 text-red-700 p-4 rounded mb-4">Failed to fetch sitemap: {String(urlsError)}</div>}
      {urlsLoading ? <p className="text-gray-500">Fetching sitemap...</p> : <UrlTable urls={urls} onScan={(url) => { setScanningUrl(url); scanMutation.mutate(url); }} scanningUrl={scanningUrl} />}
    </div>
  );
}