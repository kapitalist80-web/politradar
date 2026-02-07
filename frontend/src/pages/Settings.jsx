import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import {
  getEmailSettings,
  updateEmailSettings,
  triggerSyncParliamentarians,
  triggerSyncCommittees,
  triggerSyncVotingData,
  triggerSyncAll,
} from "../api/client";

const ALERT_TYPE_OPTIONS = [
  { value: "status_change", label: "Statusaenderungen" },
  { value: "committee_scheduled", label: "Kommissionstermine" },
  { value: "debate_scheduled", label: "Ratsdebatte traktandiert" },
  { value: "new_document", label: "Neue Dokumente" },
  { value: "vote_result", label: "Abstimmungsergebnisse" },
];

export default function Settings() {
  const { user } = useAuth();
  const [dark, setDark] = useState(
    document.documentElement.classList.contains("dark"),
  );
  const [emailEnabled, setEmailEnabled] = useState(false);
  const [emailTypes, setEmailTypes] = useState([]);
  const [emailLoading, setEmailLoading] = useState(true);
  const [emailSaving, setEmailSaving] = useState(false);
  const [emailSaved, setEmailSaved] = useState(false);
  const [syncStatus, setSyncStatus] = useState({});

  useEffect(() => {
    getEmailSettings()
      .then((data) => {
        setEmailEnabled(data.email_alerts_enabled);
        setEmailTypes(data.email_alert_types || []);
      })
      .catch(() => {})
      .finally(() => setEmailLoading(false));
  }, []);

  const toggleDark = () => {
    document.documentElement.classList.toggle("dark");
    setDark(!dark);
  };

  const handleToggleEmail = async () => {
    const newEnabled = !emailEnabled;
    setEmailEnabled(newEnabled);
    await saveEmailSettings(newEnabled, emailTypes);
  };

  const handleToggleType = async (type) => {
    const newTypes = emailTypes.includes(type)
      ? emailTypes.filter((t) => t !== type)
      : [...emailTypes, type];
    setEmailTypes(newTypes);
    await saveEmailSettings(emailEnabled, newTypes);
  };

  const saveEmailSettings = async (enabled, types) => {
    setEmailSaving(true);
    setEmailSaved(false);
    try {
      const result = await updateEmailSettings({
        email_alerts_enabled: enabled,
        email_alert_types: types,
      });
      setEmailEnabled(result.email_alerts_enabled);
      setEmailTypes(result.email_alert_types);
      setEmailSaved(true);
      setTimeout(() => setEmailSaved(false), 2000);
    } catch {
      /* ignore */
    } finally {
      setEmailSaving(false);
    }
  };

  const handleSync = async (name, fn) => {
    setSyncStatus((prev) => ({ ...prev, [name]: "running" }));
    try {
      await fn();
      setSyncStatus((prev) => ({ ...prev, [name]: "done" }));
      setTimeout(() => setSyncStatus((prev) => ({ ...prev, [name]: null })), 5000);
    } catch {
      setSyncStatus((prev) => ({ ...prev, [name]: "error" }));
      setTimeout(() => setSyncStatus((prev) => ({ ...prev, [name]: null })), 5000);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Einstellungen</h1>

      {/* Profile */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <h2 className="font-semibold mb-4">Profil</h2>
        <div className="space-y-3">
          <div>
            <label className="block text-sm text-gray-500 mb-1">Name</label>
            <p className="font-medium">{user?.name}</p>
          </div>
          <div>
            <label className="block text-sm text-gray-500 mb-1">E-Mail</label>
            <p className="font-medium">{user?.email}</p>
          </div>
        </div>
      </div>

      {/* Appearance */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <h2 className="font-semibold mb-4">Darstellung</h2>
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium">Dark Mode</p>
            <p className="text-sm text-gray-500">
              Dunkles Farbschema verwenden
            </p>
          </div>
          <button
            onClick={toggleDark}
            className={`relative w-12 h-6 rounded-full transition-colors ${
              dark ? "bg-swiss-red" : "bg-gray-300"
            }`}
          >
            <span
              className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform ${
                dark ? "translate-x-6" : ""
              }`}
            />
          </button>
        </div>
      </div>

      {/* Email Notifications */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold">E-Mail-Benachrichtigungen</h2>
          {emailSaved && (
            <span className="text-xs text-green-600 dark:text-green-400">
              Gespeichert
            </span>
          )}
          {emailSaving && (
            <div className="animate-spin h-4 w-4 border-2 border-swiss-red border-t-transparent rounded-full" />
          )}
        </div>

        {emailLoading ? (
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <div className="animate-spin h-4 w-4 border-2 border-gray-400 border-t-transparent rounded-full" />
            Laden...
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">E-Mail-Alerts aktivieren</p>
                <p className="text-sm text-gray-500">
                  Bei neuen Alerts eine zusammengefasste E-Mail erhalten
                </p>
              </div>
              <button
                onClick={handleToggleEmail}
                className={`relative w-12 h-6 rounded-full transition-colors ${
                  emailEnabled ? "bg-swiss-red" : "bg-gray-300"
                }`}
              >
                <span
                  className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform ${
                    emailEnabled ? "translate-x-6" : ""
                  }`}
                />
              </button>
            </div>

            {emailEnabled && (
              <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  Alert-Typen fuer E-Mail-Benachrichtigungen:
                </p>
                <div className="space-y-2">
                  {ALERT_TYPE_OPTIONS.map((opt) => (
                    <label
                      key={opt.value}
                      className="flex items-center gap-3 cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={emailTypes.includes(opt.value)}
                        onChange={() => handleToggleType(opt.value)}
                        className="w-4 h-4 rounded border-gray-300 text-swiss-red focus:ring-swiss-red"
                      />
                      <span className="text-sm">{opt.label}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            <p className="text-xs text-gray-400 mt-2">
              E-Mails werden an {user?.email} gesendet, wenn neue Alerts
              durch die automatische Synchronisation erkannt werden.
            </p>
          </div>
        )}
      </div>

      {/* Data Sync */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mt-6">
        <h2 className="font-semibold mb-4">Datensynchronisation</h2>
        <p className="text-sm text-gray-500 mb-4">
          Parlamentsdaten werden automatisch synchronisiert (Parlamentarier &amp; Kommissionen monatlich, Abstimmungen woechentlich).
          Hier kannst du die Synchronisation manuell ausloesen.
        </p>
        <div className="space-y-3">
          <SyncButton
            label="Alle synchronisieren"
            description="Parlamentarier, Kommissionen und Abstimmungsdaten"
            status={syncStatus.all}
            onClick={() => handleSync("all", triggerSyncAll)}
          />
          <SyncButton
            label="Parlamentarier"
            description="Ratsmitglieder, Parteien, Fraktionen, Kantone"
            status={syncStatus.parliamentarians}
            onClick={() => handleSync("parliamentarians", triggerSyncParliamentarians)}
          />
          <SyncButton
            label="Kommissionen"
            description="Kommissionen und Mitgliedschaften"
            status={syncStatus.committees}
            onClick={() => handleSync("committees", triggerSyncCommittees)}
          />
          <SyncButton
            label="Abstimmungsdaten"
            description="Abstimmungen und individuelle Stimmabgaben (kann mehrere Minuten dauern)"
            status={syncStatus.votingData}
            onClick={() => handleSync("votingData", triggerSyncVotingData)}
          />
        </div>
      </div>
    </div>
  );
}

function SyncButton({ label, description, status, onClick }) {
  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
      <div>
        <p className="font-medium text-sm">{label}</p>
        <p className="text-xs text-gray-500">{description}</p>
      </div>
      <div className="flex items-center gap-2">
        {status === "done" && (
          <span className="text-xs text-green-600 dark:text-green-400">Gestartet</span>
        )}
        {status === "error" && (
          <span className="text-xs text-red-600 dark:text-red-400">Fehler</span>
        )}
        <button
          onClick={onClick}
          disabled={status === "running"}
          className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
            status === "running"
              ? "bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed"
              : "bg-swiss-red text-white hover:bg-swiss-dark"
          }`}
        >
          {status === "running" ? (
            <span className="flex items-center gap-1.5">
              <span className="animate-spin h-3 w-3 border-2 border-white border-t-transparent rounded-full" />
              Laeuft...
            </span>
          ) : (
            "Starten"
          )}
        </button>
      </div>
    </div>
  );
}
