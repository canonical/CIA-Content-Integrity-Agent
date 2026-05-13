import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import type { Site } from "../api/types";
import { SiteCard } from "../components/SiteCard";
import { AddSiteModal } from "../components/AddSiteModal";

export function SitesPage() {
  const [showAdd, setShowAdd] = useState(false);
  const queryClient = useQueryClient();

  const { data: sites = [], isLoading } = useQuery({ queryKey: ["sites"], queryFn: () => api.sites.list() });
  const createMutation = useMutation({ mutationFn: api.sites.create, onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["sites"] }); setShowAdd(false); } });
  const deleteMutation = useMutation({ mutationFn: api.sites.delete, onSuccess: () => queryClient.invalidateQueries({ queryKey: ["sites"] }) });

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Sites</h2>
        <button onClick={() => setShowAdd(true)} className="px-4 py-2 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700">Add Site</button>
      </div>
      {isLoading && <p className="text-gray-500">Loading sites...</p>}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {sites.map((site: Site) => <SiteCard key={site.id} site={site} onDelete={() => { if (confirm(`Delete ${site.name}?`)) deleteMutation.mutate(site.id); }} />)}
      </div>
      {!isLoading && sites.length === 0 && <p className="text-gray-500 text-center py-12">No sites yet. Add one to get started.</p>}
      {showAdd && <AddSiteModal onSubmit={(data) => createMutation.mutate(data)} onClose={() => setShowAdd(false)} />}
    </div>
  );
}