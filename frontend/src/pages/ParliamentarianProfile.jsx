import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  getParliamentarian,
  getParliamentarianStats,
  getParliamentarianVotes,
} from "../api/client";
import LoyaltyBadge from "../components/LoyaltyBadge";
import VotingHistoryTable from "../components/VotingHistoryTable";

export default function ParliamentarianProfile() {
  const { personNumber } = useParams();
  const [parl, setParl] = useState(null);
  const [stats, setStats] = useState(null);
  const [votes, setVotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [votesLoading, setVotesLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getParliamentarian(personNumber),
      getParliamentarianStats(personNumber).catch(() => null),
    ])
      .then(([parlData, statsData]) => {
        setParl(parlData);
        setStats(statsData);
      })
      .catch(() => setParl(null))
      .finally(() => setLoading(false));

    getParliamentarianVotes(personNumber)
      .then(setVotes)
      .catch(() => setVotes([]))
      .finally(() => setVotesLoading(false));
  }, [personNumber]);

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="animate-spin h-8 w-8 border-4 border-swiss-red border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!parl) {
    return (
      <div className="text-center py-10">
        <p className="text-gray-500">Parlamentarier nicht gefunden</p>
        <Link to="/parliamentarians" className="text-swiss-red hover:underline text-sm mt-2 inline-block">
          Zurueck zur Uebersicht
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-start gap-4 mb-6">
        {parl.photo_url && (
          <img
            src={parl.photo_url}
            alt={`${parl.first_name} ${parl.last_name}`}
            className="w-20 h-20 rounded-full object-cover bg-gray-200 flex-shrink-0"
            onError={(e) => { e.target.style.display = "none"; }}
          />
        )}
        <div>
          <h1 className="text-2xl font-bold">
            {parl.first_name} {parl.last_name}
          </h1>
          <div className="flex flex-wrap gap-3 mt-1 text-sm text-gray-500">
            {parl.party_name && (
              <span>{parl.party_name} ({parl.party_abbreviation})</span>
            )}
            {parl.parl_group_name && parl.parl_group_name !== parl.party_name && (
              <span>Fraktion: {parl.parl_group_abbreviation}</span>
            )}
            {parl.canton_name && (
              <span>{parl.canton_name} ({parl.canton_abbreviation})</span>
            )}
            {parl.council_name && <span>{parl.council_name}</span>}
          </div>
          <div className="flex flex-wrap gap-2 mt-2">
            {!parl.active && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400">
                Nicht mehr im Amt
              </span>
            )}
            {stats && <LoyaltyBadge score={stats.party_loyalty_score} />}
          </div>
          {parl.biografie_url && (
            <a
              href={parl.biografie_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-swiss-red hover:underline mt-2 inline-block"
            >
              Profil auf parlament.ch &rarr;
            </a>
          )}
        </div>
      </div>

      {/* Stats */}
      {stats && stats.total_votes > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
          <h2 className="font-semibold mb-4">Abstimmungsstatistik</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <StatBox label="Abstimmungen" value={stats.total_votes} />
            <StatBox
              label="Ja-Rate"
              value={`${Math.round(stats.yes_rate * 100)}%`}
              color="text-green-600"
            />
            <StatBox
              label="Nein-Rate"
              value={`${Math.round(stats.no_rate * 100)}%`}
              color="text-red-600"
            />
            <StatBox
              label="Abwesenheit"
              value={`${Math.round(stats.absence_rate * 100)}%`}
              color="text-gray-500"
            />
          </div>

          {/* Simple bar chart for voting behavior */}
          <div className="mt-4">
            <div className="flex h-6 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700">
              <div
                className="bg-green-500"
                style={{ width: `${stats.yes_rate * 100}%` }}
                title={`Ja: ${Math.round(stats.yes_rate * 100)}%`}
              />
              <div
                className="bg-red-500"
                style={{ width: `${stats.no_rate * 100}%` }}
                title={`Nein: ${Math.round(stats.no_rate * 100)}%`}
              />
              <div
                className="bg-yellow-400"
                style={{ width: `${stats.abstention_rate * 100}%` }}
                title={`Enthaltung: ${Math.round(stats.abstention_rate * 100)}%`}
              />
              <div
                className="bg-gray-400"
                style={{ width: `${stats.absence_rate * 100}%` }}
                title={`Abwesend: ${Math.round(stats.absence_rate * 100)}%`}
              />
            </div>
            <div className="flex gap-4 mt-2 text-xs text-gray-500">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-green-500" /> Ja
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-red-500" /> Nein
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-yellow-400" /> Enthaltung
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-gray-400" /> Abwesend
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Voting history */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <h2 className="font-semibold mb-4">Letzte Abstimmungen</h2>
        <VotingHistoryTable votes={votes} loading={votesLoading} />
      </div>

      <Link
        to="/parliamentarians"
        className="text-sm text-gray-500 hover:text-swiss-red"
      >
        &larr; Zurueck zur Uebersicht
      </Link>
    </div>
  );
}

function StatBox({ label, value, color = "" }) {
  return (
    <div className="text-center">
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      <div className="text-xs text-gray-500 mt-1">{label}</div>
    </div>
  );
}
