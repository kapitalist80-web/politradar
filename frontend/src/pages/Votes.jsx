import { useEffect, useState } from "react";
import { getRecentVotes, getVoteDetail } from "../api/client";

const COUNCIL_OPTIONS = [
  { value: "", label: "Alle Raete" },
  { value: "1", label: "Nationalrat" },
  { value: "2", label: "Staenderat" },
];

export default function Votes() {
  const [votes, setVotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [councilId, setCouncilId] = useState("");
  const [selectedVote, setSelectedVote] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    const params = {};
    if (councilId) params.council_id = councilId;
    getRecentVotes(params)
      .then(setVotes)
      .catch(() => setVotes([]))
      .finally(() => setLoading(false));
  }, [councilId]);

  const handleVoteClick = async (voteId) => {
    if (selectedVote?.vote_id === voteId) {
      setSelectedVote(null);
      return;
    }
    setDetailLoading(true);
    try {
      const detail = await getVoteDetail(voteId);
      setSelectedVote(detail);
    } catch {
      setSelectedVote(null);
    } finally {
      setDetailLoading(false);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Abstimmungen</h1>

      <div className="flex gap-3 mb-6">
        <select
          value={councilId}
          onChange={(e) => setCouncilId(e.target.value)}
          className="px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm"
        >
          {COUNCIL_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="flex justify-center py-10">
          <div className="animate-spin h-8 w-8 border-4 border-swiss-red border-t-transparent rounded-full" />
        </div>
      ) : votes.length === 0 ? (
        <p className="text-gray-500">
          Keine Abstimmungsdaten vorhanden. Daten muessen erst synchronisiert werden.
        </p>
      ) : (
        <div className="space-y-3">
          {votes.map((v) => (
            <div key={v.vote_id}>
              <button
                onClick={() => handleVoteClick(v.vote_id)}
                className="w-full text-left bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      {v.business_number && (
                        <span className="font-mono text-xs text-gray-500">
                          {v.business_number}
                        </span>
                      )}
                      {v.vote_date && (
                        <span className="text-xs text-gray-400">
                          {new Date(v.vote_date).toLocaleDateString("de-CH")}
                        </span>
                      )}
                    </div>
                    <p className="text-sm font-medium truncate">
                      {v.subject || v.business_title || "Abstimmung"}
                    </p>
                  </div>
                  <div className="flex-shrink-0 flex items-center gap-2">
                    {v.result && (
                      <span
                        className={`text-xs font-medium px-2 py-0.5 rounded ${
                          v.result.toLowerCase().includes("angenommen")
                            ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                            : "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
                        }`}
                      >
                        {v.result}
                      </span>
                    )}
                    <VoteResultBar yes={v.total_yes} no={v.total_no} abstain={v.total_abstain} />
                  </div>
                </div>
              </button>

              {/* Detail view */}
              {selectedVote?.vote_id === v.vote_id && (
                <div className="bg-gray-50 dark:bg-gray-900 rounded-b-lg border-x border-b border-gray-200 dark:border-gray-700 p-4">
                  {detailLoading ? (
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <div className="animate-spin h-4 w-4 border-2 border-swiss-red border-t-transparent rounded-full" />
                      Details werden geladen...
                    </div>
                  ) : (
                    <div>
                      {selectedVote.meaning_yes && (
                        <div className="mb-2 text-sm">
                          <span className="text-green-600 font-medium">Ja:</span>{" "}
                          <span className="text-gray-600 dark:text-gray-400">{selectedVote.meaning_yes}</span>
                        </div>
                      )}
                      {selectedVote.meaning_no && (
                        <div className="mb-3 text-sm">
                          <span className="text-red-600 font-medium">Nein:</span>{" "}
                          <span className="text-gray-600 dark:text-gray-400">{selectedVote.meaning_no}</span>
                        </div>
                      )}

                      {/* Voting breakdown by faction */}
                      {selectedVote.votings && selectedVote.votings.length > 0 && (
                        <div>
                          <h3 className="text-sm font-medium mb-2">
                            Stimmverhalten ({selectedVote.votings.length} Stimmen)
                          </h3>
                          <FactionVotingBreakdown votings={selectedVote.votings} />
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function VoteResultBar({ yes, no, abstain }) {
  const total = (yes || 0) + (no || 0) + (abstain || 0);
  if (total === 0) return null;

  return (
    <div className="flex items-center gap-1 text-xs">
      <span className="text-green-600">{yes}</span>
      <div className="flex h-3 w-16 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700">
        <div className="bg-green-500" style={{ width: `${(yes / total) * 100}%` }} />
        <div className="bg-red-500" style={{ width: `${(no / total) * 100}%` }} />
        {abstain > 0 && (
          <div className="bg-yellow-400" style={{ width: `${(abstain / total) * 100}%` }} />
        )}
      </div>
      <span className="text-red-600">{no}</span>
    </div>
  );
}

function FactionVotingBreakdown({ votings }) {
  // Group by faction
  const factions = {};
  for (const v of votings) {
    const key = v.parl_group_abbreviation || "Andere";
    if (!factions[key]) {
      factions[key] = { yes: 0, no: 0, abstention: 0, absent: 0 };
    }
    if (v.decision === "Yes") factions[key].yes++;
    else if (v.decision === "No") factions[key].no++;
    else if (v.decision === "Abstention") factions[key].abstention++;
    else factions[key].absent++;
  }

  return (
    <div className="space-y-1">
      {Object.entries(factions)
        .sort((a, b) => {
          const totalA = a[1].yes + a[1].no + a[1].abstention;
          const totalB = b[1].yes + b[1].no + b[1].abstention;
          return totalB - totalA;
        })
        .map(([faction, counts]) => {
          const total = counts.yes + counts.no + counts.abstention;
          if (total === 0) return null;
          return (
            <div key={faction} className="flex items-center gap-2 text-xs">
              <span className="w-10 text-right font-medium">{faction}</span>
              <div className="flex h-3 flex-1 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700">
                <div className="bg-green-500" style={{ width: `${(counts.yes / total) * 100}%` }} />
                <div className="bg-red-500" style={{ width: `${(counts.no / total) * 100}%` }} />
                {counts.abstention > 0 && (
                  <div className="bg-yellow-400" style={{ width: `${(counts.abstention / total) * 100}%` }} />
                )}
              </div>
              <span className="w-20 text-gray-500">
                {counts.yes}J {counts.no}N {counts.abstention > 0 ? `${counts.abstention}E` : ""}
              </span>
            </div>
          );
        })}
    </div>
  );
}
