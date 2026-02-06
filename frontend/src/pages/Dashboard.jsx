import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { deleteBusiness, getAlerts, getBusinesses } from "../api/client";
import StatusBadge from "../components/StatusBadge";

export default function Dashboard() {
  const [businesses, setBusinesses] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const [biz, alerts] = await Promise.all([
        getBusinesses(),
        getAlerts({ is_read: false }),
      ]);
      setBusinesses(biz || []);
      setUnreadCount(Array.isArray(alerts) ? alerts.length : 0);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleDelete = async (id) => {
    if (!confirm("Tracking beenden?")) return;
    await deleteBusiness(id);
    load();
  };

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="animate-spin h-8 w-8 border-4 border-swiss-red border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <div className="flex items-center gap-4">
          {unreadCount > 0 && (
            <Link
              to="/alerts"
              className="text-sm bg-swiss-red text-white px-3 py-1 rounded-full"
            >
              {unreadCount} ungelesene Alerts
            </Link>
          )}
          <Link
            to="/add"
            className="bg-swiss-red text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-swiss-dark transition-colors"
          >
            + Geschaeft hinzufuegen
          </Link>
        </div>
      </div>

      {businesses.length === 0 ? (
        <div className="text-center py-20 text-gray-500">
          <p className="text-lg mb-2">Noch keine Geschaefte verfolgt</p>
          <Link to="/add" className="text-swiss-red hover:underline">
            Jetzt ein Geschaeft hinzufuegen
          </Link>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {businesses.map((biz) => (
            <div
              key={biz.id}
              className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-5 hover:shadow-md transition-shadow"
            >
              <div className="flex justify-between items-start mb-2">
                <span className="text-sm font-mono text-gray-500">
                  {biz.business_number}
                </span>
                <StatusBadge status={biz.status} />
              </div>
              <Link
                to={`/business/${biz.id}`}
                className="block font-medium text-gray-900 dark:text-gray-100 hover:text-swiss-red mb-2 line-clamp-2"
              >
                {biz.title || "Ohne Titel"}
              </Link>
              <p className="text-sm text-gray-500 line-clamp-2 mb-3">
                {biz.description || ""}
              </p>
              <div className="flex justify-between items-center text-xs text-gray-400">
                <span>
                  {biz.business_type}
                </span>
                <button
                  onClick={() => handleDelete(biz.id)}
                  className="text-red-400 hover:text-red-600"
                >
                  Entfernen
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
