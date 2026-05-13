import type { Notification } from "../api/types";

const actionColors: Record<string, string> = {
  auto_fix: "bg-green-100 text-green-700", notify_with_suggestion: "bg-blue-100 text-blue-700",
  notify_investigate: "bg-yellow-100 text-yellow-700", escalate_ops: "bg-red-100 text-red-700", suppress_false_alarm: "bg-gray-100 text-gray-600",
};

export function NotificationsTab({ notifications }: { notifications: Notification[] }) {
  if (notifications.length === 0) return <p className="text-gray-500 text-center py-8">No notifications drafted.</p>;
  return (
    <div className="flex flex-col gap-4">
      {notifications.map((n, i) => (
        <div key={i} className="bg-white border rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="font-medium text-gray-900">{n.recipient.display_name} &lt;{n.recipient.email}&gt;</span>
            <span className={`text-xs px-2 py-0.5 rounded ${actionColors[n.action_taken] || "bg-gray-100"}`}>{n.action_taken.replace(/_/g, " ")}</span>
          </div>
          <p className="text-sm font-medium text-gray-700 mb-1">{n.subject}</p>
          <pre className="text-xs text-gray-600 whitespace-pre-wrap bg-gray-50 p-3 rounded">{n.body}</pre>
        </div>
      ))}
    </div>
  );
}