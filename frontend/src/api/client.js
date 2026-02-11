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
    throw new Error("Ungültige Anmeldedaten");
  }

  if (res.status === 204) return null;

  let data;
  try {
    data = await res.json();
  } catch {
    if (!res.ok) throw new Error(`Serverfehler (${res.status})`);
    throw new Error("Ungültige Serverantwort");
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

export const updateBusinessPriority = (id, priority) =>
  request(`/businesses/${id}/priority`, {
    method: "PATCH",
    body: JSON.stringify({ priority }),
  });

export const getBusinessNotes = (id) => request(`/businesses/${id}/notes`);

export const addBusinessNote = (id, content) =>
  request(`/businesses/${id}/notes`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });

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
export const getMonitoringCandidates = (decision = "pending", businessType = "") => {
  const params = new URLSearchParams({ decision });
  if (businessType) params.set("business_type", businessType);
  return request(`/monitoring?${params.toString()}`);
};

export const getMonitoringBusinessTypes = () =>
  request("/monitoring/business-types");

export const decideCandiate = (id, decision) =>
  request(`/monitoring/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ decision }),
  });

// Parliament search / preview / cache
export const getRecentBusinesses = () => request("/parliament/recent");

export const searchParliament = (q) =>
  request(`/parliament/search?q=${encodeURIComponent(q)}`);

export const previewBusiness = (nr) =>
  request(`/parliament/preview/${encodeURIComponent(nr)}`);

// Settings
export const getEmailSettings = () => request("/settings/email");

export const updateEmailSettings = (settings) =>
  request("/settings/email", {
    method: "PUT",
    body: JSON.stringify(settings),
  });

// Parliamentarians
export const getParliamentarians = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/parliamentarians${qs ? `?${qs}` : ""}`);
};

export const getParliamentarian = (personNumber) =>
  request(`/parliamentarians/${personNumber}`);

export const getParliamentarianVotes = (personNumber, limit = 50, offset = 0) =>
  request(`/parliamentarians/${personNumber}/votes?limit=${limit}&offset=${offset}`);

export const getParliamentarianStats = (personNumber) =>
  request(`/parliamentarians/${personNumber}/stats`);

// Committees
export const getCommittees = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/committees${qs ? `?${qs}` : ""}`);
};

export const getCommitteeMembers = (committeeNumber) =>
  request(`/committees/${committeeNumber}/members`);

// Councils
export const getCouncilMembers = (councilId) =>
  request(`/councils/${councilId}/members`);

// Parties & Parliamentary Groups
export const getParties = () => request("/parties");
export const getParlGroups = () => request("/parl-groups");

// Votes
export const getVoteSessions = () => request("/votes/sessions");

export const getRecentVotes = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/votes/recent${qs ? `?${qs}` : ""}`);
};

export const getVoteDetail = (voteId) => request(`/votes/${voteId}`);

// Business Treating Body & Predictions
export const getTreatingBody = (businessId) =>
  request(`/businesses/${businessId}/treating-body`);

export const getVotePrediction = (businessId) =>
  request(`/businesses/${businessId}/vote-prediction`);

// Manual Sync
export const triggerSyncParliamentarians = () =>
  request("/sync/parliamentarians", { method: "POST" });

export const triggerSyncCommittees = () =>
  request("/sync/committees", { method: "POST" });

export const triggerSyncVotingData = () =>
  request("/sync/voting-data", { method: "POST" });

export const triggerSyncBusinesses = () =>
  request("/sync/businesses", { method: "POST" });

export const triggerSyncAll = () =>
  request("/sync/all", { method: "POST" });
