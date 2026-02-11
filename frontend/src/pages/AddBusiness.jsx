import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  addBusiness,
  getRecentBusinesses,
  previewBusiness,
  searchParliament,
} from "../api/client";

export default function AddBusiness() {
  const [number, setNumber] = useState("");
  const [query, setQuery] = useState("");
  const [preview, setPreview] = useState(null);
  const [results, setResults] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [apiLoading, setApiLoading] = useState(false);
  const [cachedBusinesses, setCachedBusinesses] = useState([]);
  const [cacheLoading, setCacheLoading] = useState(true);
  const navigate = useNavigate();

  // Load cached recent businesses on mount
  useEffect(() => {
    getRecentBusinesses()
      .then((data) => setCachedBusinesses(data || []))
      .catch(() => {})
      .finally(() => setCacheLoading(false));
  }, []);

  // Build a map of cached business numbers for fast lookup
  const cachedMap = useMemo(
    () => new Map(cachedBusinesses.map((b) => [b.business_number, b])),
    [cachedBusinesses],
  );

  // Filter cached businesses by query for instant local search
  const localResults = useMemo(() => {
    if (query.length < 2) return [];
    const q = query.toLowerCase();
    return cachedBusinesses
      .filter(
        (b) =>
          b.title.toLowerCase().includes(q) ||
          b.business_number.includes(q),
      )
      .slice(0, 20);
  }, [query, cachedBusinesses]);

  const handlePreview = async () => {
    if (!number.match(/^\d{2}\.\d{3,5}$/)) {
      setError("Format: z.B. 24.3927");
      return;
    }
    setError("");

    // Use cached data if available (instant)
    const cached = cachedMap.get(number);
    if (cached) {
      setPreview({ business_number: cached.business_number, title: cached.title });
      return;
    }

    setLoading(true);
    setApiLoading(true);
    try {
      const data = await previewBusiness(number);
      setPreview(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setApiLoading(false);
    }
  };

  const handleSearch = async () => {
    if (query.length < 2) return;
    setError("");
    setLoading(true);
    setApiLoading(true);
    try {
      const data = await searchParliament(query);
      setResults(data || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setApiLoading(false);
    }
  };

  const [adding, setAdding] = useState(false);

  const handleAdd = async (businessNumber) => {
    if (adding) return;
    setAdding(true);
    setError("");
    try {
      await addBusiness(businessNumber);
      navigate("/");
    } catch (err) {
      setError(err.message);
      setAdding(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Geschäft hinzufügen</h1>

      {error && (
        <div className="text-sm text-red-600 bg-red-50 dark:bg-red-900/20 p-3 rounded mb-4">
          {error}
        </div>
      )}

      {apiLoading && (
        <div className="flex items-center gap-2 text-sm text-gray-500 bg-blue-50 dark:bg-blue-900/20 p-3 rounded mb-4">
          <div className="animate-spin h-4 w-4 border-2 border-swiss-red border-t-transparent rounded-full" />
          Parlament-API wird kontaktiert...
        </div>
      )}

      {/* Direct number input */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <h2 className="font-medium mb-3">Geschäftsnummer eingeben</h2>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="z.B. 24.3927"
            value={number}
            onChange={(e) => setNumber(e.target.value)}
            className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-swiss-red"
          />
          <button
            onClick={handlePreview}
            disabled={loading}
            className="bg-swiss-red text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-swiss-dark disabled:opacity-50"
          >
            Vorschau
          </button>
        </div>
      </div>

      {/* Preview */}
      {preview && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
          <h3 className="font-medium">{preview.title || "Kein Titel"}</h3>
          <p className="text-sm text-gray-500 mt-1">{preview.description}</p>
          <div className="flex gap-4 mt-3 text-xs text-gray-400">
            <span>{preview.business_type}</span>
            <span>{preview.status}</span>
          </div>
          <button
            onClick={() => handleAdd(preview.business_number)}
            disabled={adding}
            className="mt-4 bg-swiss-red text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-swiss-dark disabled:opacity-50"
          >
            {adding ? "Wird hinzugefügt..." : "Verfolgen"}
          </button>
        </div>
      )}

      {/* Search */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="font-medium mb-3">Geschäft suchen</h2>
        <div className="flex gap-2 mb-4">
          <input
            type="text"
            placeholder="Stichwort eingeben..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-swiss-red"
          />
          <button
            onClick={handleSearch}
            disabled={loading}
            className="bg-gray-800 dark:bg-gray-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-700 disabled:opacity-50"
          >
            Suchen
          </button>
        </div>

        {cacheLoading && (
          <div className="flex items-center gap-2 text-sm text-gray-400 py-2">
            <div className="animate-spin h-4 w-4 border-2 border-gray-400 border-t-transparent rounded-full" />
            Geschäfte werden geladen...
          </div>
        )}

        {/* Local cached results (instant) */}
        {localResults.length > 0 && results.length === 0 && (
          <div>
            <p className="text-xs text-gray-400 mb-2">
              Schnellsuche (letzte 12 Monate)
            </p>
            <div className="space-y-3">
              {localResults.map((r) => (
                <div
                  key={r.business_number}
                  className="flex justify-between items-start p-3 rounded-md border border-gray-100 dark:border-gray-700"
                >
                  <div className="min-w-0 flex-1">
                    <div className="text-xs font-mono text-gray-400">
                      {r.business_number}
                    </div>
                    <div className="text-sm font-medium truncate">
                      {r.title}
                    </div>
                  </div>
                  <button
                    onClick={() => handleAdd(r.business_number)}
                    disabled={adding}
                    className="ml-3 text-sm text-swiss-red hover:underline flex-shrink-0 disabled:opacity-50"
                  >
                    {adding ? "..." : "Verfolgen"}
                  </button>
                </div>
              ))}
            </div>
            <p className="text-xs text-gray-400 mt-3">
              Ältere Geschäfte? Klicken Sie &quot;Suchen&quot; für eine Suche
              via Parlament-API.
            </p>
          </div>
        )}

        {/* API search results */}
        {results.length > 0 && (
          <div className="space-y-3">
            {results.map((r) => (
              <div
                key={r.business_number}
                className="flex justify-between items-start p-3 rounded-md border border-gray-100 dark:border-gray-700"
              >
                <div className="min-w-0 flex-1">
                  <div className="text-xs font-mono text-gray-400">
                    {r.business_number}
                  </div>
                  <div className="text-sm font-medium truncate">
                    {r.title}
                  </div>
                </div>
                <button
                  onClick={() => handleAdd(r.business_number)}
                  className="ml-3 text-sm text-swiss-red hover:underline flex-shrink-0"
                >
                  Verfolgen
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
