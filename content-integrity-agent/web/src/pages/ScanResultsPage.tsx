import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import type { Scan, ScanStatus } from "../api/types";
import { useScanProgress } from "../hooks/useScanProgress";
import { ScanProgress } from "../components/ScanProgress";
import { BrokenLinksTab } from "../components/BrokenLinksTab";
import { SuggestionsTab } from "../components/SuggestionsTab";
import { NotificationsTab } from "../components/NotificationsTab";
import { AuditLogTab } from "../components/AuditLogTab";

type Tab = "links" | "suggestions" | "notifications" | "audit";

export function ScanResultsPage() {
  const { scanId } = useParams<{ scanId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const numericId = Number(scanId);
  const [activeTab, setActiveTab] = useState<Tab>("links");

  const { data: scan, isLoading } = useQuery({
    queryKey: ["scan", numericId],
    queryFn: () => api.scans.get(numericId),
    enabled: !isNaN(numericId),
    refetchInterval: (q) => {
      const d = q.state.data;
      if (d && !["complete", "failed", "cancelled"].includes(d.status)) return 2000;
      return false;
    },
  });

  const onProgress = useCallback((event: { scan_id: number; status: ScanStatus; progress: number; current_agent: string | null }) => {
    queryClient.setQueryData(["scan", numericId], (old: Scan | undefined) =>
      old ? { ...old, status: event.status, progress: event.progress, current_agent: event.current_agent } : old
    );
  }, [numericId, queryClient]);

  const onComplete = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ["scan", numericId] });
  }, [numericId, queryClient]);

  const { connect, disconnect } = useScanProgress({ scanId: numericId, onProgress, onComplete });

  useEffect(() => {
    if (scan && !["complete", "failed", "cancelled"].includes(scan.status)) connect();
    return () => { disconnect(); };
  }, [scan?.status, connect, disconnect]);

  if (isLoading) return <p className="text-gray-500">Loading scan...</p>;
  if (!scan) return <p className="text-gray-500">Scan not found.</p>;

  const isDone = ["complete", "failed", "cancelled"].includes(scan.status);
  const results = scan.results;
  const tabs: { key: Tab; label: string; count?: number }[] = [
    { key: "links", label: "Broken Links", count: results?.failures?.length },
    { key: "suggestions", label: "Suggestions", count: results?.suggestions ? Object.keys(results.suggestions).length : 0 },
    { key: "notifications", label: "Notifications", count: results?.notifications?.length },
    { key: "audit", label: "Audit Log", count: results?.audit_log?.length },
  ];

  return (
    <div>
      <button onClick={() => navigate(-1)} className="text-sm text-indigo-600 hover:underline mb-2">&larr; Back</button>
      <ScanProgress scan={scan} />
      {scan.status === "crawling" || scan.status === "analyzing" || scan.status === "pending" ? (
        <p className="text-gray-500 text-center py-8">Scan in progress, results will appear here when complete...</p>
      ) : isDone && results ? (
        <div>
          <div className="flex border-b mb-4">
            {tabs.map((tab) => (
              <button key={tab.key} onClick={() => setActiveTab(tab.key)} className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${activeTab === tab.key ? "border-indigo-600 text-indigo-600" : "border-transparent text-gray-500 hover:text-gray-700"}`}>
                {tab.label}{tab.count !== undefined && <span className="ml-1.5 bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded-full text-xs">{tab.count}</span>}
              </button>
            ))}
          </div>
          {activeTab === "links" && <BrokenLinksTab failures={results.failures || []} />}
          {activeTab === "suggestions" && <SuggestionsTab suggestions={results.suggestions || {}} />}
          {activeTab === "notifications" && <NotificationsTab notifications={results.notifications || []} />}
          {activeTab === "audit" && <AuditLogTab entries={results.audit_log || []} />}
        </div>
      ) : scan.status === "failed" ? (
        <div className="bg-red-50 text-red-700 p-6 rounded"><h3 className="font-semibold mb-1">Scan Failed</h3><p className="text-sm">{scan.error_message || "Unknown error"}</p></div>
      ) : null}
    </div>
  );
}