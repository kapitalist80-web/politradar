const API_BASE = "/api";

function authHeaders() {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request(path, options = {}) {
  const { headers: extraHeaders, ...fetchOptions } = options;
  const res = await fetch(`${API_BASE}${path}`, {
    ...fetchOptions,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...extraHeaders,
    },
  });

  if (res.status === 401) {
    localStorage.removeItem("token");
    throw new Error("Ungueltige Anmeldedaten");
  }

  if (res.status === 204) return null;

  let data;
  try {
    data = await res.json();
  } catch {
    if (!res.ok) throw new Error(`Serverfehler (${res.status})`);
    throw new Error("Ungueltige Serverantwort");
  }
  if (!res.ok) throw new Error(data.detail || "Fehler");
  return data;
}

// Auth
export const login = (email, password) =>
  request("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });

export const register = (email, name, password) =>
  request("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, name, password }),
  });

export const getMe = () => request("/auth/me");

// Businesses
export const getBusinesses = () => request("/businesses");

export const addBusiness = (businessNumber) =>
  request("/businesses", {
    method: "POST",
    body: JSON.stringify({ business_number: businessNumber }),
  });

export const getBusiness = (id) => request(`/businesses/${id}`);

export const deleteBusiness = (id) =>
  request(`/businesses/${id}`, { method: "DELETE" });

export const getBusinessSchedule = (id) => request(`/businesses/${id}/schedule`);

// Alerts
export const getAlerts = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/alerts${qs ? `?${qs}` : ""}`);
};

export const markAlertRead = (id) =>
  request(`/alerts/${id}/read`, { method: "PATCH" });

export const markAllAlertsRead = () =>
  request("/alerts/read-all", { method: "POST" });

// Monitoring
export const getMonitoringCandidates = (decision = "pending") =>
  request(`/monitoring?decision=${decision}`);

export const decideCandiate = (id, decision) =>
  request(`/monitoring/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ decision }),
  });

// Parliament search / preview
export const searchParliament = (q) =>
  request(`/parliament/search?q=${encodeURIComponent(q)}`);

export const previewBusiness = (nr) =>
  request(`/parliament/preview/${encodeURIComponent(nr)}`);
