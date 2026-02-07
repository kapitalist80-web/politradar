import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { deleteBusiness, getAlerts, getBusinesses } from "../api/client";
import StatusBadge from "../components/StatusBadge";

const fmtDate = (d) =>
  d ? new Date(d).toLocaleDateString("de-CH") : "–";

export default function Dashboard() {
  const [businesses, setBusinesses] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [sortKey, setSortKey] = useState("business_number");
  const [sortDir, setSortDir] = useState("asc");

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

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  const sorted = useMemo(() => {
    const list = [...businesses];
    list.sort((a, b) => {
      let va = a[sortKey];
      let vb = b[sortKey];
      // Treat null/undefined as "last"
      if (va == null && vb == null) return 0;
      if (va == null) return 1;
      if (vb == null) return -1;
      if (typeof va === "string") va = va.toLowerCase();
      if (typeof vb === "string") vb = vb.toLowerCase();
      if (va < vb) return sortDir === "asc" ? -1 : 1;
      if (va > vb) return sortDir === "asc" ? 1 : -1;
      return 0;
    });
    return list;
  }, [businesses, sortKey, sortDir]);

  const SortIcon = ({ col }) => {
    if (sortKey !== col) return <span className="text-gray-300 ml-1">&#8597;</span>;
    return <span className="ml-1">{sortDir === "asc" ? "\u25B2" : "\u25BC"}</span>;
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
        <>
          {/* Desktop: sortable table list */}
          <div className="hidden md:block">
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 text-left text-xs uppercase text-gray-500 dark:text-gray-400">
                    <th
                      className="px-4 py-3 cursor-pointer select-none hover:text-swiss-red"
                      onClick={() => handleSort("business_number")}
                    >
                      Nummer <SortIcon col="business_number" />
                    </th>
                    <th className="px-4 py-3">Titel</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Typ</th>
                    <th
                      className="px-4 py-3 cursor-pointer select-none hover:text-swiss-red"
                      onClick={() => handleSort("submission_date")}
                    >
                      Einreichung <SortIcon col="submission_date" />
                    </th>
                    <th
                      className="px-4 py-3 cursor-pointer select-none hover:text-swiss-red"
                      onClick={() => handleSort("next_event_date")}
                    >
                      Naechster Termin <SortIcon col="next_event_date" />
                    </th>
                    <th className="px-4 py-3"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                  {sorted.map((biz) => (
                    <tr
                      key={biz.id}
                      className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                    >
                      <td className="px-4 py-3 font-mono text-gray-500 whitespace-nowrap">
                        {biz.business_number}
                      </td>
                      <td className="px-4 py-3">
                        <Link
                          to={`/business/${biz.id}`}
                          className="font-medium text-gray-900 dark:text-gray-100 hover:text-swiss-red line-clamp-1"
                        >
                          {biz.title || "Ohne Titel"}
                        </Link>
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge status={biz.status} />
                      </td>
                      <td className="px-4 py-3 text-gray-500 whitespace-nowrap">
                        {biz.business_type || "–"}
                      </td>
                      <td className="px-4 py-3 text-gray-500 whitespace-nowrap">
                        {fmtDate(biz.submission_date)}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        {biz.next_event_date ? (
                          <span className="text-swiss-red font-medium">
                            {fmtDate(biz.next_event_date)}
                          </span>
                        ) : (
                          <span className="text-gray-400">–</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => handleDelete(biz.id)}
                          className="text-red-400 hover:text-red-600 text-xs"
                        >
                          Entfernen
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Mobile: card tiles */}
          <div className="md:hidden grid gap-4 grid-cols-1 sm:grid-cols-2">
            {sorted.map((biz) => (
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
                  <span>{biz.business_type}</span>
                  <button
                    onClick={() => handleDelete(biz.id)}
                    className="text-red-400 hover:text-red-600"
                  >
                    Entfernen
                  </button>
                </div>
                {biz.next_event_date && (
                  <p className="text-xs text-swiss-red mt-2">
                    Naechster Termin: {fmtDate(biz.next_event_date)}
                  </p>
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
