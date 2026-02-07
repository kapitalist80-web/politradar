import ParliamentarianCard from "./ParliamentarianCard";

export default function CommitteePanel({ treatingBody, loading }) {
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

  // Group members by faction
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

      {treatingBody.members && treatingBody.members.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Mitglieder ({treatingBody.members.length})
          </h3>

          {/* Faction summary */}
          <div className="flex flex-wrap gap-2 mb-4">
            {Object.entries(factionGroups)
              .sort((a, b) => b[1].length - a[1].length)
              .map(([faction, members]) => (
                <span
                  key={faction}
                  className="text-xs px-2 py-1 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                >
                  {faction}: {members.length}
                </span>
              ))}
          </div>

          {/* Member list */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {treatingBody.members.map((m) => (
              <ParliamentarianCard
                key={m.person_number}
                member={m}
                showFunction={true}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
