import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { login } from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const { loginUser } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const data = await login(email, password);
      loginUser(data.access_token, data.user);
      navigate("/");
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <span className="text-swiss-red font-bold text-3xl">+</span>
          <h1 className="text-2xl font-bold mt-2">Parlamentsmonitor</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Anmelden
          </p>
        </div>
        <form
          onSubmit={handleSubmit}
          className="bg-white dark:bg-gray-800 shadow rounded-lg p-8 space-y-4"
        >
          {error && (
            <div className="text-sm text-red-600 bg-red-50 dark:bg-red-900/20 p-3 rounded">
              {error}
            </div>
          )}
          <div>
            <label className="block text-sm font-medium mb-1">E-Mail</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-swiss-red"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Passwort</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-swiss-red"
            />
          </div>
          <button
            type="submit"
            className="w-full bg-swiss-red text-white py-2 rounded-md font-medium hover:bg-swiss-dark transition-colors"
          >
            Anmelden
          </button>
          <p className="text-sm text-center text-gray-500">
            Noch kein Konto?{" "}
            <Link to="/register" className="text-swiss-red hover:underline">
              Registrieren
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
