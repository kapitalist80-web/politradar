import { useEffect, useState } from "react";
import {
  decideCandiate,
  getMonitoringBusinessTypes,
  getMonitoringCandidates,
} from "../api/client";

export default function Monitoring() {
  const [candidates, setCandidates] = useState([]);
  const [tab, setTab] = useState("pending");
  const [businessTypes, setBusinessTypes] = useState([]);
  const [typeFilter, setTypeFilter] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMonitoringBusinessTypes()
      .then((types) => setBusinessTypes(types || []))
      .catch(() => {});
  }, []);

  const load = async () => {
    setLoading(true);
    try {
      const data = await getMonitoringCandidates(tab, typeFilter);
      setCandidates(data || []);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [tab, typeFilter]);

  const handleDecide = async (id, decision) => {
    await decideCandiate(id, decision);
    setCandidates((prev) => prev.filter((c) => c.id !== id));
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Monitoring</h1>

      {/* Tabs */}
      <div className="flex flex-wrap items-center gap-4 mb-6">
        <div className="flex gap-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1 w-fit">
          {["pending", "accepted", "rejected"].map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                tab === t
                  ? "bg-white dark:bg-gray-700 shadow-sm"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              {t === "pending"
                ? "Offen"
                : t === "accepted"
                  ? "Akzeptiert"
                  : "Abgelehnt"}
            </button>
          ))}
        </div>

        {/* Category filter */}
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="text-sm border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200"
        >
          <option value="">Alle Kategorien</option>
          {businessTypes.map((bt) => (
            <option key={bt} value={bt}>
              {bt}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="flex justify-center py-10">
          <div className="animate-spin h-8 w-8 border-4 border-swiss-red border-t-transparent rounded-full" />
        </div>
      ) : candidates.length === 0 ? (
        <p className="text-center py-10 text-gray-500">
          Keine Kandidaten in dieser Kategorie
        </p>
      ) : (
        <div className="space-y-3">
          {candidates.map((c) => (
            <div
              key={c.id}
              className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-5"
            >
              <div className="flex justify-between items-start gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono text-sm text-gray-500">
                      {c.business_number}
                    </span>
                    {c.business_type && (
                      <span className="text-xs px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-500">
                        {c.business_type}
                      </span>
                    )}
                  </div>
                  <h3 className="font-medium">{c.title || "Ohne Titel"}</h3>
                  <p className="text-sm text-gray-500 mt-1 line-clamp-2">
                    {c.description}
                  </p>
                  {c.submission_date && (
                    <p className="text-xs text-gray-400 mt-2">
                      Eingereicht:{" "}
                      {new Date(c.submission_date).toLocaleDateString("de-CH")}
                    </p>
                  )}
                </div>

                {tab === "pending" && (
                  <div className="flex gap-2 flex-shrink-0">
                    <button
                      onClick={() => handleDecide(c.id, "accepted")}
                      className="px-4 py-2 bg-green-600 text-white rounded-md text-sm font-medium hover:bg-green-700"
                    >
                      Relevant
                    </button>
                    <button
                      onClick={() => handleDecide(c.id, "rejected")}
                      className="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-200 rounded-md text-sm font-medium hover:bg-gray-400"
                    >
                      Irrelevant
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
