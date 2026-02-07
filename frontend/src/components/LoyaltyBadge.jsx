export default function LoyaltyBadge({ score }) {
  if (score === null || score === undefined) return null;

  const pct = Math.round(score * 100);
  let color, label;

  if (pct >= 80) {
    color = "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
    label = "Hoch";
  } else if (pct >= 50) {
    color = "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200";
    label = "Mittel";
  } else {
    color = "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200";
    label = "Niedrig";
  }

  return (
    <span className={`inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-full ${color}`}>
      Fraktionstreue: {pct}% ({label})
    </span>
  );
}
