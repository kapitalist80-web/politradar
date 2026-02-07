import { markAlertRead } from "../api/client";

const TYPE_LABELS = {
  status_change: "Statusaenderung",
  committee_scheduled: "Kommission",
  debate_scheduled: "Debatte",
  new_document: "Dokument",
  vote_result: "Abstimmung",
};

export default function AlertItem({ alert, onUpdated }) {
  const handleRead = async () => {
    if (alert.is_read) return;
    await markAlertRead(alert.id);
    onUpdated?.();
  };

  return (
    <div
      onClick={handleRead}
      className={`p-4 rounded-lg border cursor-pointer transition-colors ${
        alert.is_read
          ? "bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700"
          : "bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800"
      }`}
    >
      <div className="flex justify-between items-start gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-medium px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
              {TYPE_LABELS[alert.alert_type] || alert.alert_type}
            </span>
            <span className="text-xs text-gray-500">
              {alert.business_number}
            </span>
            {!alert.is_read && (
              <span className="w-2 h-2 rounded-full bg-swiss-red flex-shrink-0" />
            )}
          </div>
          <p className="text-sm text-gray-800 dark:text-gray-200">
            {alert.message}
          </p>
          {alert.event_date && (
            <p className="text-xs text-gray-400 mt-1">
              Termin: {new Date(alert.event_date).toLocaleDateString("de-CH")}
            </p>
          )}
        </div>
        <time className="text-xs text-gray-400 whitespace-nowrap">
          {new Date(alert.created_at).toLocaleDateString("de-CH")}
        </time>
      </div>
    </div>
  );
}
