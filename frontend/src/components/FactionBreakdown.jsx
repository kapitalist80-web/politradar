import VotePredictionBar from "./VotePredictionBar";

export default function FactionBreakdown({ prediction, loading }) {
  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <h2 className="font-semibold mb-4">Abstimmungsprognose</h2>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <div className="animate-spin h-4 w-4 border-2 border-swiss-red border-t-transparent rounded-full" />
          Prognose wird berechnet...
        </div>
      </div>
    );
  }

  if (!prediction) {
    return null;
  }

  const confidenceColor =
    prediction.overall_yes_probability > 0.6
      ? "text-green-600 dark:text-green-400"
      : prediction.overall_yes_probability < 0.4
        ? "text-red-600 dark:text-red-400"
        : "text-yellow-600 dark:text-yellow-400";

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
      <h2 className="font-semibold mb-4">Abstimmungsprognose</h2>

      {/* Overall result */}
      <div className="mb-4 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium">Erwartetes Ergebnis:</span>
          <span className={`font-semibold ${confidenceColor}`}>
            {prediction.expected_result}
          </span>
        </div>
        <VotePredictionBar
          yesRate={prediction.overall_yes_probability}
          noRate={1 - prediction.overall_yes_probability}
          size="lg"
        />
      </div>

      {/* Faction breakdown */}
      {prediction.faction_breakdown && prediction.faction_breakdown.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Aufschluesselung nach Fraktionen
          </h3>
          {prediction.faction_breakdown.map((f) => (
            <div key={f.parl_group_abbreviation} className="flex items-center gap-3">
              <div className="w-16 text-right">
                <span className="text-xs font-medium">
                  {f.parl_group_abbreviation}
                </span>
                <span className="text-xs text-gray-400 ml-1">
                  ({f.member_count})
                </span>
              </div>
              <div className="flex-1">
                <VotePredictionBar
                  yesRate={f.avg_yes}
                  noRate={f.avg_no}
                  size="sm"
                />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Disclaimer */}
      <p className="mt-4 text-xs text-gray-400 italic">
        {prediction.disclaimer}
      </p>

      {/* Member details toggle */}
      {prediction.member_predictions && prediction.member_predictions.length > 0 && (
        <details className="mt-4">
          <summary className="text-sm text-swiss-red cursor-pointer hover:underline">
            Einzelprognosen anzeigen ({prediction.member_predictions.length} Mitglieder)
          </summary>
          <div className="mt-3 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left py-2 pr-3">Name</th>
                  <th className="text-left py-2 pr-3">Partei</th>
                  <th className="text-left py-2 pr-3">Kanton</th>
                  <th className="text-left py-2 pr-3">Prognose</th>
                  <th className="text-right py-2">Konfidenz</th>
                </tr>
              </thead>
              <tbody>
                {prediction.member_predictions.map((mp) => {
                  const mainPred =
                    mp.predicted_yes > mp.predicted_no ? "Ja" : mp.predicted_no > mp.predicted_yes ? "Nein" : "Unsicher";
                  const predColor =
                    mainPred === "Ja"
                      ? "text-green-600 dark:text-green-400"
                      : mainPred === "Nein"
                        ? "text-red-600 dark:text-red-400"
                        : "text-gray-500";
                  const confPct = Math.round(mp.confidence * 100);
                  const confColor =
                    confPct >= 70
                      ? "text-green-600"
                      : confPct >= 50
                        ? "text-yellow-600"
                        : "text-gray-400";

                  return (
                    <tr key={mp.person_number} className="border-b border-gray-100 dark:border-gray-800">
                      <td className="py-1.5 pr-3">
                        {mp.first_name} {mp.last_name}
                      </td>
                      <td className="py-1.5 pr-3 text-gray-500">
                        {mp.party_abbreviation}
                      </td>
                      <td className="py-1.5 pr-3 text-gray-500">
                        {mp.canton_abbreviation}
                      </td>
                      <td className={`py-1.5 pr-3 font-medium ${predColor}`}>
                        {mainPred}
                      </td>
                      <td className={`py-1.5 text-right ${confColor}`}>
                        {confPct}%
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </details>
      )}
    </div>
  );
}
