export default function VotePredictionBar({ yesRate, noRate, abstainRate = 0, size = "md" }) {
  const yesPct = Math.round((yesRate || 0) * 100);
  const noPct = Math.round((noRate || 0) * 100);
  const abstainPct = Math.round((abstainRate || 0) * 100);

  const h = size === "sm" ? "h-3" : size === "lg" ? "h-6" : "h-4";

  return (
    <div className="w-full">
      <div className={`flex ${h} rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700`}>
        {yesPct > 0 && (
          <div
            className="bg-green-500 transition-all"
            style={{ width: `${yesPct}%` }}
            title={`Ja: ${yesPct}%`}
          />
        )}
        {abstainPct > 0 && (
          <div
            className="bg-yellow-400 transition-all"
            style={{ width: `${abstainPct}%` }}
            title={`Enthaltung: ${abstainPct}%`}
          />
        )}
        {noPct > 0 && (
          <div
            className="bg-red-500 transition-all"
            style={{ width: `${noPct}%` }}
            title={`Nein: ${noPct}%`}
          />
        )}
      </div>
      <div className="flex justify-between text-xs text-gray-500 mt-1">
        <span className="text-green-600 dark:text-green-400">{yesPct}% Ja</span>
        {abstainPct > 0 && (
          <span className="text-yellow-600 dark:text-yellow-400">{abstainPct}% Enth.</span>
        )}
        <span className="text-red-600 dark:text-red-400">{noPct}% Nein</span>
      </div>
    </div>
  );
}
