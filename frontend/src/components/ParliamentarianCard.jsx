import { Link } from "react-router-dom";

const FACTION_COLORS = {
  "V": "border-green-700",
  "S": "border-red-600",
  "RL": "border-blue-600",
  "M-E": "border-orange-500",
  "G": "border-green-500",
  "GL": "border-lime-500",
};

function getFactionColor(abbr) {
  if (!abbr) return "border-gray-300 dark:border-gray-600";
  for (const [key, color] of Object.entries(FACTION_COLORS)) {
    if (abbr.includes(key)) return color;
  }
  return "border-gray-300 dark:border-gray-600";
}

export default function ParliamentarianCard({ member, showFunction = false }) {
  const factionColor = getFactionColor(member.parl_group_abbreviation);

  return (
    <Link
      to={`/parliamentarian/${member.person_number}`}
      className={`block bg-white dark:bg-gray-800 rounded-lg border-l-4 ${factionColor} shadow-sm hover:shadow-md transition-shadow p-3`}
    >
      <div className="flex items-center gap-3">
        {member.photo_url && (
          <img
            src={member.photo_url}
            alt={`${member.first_name} ${member.last_name}`}
            className="w-10 h-10 rounded-full object-cover bg-gray-200"
            onError={(e) => { e.target.style.display = "none"; }}
          />
        )}
        <div className="min-w-0 flex-1">
          <div className="font-medium text-sm truncate">
            {member.first_name} {member.last_name}
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-500">
            {member.party_abbreviation && (
              <span className="font-medium">{member.party_abbreviation}</span>
            )}
            {member.canton_abbreviation && (
              <span>{member.canton_abbreviation}</span>
            )}
            {showFunction && member.function && (
              <span className="text-swiss-red">{member.function}</span>
            )}
          </div>
        </div>
        {member.parl_group_abbreviation && (
          <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
            {member.parl_group_abbreviation}
          </span>
        )}
      </div>
    </Link>
  );
}
