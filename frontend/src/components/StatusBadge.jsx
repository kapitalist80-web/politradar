const STATUS_COLORS = {
  active: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300",
  pending: "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300",
  completed:
    "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300",
  default:
    "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300",
};

function resolveColor(status) {
  if (!status) return STATUS_COLORS.default;
  const s = status.toLowerCase();
  if (s.includes("erledigt") || s.includes("abgeschlossen"))
    return STATUS_COLORS.completed;
  if (
    s.includes("rat") ||
    s.includes("kommission") ||
    s.includes("behandlung")
  )
    return STATUS_COLORS.active;
  if (s.includes("haengig") || s.includes("eingereicht"))
    return STATUS_COLORS.pending;
  return STATUS_COLORS.default;
}

export default function StatusBadge({ status }) {
  if (!status) return null;
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${resolveColor(status)}`}
    >
      {status}
    </span>
  );
}
