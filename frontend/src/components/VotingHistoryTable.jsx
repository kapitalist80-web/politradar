const DECISION_STYLES = {
  Yes: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  No: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
  Abstention: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
  Absent: "bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400",
  President: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
};

const DECISION_LABELS = {
  Yes: "Ja",
  No: "Nein",
  Abstention: "Enthaltung",
  Absent: "Abwesend",
  President: "Präsidium",
};

export default function VotingHistoryTable({ votes, loading }) {
  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-500 py-4">
        <div className="animate-spin h-4 w-4 border-2 border-swiss-red border-t-transparent rounded-full" />
        Abstimmungen werden geladen...
      </div>
    );
  }

  if (!votes || votes.length === 0) {
    return <p className="text-sm text-gray-500">Keine Abstimmungsdaten vorhanden</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200 dark:border-gray-700">
            <th className="text-left py-2 pr-3">Datum</th>
            <th className="text-left py-2 pr-3">Geschäft</th>
            <th className="text-left py-2 pr-3">Gegenstand</th>
            <th className="text-left py-2 pr-3">Stimme</th>
            <th className="text-left py-2">Ergebnis</th>
          </tr>
        </thead>
        <tbody>
          {votes.map((v, i) => (
            <tr key={i} className="border-b border-gray-100 dark:border-gray-800">
              <td className="py-2 pr-3 text-gray-500 whitespace-nowrap">
                {v.vote_date
                  ? new Date(v.vote_date).toLocaleDateString("de-CH")
                  : "-"}
              </td>
              <td className="py-2 pr-3 font-mono text-xs">
                {v.business_number || "-"}
              </td>
              <td className="py-2 pr-3 max-w-xs truncate" title={v.subject}>
                {v.subject || v.business_title || "-"}
              </td>
              <td className="py-2 pr-3">
                <span
                  className={`inline-flex text-xs font-medium px-2 py-0.5 rounded ${
                    DECISION_STYLES[v.decision] || "bg-gray-100 text-gray-600"
                  }`}
                >
                  {DECISION_LABELS[v.decision] || v.decision}
                </span>
              </td>
              <td className="py-2 text-gray-500 text-xs">
                {v.result || "-"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
