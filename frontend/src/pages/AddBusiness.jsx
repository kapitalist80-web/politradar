import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  addBusiness,
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
  const navigate = useNavigate();

  const handlePreview = async () => {
    if (!number.match(/^\d{2}\.\d{3,5}$/)) {
      setError("Format: z.B. 24.3927");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const data = await previewBusiness(number);
      setPreview(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (query.length < 2) return;
    setError("");
    setLoading(true);
    try {
      const data = await searchParliament(query);
      setResults(data || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async (businessNumber) => {
    setError("");
    try {
      await addBusiness(businessNumber);
      navigate("/");
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Geschaeft hinzufuegen</h1>

      {error && (
        <div className="text-sm text-red-600 bg-red-50 dark:bg-red-900/20 p-3 rounded mb-4">
          {error}
        </div>
      )}

      {/* Direct number input */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <h2 className="font-medium mb-3">Geschaeftsnummer eingeben</h2>
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
            className="mt-4 bg-swiss-red text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-swiss-dark"
          >
            Verfolgen
          </button>
        </div>
      )}

      {/* Search */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="font-medium mb-3">Geschaeft suchen</h2>
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
