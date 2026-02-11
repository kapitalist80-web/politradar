import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { deleteBusiness, getAlerts, getBusinesses, updateBusinessPriority } from "../api/client";
import StatusBadge from "../components/StatusBadge";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";

const fmtDate = (d) =>
  d ? new Date(d).toLocaleDateString("de-CH") : "–";

const PRIORITY_LABELS = { 1: "1 (Hoch)", 2: "2 (Mittel)", 3: "3 (Niedrig)" };

function PriorityBadge({ value }) {
  if (!value) return <span className="text-gray-400">–</span>;
  const colors = {
    1: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
    2: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
    3: "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300",
  };
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded ${colors[value] || ""}`}>
      {PRIORITY_LABELS[value] || value}
    </span>
  );
}

export default function Dashboard() {
  const [businesses, setBusinesses] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [sortKey, setSortKey] = useState("submission_date");
  const [sortDir, setSortDir] = useState("desc");

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

  const handlePriorityChange = async (id, value) => {
    const priority = value ? parseInt(value) : null;
    await updateBusinessPriority(id, priority);
    setBusinesses((prev) =>
      prev.map((b) => (b.id === id ? { ...b, priority } : b))
    );
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

  const handleExportPDF = () => {
    const doc = new jsPDF({ orientation: "landscape" });
    doc.setFontSize(16);
    doc.text("Parlamentsmonitor \u2013 Geschäftsübersicht", 14, 15);
    doc.setFontSize(9);
    doc.text(`Exportiert am ${new Date().toLocaleDateString("de-CH")}`, 14, 22);

    const headers = [["Nummer", "Titel", "Status", "Typ", "Priorität", "Einreichung", "Nächster Termin"]];
    const rows = sorted.map((biz) => [
      biz.business_number,
      biz.title || "Ohne Titel",
      biz.status || "–",
      biz.business_type || "–",
      biz.priority ? PRIORITY_LABELS[biz.priority] : "–",
      fmtDate(biz.submission_date),
      fmtDate(biz.next_event_date),
    ]);

    autoTable(doc, {
      head: headers,
      body: rows,
      startY: 28,
      styles: { fontSize: 9 },
      headStyles: { fillColor: [213, 43, 30] },
      columnStyles: {
        0: { cellWidth: 25 },
        1: { cellWidth: 80 },
      },
    });

    doc.save(`parlamentsmonitor-${new Date().toISOString().slice(0, 10)}.pdf`);
  };

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
        <div className="flex items-center gap-3">
          {unreadCount > 0 && (
            <Link
              to="/alerts"
              className="text-sm bg-swiss-red text-white px-3 py-1 rounded-full"
            >
              {unreadCount} ungelesene Alerts
            </Link>
          )}
          {businesses.length > 0 && (
            <button
              onClick={handleExportPDF}
              className="bg-gray-800 dark:bg-gray-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-700 transition-colors"
            >
              PDF Export
            </button>
          )}
          <Link
            to="/add"
            className="bg-swiss-red text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-swiss-dark transition-colors"
          >
            + Geschäft hinzufügen
          </Link>
        </div>
      </div>

      {businesses.length === 0 ? (
        <div className="text-center py-20 text-gray-500">
          <p className="text-lg mb-2">Noch keine Geschäfte verfolgt</p>
          <Link to="/add" className="text-swiss-red hover:underline">
            Jetzt ein Geschäft hinzufügen
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
                    <th
                      className="px-4 py-3 cursor-pointer select-none hover:text-swiss-red"
                      onClick={() => handleSort("status")}
                    >
                      Status <SortIcon col="status" />
                    </th>
                    <th className="px-4 py-3">Typ</th>
                    <th
                      className="px-4 py-3 cursor-pointer select-none hover:text-swiss-red"
                      onClick={() => handleSort("priority")}
                    >
                      Priorität <SortIcon col="priority" />
                    </th>
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
                      Nächster Termin <SortIcon col="next_event_date" />
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
                          className="font-medium text-gray-900 dark:text-gray-100 hover:text-swiss-red line-clamp-2"
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
                      <td className="px-4 py-3">
                        <select
                          value={biz.priority || ""}
                          onChange={(e) => handlePriorityChange(biz.id, e.target.value)}
                          onClick={(e) => e.stopPropagation()}
                          className="text-xs border border-gray-300 dark:border-gray-600 rounded px-1.5 py-0.5 bg-white dark:bg-gray-700"
                        >
                          <option value="">–</option>
                          <option value="1">1 (Hoch)</option>
                          <option value="2">2 (Mittel)</option>
                          <option value="3">3 (Niedrig)</option>
                        </select>
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
                  <div className="flex items-center gap-2">
                    <PriorityBadge value={biz.priority} />
                    <StatusBadge status={biz.status} />
                  </div>
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
                    Nächster Termin: {fmtDate(biz.next_event_date)}
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
