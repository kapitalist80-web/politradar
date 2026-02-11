import { useEffect, useState, useCallback } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { addBusinessNote, deleteBusiness, getBusiness, getBusinessNotes, getBusinessSchedule, getTreatingBody, updateBusinessPriority } from "../api/client";
import StatusBadge from "../components/StatusBadge";
import CommitteePanel from "../components/CommitteePanel";

function HtmlContent({ html, className = "" }) {
  if (!html) return null;
  return (
    <div
      className={className}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

const EVENT_TYPE_LABELS = {
  status_change: "Status",
  committee_scheduled: "Kommission",
  debate_scheduled: "Traktandiert",
  new_document: "Dokument",
  vote_result: "Abstimmung",
};

export default function BusinessDetail() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [schedule, setSchedule] = useState(null);
  const [scheduleLoading, setScheduleLoading] = useState(true);
  const [treatingBody, setTreatingBody] = useState(null);
  const [treatingBodyLoading, setTreatingBodyLoading] = useState(true);
  const [loading, setLoading] = useState(true);
  const [notes, setNotes] = useState([]);
  const [notesLoading, setNotesLoading] = useState(true);
  const [newNote, setNewNote] = useState("");
  const [noteSubmitting, setNoteSubmitting] = useState(false);
  const navigate = useNavigate();

  const loadData = useCallback(() => {
    return getBusiness(id)
      .then(setData)
      .catch(() => navigate("/"));
  }, [id, navigate]);

  useEffect(() => {
    loadData().finally(() => setLoading(false));
    getBusinessSchedule(id)
      .then(setSchedule)
      .catch(() => setSchedule(null))
      .finally(() => setScheduleLoading(false));
    getTreatingBody(id)
      .then(setTreatingBody)
      .catch(() => setTreatingBody(null))
      .finally(() => setTreatingBodyLoading(false));
    getBusinessNotes(id)
      .then(setNotes)
      .catch(() => setNotes([]))
      .finally(() => setNotesLoading(false));
  }, [loadData, id]);

  // Re-fetch once after delay to pick up background-synced data
  useEffect(() => {
    if (!data) return;
    const needsBackfill = !data.business?.author || !data.business?.status;
    if (!needsBackfill) return;
    const timer = setTimeout(() => loadData(), 5000);
    return () => clearTimeout(timer);
  }, [loading]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleDelete = async () => {
    if (!confirm("Tracking beenden?")) return;
    await deleteBusiness(id);
    navigate("/");
  };

  const handlePriorityChange = async (value) => {
    const priority = value ? parseInt(value) : null;
    await updateBusinessPriority(id, priority);
    loadData();
  };

  const handleAddNote = async () => {
    if (!newNote.trim()) return;
    setNoteSubmitting(true);
    try {
      const note = await addBusinessNote(id, newNote.trim());
      setNotes((prev) => [note, ...prev]);
      setNewNote("");
    } catch {
      /* ignore */
    } finally {
      setNoteSubmitting(false);
    }
  };

  if (loading || !data) {
    return (
      <div className="flex justify-center py-20">
        <div className="animate-spin h-8 w-8 border-4 border-swiss-red border-t-transparent rounded-full" />
      </div>
    );
  }

  const { business, events } = data;

  const affairId = "20" + business.business_number.replace(".", "");
  const parlamentUrl = `https://www.parlament.ch/de/ratsbetrieb/suche-curia-vista/geschaeft?AffairId=${affairId}`;

  const hasPreconsultations = schedule?.preconsultations?.length > 0;
  const hasSessions = schedule?.sessions?.length > 0;
  const hasSchedule = hasPreconsultations || hasSessions;

  return (
    <div className="max-w-3xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <span className="font-mono text-gray-500">
            {business.business_number}
          </span>
          <StatusBadge status={business.status} />
          <select
            value={business.priority || ""}
            onChange={(e) => handlePriorityChange(e.target.value)}
            className="text-xs border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-700"
          >
            <option value="">Priorität</option>
            <option value="1">1 (Hoch)</option>
            <option value="2">2 (Mittel)</option>
            <option value="3">3 (Niedrig)</option>
          </select>
        </div>
        <h1 className="text-2xl font-bold mb-2">
          {business.title || "Ohne Titel"}
        </h1>
        <HtmlContent
          html={business.description}
          className="text-gray-600 dark:text-gray-400 prose prose-sm dark:prose-invert max-w-none"
        />
        <div className="flex flex-wrap gap-4 mt-3 text-sm text-gray-500">
          {business.business_type && <span>{business.business_type}</span>}
          {business.author && (
            <span>
              Urheber: {business.author}
              {business.author_faction && (
                <span className="ml-1 text-gray-400">({business.author_faction})</span>
              )}
            </span>
          )}
          {business.first_council && (
            <span>Erstbehandelnder Rat: {business.first_council}</span>
          )}
          {business.submission_date && (
            <span>
              Eingereicht:{" "}
              {new Date(business.submission_date).toLocaleDateString("de-CH")}
            </span>
          )}
          {business.last_api_sync && (
            <span>
              Letzter Sync:{" "}
              {new Date(business.last_api_sync).toLocaleString("de-CH")}
            </span>
          )}
        </div>
        {business.federal_council_proposal && (
          <div className="mt-3">
            <span className={`inline-flex items-center text-sm font-medium px-3 py-1 rounded-full ${
              business.federal_council_proposal.toLowerCase().includes("annahme")
                ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                : business.federal_council_proposal.toLowerCase().includes("ablehnung")
                  ? "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
                  : "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200"
            }`}>
              Antrag Bundesrat: {business.federal_council_proposal}
            </span>
          </div>
        )}
        <div className="mt-3">
          <a
            href={parlamentUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-swiss-red hover:underline"
          >
            Geschäft auf parlament.ch ansehen &rarr;
          </a>
        </div>
      </div>

      {/* Kommissions- und Sessionstermine */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <h2 className="font-semibold mb-4">Terminplanung</h2>
        {scheduleLoading ? (
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <div className="animate-spin h-4 w-4 border-2 border-swiss-red border-t-transparent rounded-full" />
            Termine werden geladen...
          </div>
        ) : !hasSchedule ? (
          <p className="text-sm text-gray-500">Keine Termine bekannt</p>
        ) : (
          <div className="space-y-4">
            {hasPreconsultations && (
              <div>
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Vorberatung in Kommissionen</h3>
                <div className="space-y-2">
                  {schedule.preconsultations.map((p, i) => (
                    <div key={i} className="flex items-start gap-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                      <div className="flex-shrink-0 mt-0.5">
                        <div className="w-2.5 h-2.5 rounded-full bg-blue-500" />
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-sm font-medium">{p.committee_name}</span>
                          {p.committee_abbrev && (
                            <span className="text-xs px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-800 text-blue-700 dark:text-blue-200">
                              {p.committee_abbrev}
                            </span>
                          )}
                        </div>
                        <div className="flex gap-3 mt-1 text-xs text-gray-500">
                          {p.date && (
                            <span>{new Date(p.date).toLocaleDateString("de-CH")}</span>
                          )}
                          {p.treatment_category && (
                            <span>Kategorie: {p.treatment_category}</span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {hasSessions && (
              <div>
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Ratssitzungen (traktandiert)</h3>
                <div className="space-y-2">
                  {schedule.sessions.map((s, i) => (
                    <div key={i} className="flex items-start gap-3 p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg">
                      <div className="flex-shrink-0 mt-0.5">
                        <div className="w-2.5 h-2.5 rounded-full bg-amber-500" />
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-sm font-medium">{s.council}</span>
                          {s.council_abbrev && (
                            <span className="text-xs px-1.5 py-0.5 rounded bg-amber-100 dark:bg-amber-800 text-amber-700 dark:text-amber-200">
                              {s.council_abbrev}
                            </span>
                          )}
                          {s.session_name && (
                            <span className="text-xs text-gray-500">{s.session_name}</span>
                          )}
                        </div>
                        <div className="flex gap-3 mt-1 text-xs text-gray-500">
                          {s.meeting_date && (
                            <span>{new Date(s.meeting_date).toLocaleDateString("de-CH")}</span>
                          )}
                          {s.begin && <span>Beginn: {s.begin}</span>}
                          {s.meeting_order && <span>{s.meeting_order}</span>}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Behandelndes Gremium */}
      <CommitteePanel treatingBody={treatingBody} loading={treatingBodyLoading} />

      {/* Motionstext */}
      {business.submitted_text && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
          <h2 className="font-semibold mb-3">Motionstext</h2>
          <HtmlContent
            html={business.submitted_text}
            className="text-sm text-gray-700 dark:text-gray-300 prose prose-sm dark:prose-invert max-w-none"
          />
        </div>
      )}

      {/* Notizen */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <h2 className="font-semibold mb-4">Notizen</h2>
        <div className="mb-4">
          <textarea
            value={newNote}
            onChange={(e) => setNewNote(e.target.value)}
            placeholder="Neue Notiz hinzufügen..."
            rows={3}
            className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 resize-none focus:outline-none focus:ring-2 focus:ring-swiss-red"
          />
          <button
            onClick={handleAddNote}
            disabled={noteSubmitting || !newNote.trim()}
            className="mt-2 bg-swiss-red text-white px-4 py-1.5 rounded-md text-sm font-medium hover:bg-swiss-dark transition-colors disabled:opacity-50"
          >
            {noteSubmitting ? "Speichern..." : "Speichern"}
          </button>
        </div>
        {notesLoading ? (
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <div className="animate-spin h-4 w-4 border-2 border-swiss-red border-t-transparent rounded-full" />
            Notizen werden geladen...
          </div>
        ) : notes.length > 0 ? (
          <div className="space-y-3">
            {notes.map((note) => (
              <div
                key={note.id}
                className="border-l-4 border-swiss-red pl-4 py-2"
              >
                <div className="flex items-center gap-2 text-xs text-gray-500 mb-1">
                  <span className="font-medium">{note.user_name || "Unbekannt"}</span>
                  <span>&middot;</span>
                  <time>{new Date(note.created_at).toLocaleString("de-CH")}</time>
                </div>
                <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                  {note.content}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500">Noch keine Notizen</p>
        )}
      </div>

      {/* Begruendung */}
      {business.reasoning && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
          <h2 className="font-semibold mb-3">Begr&uuml;ndung</h2>
          <HtmlContent
            html={business.reasoning}
            className="text-sm text-gray-700 dark:text-gray-300 prose prose-sm dark:prose-invert max-w-none"
          />
        </div>
      )}

      {/* Stellungnahme des Bundesrates */}
      {business.federal_council_response && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
          <h2 className="font-semibold mb-3">Stellungnahme des Bundesrates</h2>
          <HtmlContent
            html={business.federal_council_response}
            className="text-sm text-gray-700 dark:text-gray-300 prose prose-sm dark:prose-invert max-w-none"
          />
        </div>
      )}

      {/* Timeline */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <h2 className="font-semibold mb-4">Eventverlauf</h2>
        {events.length === 0 ? (
          <p className="text-sm text-gray-500">Noch keine Events</p>
        ) : (
          <div className="space-y-4">
            {events.map((evt) => (
              <div key={evt.id} className="flex gap-4">
                <div className="flex flex-col items-center">
                  <div className={`w-3 h-3 rounded-full ${
                    evt.event_type === "committee_scheduled" ? "bg-blue-500" :
                    evt.event_type === "debate_scheduled" ? "bg-amber-500" :
                    "bg-swiss-red"
                  }`} />
                  <div className="w-px flex-1 bg-gray-200 dark:bg-gray-700" />
                </div>
                <div className="pb-4">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                      evt.event_type === "committee_scheduled"
                        ? "bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300"
                        : evt.event_type === "debate_scheduled"
                          ? "bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300"
                          : "bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300"
                    }`}>
                      {EVENT_TYPE_LABELS[evt.event_type] || evt.event_type}
                    </span>
                    {evt.event_date && (
                      <time className="text-xs text-gray-400">
                        {new Date(evt.event_date).toLocaleDateString("de-CH")}
                      </time>
                    )}
                  </div>
                  <p className="text-sm">{evt.description}</p>
                  {evt.committee_name && (
                    <p className="text-xs text-gray-500 mt-1">
                      Kommission: {evt.committee_name}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <button
        onClick={handleDelete}
        className="text-sm text-red-500 hover:text-red-700"
      >
        Tracking beenden
      </button>
    </div>
  );
}
