import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getParliamentarians, getParlGroups } from "../api/client";

const COUNCIL_OPTIONS = [
  { value: "", label: "Alle Räte" },
  { value: "1", label: "Nationalrat" },
  { value: "2", label: "Ständerat" },
];

export default function Parliamentarians() {
  const [members, setMembers] = useState([]);
  const [parlGroups, setParlGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [councilId, setCouncilId] = useState("");
  const [parlGroup, setParlGroup] = useState("");
  const [canton, setCanton] = useState("");

  useEffect(() => {
    getParlGroups().then(setParlGroups).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    const params = {};
    if (councilId) params.council_id = councilId;
    if (parlGroup) params.parl_group = parlGroup;
    if (canton) params.canton = canton;
    if (search) params.search = search;

    getParliamentarians(params)
      .then(setMembers)
      .catch(() => setMembers([]))
      .finally(() => setLoading(false));
  }, [councilId, parlGroup, canton, search]);

  // Extract unique cantons from data
  const cantons = [...new Set(members.map((m) => m.canton_abbreviation).filter(Boolean))].sort();

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Parlamentarier</h1>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Name suchen..."
          className="px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm focus:ring-swiss-red focus:border-swiss-red"
        />
        <select
          value={councilId}
          onChange={(e) => setCouncilId(e.target.value)}
          className="px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm"
        >
          {COUNCIL_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <select
          value={parlGroup}
          onChange={(e) => setParlGroup(e.target.value)}
          className="px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm"
        >
          <option value="">Alle Fraktionen</option>
          {parlGroups.map((pg) => (
            <option key={pg.parl_group_number} value={pg.parl_group_abbreviation}>
              {pg.parl_group_abbreviation} - {pg.parl_group_name}
            </option>
          ))}
        </select>
        {cantons.length > 0 && (
          <select
            value={canton}
            onChange={(e) => setCanton(e.target.value)}
            className="px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm"
          >
            <option value="">Alle Kantone</option>
            {cantons.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        )}
      </div>

      {/* Count */}
      <p className="text-sm text-gray-500 mb-4">
        {loading ? "Laden..." : `${members.length} Mitglieder`}
      </p>

      {loading ? (
        <div className="flex justify-center py-10">
          <div className="animate-spin h-8 w-8 border-4 border-swiss-red border-t-transparent rounded-full" />
        </div>
      ) : members.length === 0 ? (
        <p className="text-gray-500">
          Keine Parlamentarier gefunden. Daten müssen erst synchronisiert werden.
        </p>
      ) : (
        <>
          {/* Desktop table */}
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left py-2 pr-3">Name</th>
                  <th className="text-left py-2 pr-3">Partei</th>
                  <th className="text-left py-2 pr-3">Fraktion</th>
                  <th className="text-left py-2 pr-3">Kanton</th>
                  <th className="text-left py-2">Rat</th>
                </tr>
              </thead>
              <tbody>
                {members.map((m) => (
                  <tr
                    key={m.person_number}
                    className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50"
                  >
                    <td className="py-2 pr-3">
                      <Link
                        to={`/parliamentarian/${m.person_number}`}
                        className="flex items-center gap-2 text-swiss-red hover:underline"
                      >
                        {m.photo_url && (
                          <img
                            src={m.photo_url}
                            alt=""
                            className="w-7 h-7 rounded-full object-cover bg-gray-200"
                            onError={(e) => { e.target.style.display = "none"; }}
                          />
                        )}
                        {m.first_name} {m.last_name}
                      </Link>
                    </td>
                    <td className="py-2 pr-3">{m.party_abbreviation}</td>
                    <td className="py-2 pr-3">{m.parl_group_abbreviation}</td>
                    <td className="py-2 pr-3">{m.canton_abbreviation}</td>
                    <td className="py-2">{m.council_name}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile cards */}
          <div className="md:hidden space-y-2">
            {members.map((m) => (
              <Link
                key={m.person_number}
                to={`/parliamentarian/${m.person_number}`}
                className="block bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-3"
              >
                <div className="flex items-center gap-3">
                  {m.photo_url && (
                    <img
                      src={m.photo_url}
                      alt=""
                      className="w-10 h-10 rounded-full object-cover bg-gray-200"
                      onError={(e) => { e.target.style.display = "none"; }}
                    />
                  )}
                  <div>
                    <div className="font-medium text-sm">
                      {m.first_name} {m.last_name}
                    </div>
                    <div className="text-xs text-gray-500">
                      {m.party_abbreviation} | {m.canton_abbreviation} | {m.council_name}
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
