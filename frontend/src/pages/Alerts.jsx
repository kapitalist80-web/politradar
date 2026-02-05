import { useEffect, useState } from "react";
import { getAlerts, markAllAlertsRead } from "../api/client";
import AlertItem from "../components/AlertItem";

const ALERT_TYPES = [
  { value: "", label: "Alle" },
  { value: "status_change", label: "Statusaenderung" },
  { value: "committee_scheduled", label: "Kommission" },
  { value: "debate_scheduled", label: "Debatte" },
  { value: "new_document", label: "Dokument" },
  { value: "vote_result", label: "Abstimmung" },
];

export default function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [filter, setFilter] = useState("");
  const [showUnread, setShowUnread] = useState(false);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const params = {};
      if (filter) params.alert_type = filter;
      if (showUnread) params.is_read = false;
      const data = await getAlerts(params);
      setAlerts(data || []);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [filter, showUnread]);

  const handleMarkAll = async () => {
    await markAllAlertsRead();
    load();
  };

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Alerts</h1>
        <button
          onClick={handleMarkAll}
          className="text-sm text-gray-500 hover:text-swiss-red"
        >
          Alle als gelesen markieren
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2 mb-6">
        {ALERT_TYPES.map((t) => (
          <button
            key={t.value}
            onClick={() => setFilter(t.value)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
              filter === t.value
                ? "bg-swiss-red text-white"
                : "bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600"
            }`}
          >
            {t.label}
          </button>
        ))}
        <button
          onClick={() => setShowUnread(!showUnread)}
          className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
            showUnread
              ? "bg-blue-600 text-white"
              : "bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600"
          }`}
        >
          Nur ungelesene
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-10">
          <div className="animate-spin h-8 w-8 border-4 border-swiss-red border-t-transparent rounded-full" />
        </div>
      ) : alerts.length === 0 ? (
        <p className="text-center py-10 text-gray-500">Keine Alerts</p>
      ) : (
        <div className="space-y-3">
          {alerts.map((a) => (
            <AlertItem key={a.id} alert={a} onUpdated={load} />
          ))}
        </div>
      )}
    </div>
  );
}
