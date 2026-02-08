import { useState } from "react";
import { Link } from "react-router-dom";

const FACTION_COLORS = {
  "V": { bg: "bg-green-700", text: "text-green-700", light: "bg-green-100 dark:bg-green-900/30" },
  "S": { bg: "bg-red-600", text: "text-red-600", light: "bg-red-100 dark:bg-red-900/30" },
  "RL": { bg: "bg-blue-600", text: "text-blue-600", light: "bg-blue-100 dark:bg-blue-900/30" },
  "M-E": { bg: "bg-orange-500", text: "text-orange-500", light: "bg-orange-100 dark:bg-orange-900/30" },
  "G": { bg: "bg-green-500", text: "text-green-500", light: "bg-green-100 dark:bg-green-900/30" },
  "GL": { bg: "bg-lime-500", text: "text-lime-500", light: "bg-lime-100 dark:bg-lime-900/30" },
};

function getFactionStyle(abbr) {
  if (!abbr) return { bg: "bg-gray-400", text: "text-gray-500", light: "bg-gray-100 dark:bg-gray-800" };
  for (const [key, style] of Object.entries(FACTION_COLORS)) {
    if (abbr.includes(key)) return style;
  }
  return { bg: "bg-gray-400", text: "text-gray-500", light: "bg-gray-100 dark:bg-gray-800" };
}

export default function CommitteePanel({ treatingBody, loading }) {
  const [expandedFaction, setExpandedFaction] = useState(null);

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <h2 className="font-semibold mb-4">Behandelndes Gremium</h2>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <div className="animate-spin h-4 w-4 border-2 border-swiss-red border-t-transparent rounded-full" />
          Gremiumsdaten werden geladen...
        </div>
      </div>
    );
  }

  if (!treatingBody || !treatingBody.next_body_name) {
    return null;
  }

  // Group members by faction, sorted by size
  const factionGroups = {};
  if (treatingBody.members) {
    for (const m of treatingBody.members) {
      const key = m.parl_group_abbreviation || "Andere";
      if (!factionGroups[key]) {
        factionGroups[key] = [];
      }
      factionGroups[key].push(m);
    }
  }
  const sortedFactions = Object.entries(factionGroups).sort(
    (a, b) => b[1].length - a[1].length,
  );
  const totalMembers = treatingBody.members?.length || 0;

  const toggleFaction = (faction) => {
    setExpandedFaction(expandedFaction === faction ? null : faction);
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
      <h2 className="font-semibold mb-2">Behandelndes Gremium</h2>
      <div className="flex items-center gap-2 mb-4">
        <span className="text-lg font-medium">{treatingBody.next_body_name}</span>
        {treatingBody.next_body_abbreviation && (
          <span className="text-xs px-2 py-0.5 rounded bg-blue-100 dark:bg-blue-800 text-blue-700 dark:text-blue-200">
            {treatingBody.next_body_abbreviation}
          </span>
        )}
        {treatingBody.next_date && (
          <span className="text-sm text-gray-500 ml-2">
            {new Date(treatingBody.next_date).toLocaleDateString("de-CH")}
          </span>
        )}
      </div>

      {totalMembers > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Sitzverteilung ({totalMembers} Sitze)
          </h3>

          {/* Seat distribution bar */}
          <div className="flex h-8 rounded-lg overflow-hidden mb-4">
            {sortedFactions.map(([faction, members]) => {
              const style = getFactionStyle(faction);
              const pct = (members.length / totalMembers) * 100;
              return (
                <div
                  key={faction}
                  className={`${style.bg} relative group cursor-pointer flex items-center justify-center`}
                  style={{ width: `${pct}%`, minWidth: members.length > 0 ? "24px" : 0 }}
                  onClick={() => toggleFaction(faction)}
                >
                  <span className="text-white text-xs font-bold drop-shadow-sm">
                    {members.length}
                  </span>
                  <div className="absolute -top-8 left-1/2 -translate-x-1/2 hidden group-hover:block bg-gray-900 text-white text-xs px-2 py-1 rounded whitespace-nowrap z-10">
                    {faction}: {members.length} Sitze
                  </div>
                </div>
              );
            })}
          </div>

          {/* Faction legend + drilldown */}
          <div className="space-y-2">
            {sortedFactions.map(([faction, members]) => {
              const style = getFactionStyle(faction);
              const isExpanded = expandedFaction === faction;
              return (
                <div key={faction}>
                  <button
                    onClick={() => toggleFaction(faction)}
                    className={`w-full flex items-center justify-between p-2.5 rounded-lg transition-colors ${
                      isExpanded ? style.light : "hover:bg-gray-50 dark:hover:bg-gray-700/50"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className={`w-3 h-3 rounded-sm ${style.bg}`} />
                      <span className="text-sm font-medium">{faction}</span>
                      <span className="text-xs text-gray-500">
                        {members.length} {members.length === 1 ? "Sitz" : "Sitze"}
                      </span>
                    </div>
                    <svg
                      className={`w-4 h-4 text-gray-400 transition-transform ${isExpanded ? "rotate-180" : ""}`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>

                  {isExpanded && (
                    <div className={`mt-1 ml-5 rounded-lg ${style.light} p-2`}>
                      <div className="space-y-1">
                        {members.map((m) => (
                          <Link
                            key={m.person_number}
                            to={`/parliamentarian/${m.person_number}`}
                            className="flex items-center gap-2 p-1.5 rounded hover:bg-white/50 dark:hover:bg-gray-700/50 transition-colors"
                          >
                            {m.photo_url && (
                              <img
                                src={m.photo_url}
                                alt=""
                                className="w-7 h-7 rounded-full object-cover bg-gray-200 flex-shrink-0"
                                onError={(e) => { e.target.style.display = "none"; }}
                              />
                            )}
                            <div className="min-w-0 flex-1">
                              <span className="text-sm font-medium">
                                {m.first_name} {m.last_name}
                              </span>
                              <span className="text-xs text-gray-500 ml-2">
                                {m.party_abbreviation}
                                {m.canton_abbreviation ? ` / ${m.canton_abbreviation}` : ""}
                              </span>
                            </div>
                            {m.function && (
                              <span className="text-xs text-swiss-red font-medium flex-shrink-0">
                                {m.function}
                              </span>
                            )}
                          </Link>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
