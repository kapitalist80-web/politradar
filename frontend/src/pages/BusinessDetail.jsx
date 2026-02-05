import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { deleteBusiness, getBusiness } from "../api/client";
import StatusBadge from "../components/StatusBadge";

export default function BusinessDetail() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    getBusiness(id)
      .then(setData)
      .catch(() => navigate("/"))
      .finally(() => setLoading(false));
  }, [id, navigate]);

  const handleDelete = async () => {
    if (!confirm("Tracking beenden?")) return;
    await deleteBusiness(id);
    navigate("/");
  };

  if (loading || !data) {
    return (
      <div className="flex justify-center py-20">
        <div className="animate-spin h-8 w-8 border-4 border-swiss-red border-t-transparent rounded-full" />
      </div>
    );
  }

  const { business, events } = data;

  return (
    <div className="max-w-3xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <span className="font-mono text-gray-500">
            {business.business_number}
          </span>
          <StatusBadge status={business.status} />
        </div>
        <h1 className="text-2xl font-bold mb-2">
          {business.title || "Ohne Titel"}
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          {business.description}
        </p>
        <div className="flex gap-4 mt-3 text-sm text-gray-500">
          {business.business_type && <span>{business.business_type}</span>}
          {business.submission_date && (
            <span>
              Eingereicht:{" "}
              {new Date(business.submission_date).toLocaleDateString("de-CH")}
            </span>
          )}
          {business.last_api_sync && (
            <span>
              Letzter Sync:{" "}
              {new Date(business.last_api_sync).toLocaleString("de-CH")}
            </span>
          )}
        </div>
      </div>

      {/* Timeline */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <h2 className="font-semibold mb-4">Eventverlauf</h2>
        {events.length === 0 ? (
          <p className="text-sm text-gray-500">Noch keine Events</p>
        ) : (
          <div className="space-y-4">
            {events.map((evt) => (
              <div key={evt.id} className="flex gap-4">
                <div className="flex flex-col items-center">
                  <div className="w-3 h-3 rounded-full bg-swiss-red" />
                  <div className="w-px flex-1 bg-gray-200 dark:bg-gray-700" />
                </div>
                <div className="pb-4">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-medium px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
                      {evt.event_type}
                    </span>
                    {evt.event_date && (
                      <time className="text-xs text-gray-400">
                        {new Date(evt.event_date).toLocaleDateString("de-CH")}
                      </time>
                    )}
                  </div>
                  <p className="text-sm">{evt.description}</p>
                  {evt.committee_name && (
                    <p className="text-xs text-gray-500 mt-1">
                      Kommission: {evt.committee_name}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <button
        onClick={handleDelete}
        className="text-sm text-red-500 hover:text-red-700"
      >
        Tracking beenden
      </button>
    </div>
  );
}
