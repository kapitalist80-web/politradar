import { useState } from "react";
import { useAuth } from "../context/AuthContext";

export default function Settings() {
  const { user } = useAuth();
  const [dark, setDark] = useState(
    document.documentElement.classList.contains("dark"),
  );

  const toggleDark = () => {
    document.documentElement.classList.toggle("dark");
    setDark(!dark);
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

      {/* Notifications placeholder */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="font-semibold mb-4">Benachrichtigungen</h2>
        <p className="text-sm text-gray-500">
          E-Mail-Benachrichtigungen werden in einer zukuenftigen Version
          verfuegbar sein.
        </p>
      </div>
    </div>
  );
}
