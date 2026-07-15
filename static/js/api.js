/* Smart Queue Management System — lightweight API client for the
   authentication endpoints built in Phase 3. Plain fetch, no build step. */

(function () {
  "use strict";

  const API_BASE = "/api/v1/accounts";
  const KEYS = { access: "sqms_access", refresh: "sqms_refresh", user: "sqms_user" };

  function extractErrorMessage(body) {
    if (body && body.error && body.error.message) return body.error.message;
    if (body && body.detail) return body.detail;
    if (body && typeof body === "object") {
      const firstKey = Object.keys(body)[0];
      if (firstKey) {
        const value = body[firstKey];
        return Array.isArray(value) ? value[0] : String(value);
      }
    }
    return "Something went wrong. Please try again.";
  }

  async function post(path, data) {
    const response = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(extractErrorMessage(body));
    }
    return body;
  }

  async function authorizedGet(path) {
    const response = await fetch(`${API_BASE}${path}`, {
      headers: { Authorization: `Bearer ${getAccessToken()}` },
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(extractErrorMessage(body));
    return body;
  }

  function setSession(access, refresh, user) {
    localStorage.setItem(KEYS.access, access);
    localStorage.setItem(KEYS.refresh, refresh);
    if (user) localStorage.setItem(KEYS.user, JSON.stringify(user));
  }

  function clearSession() {
    localStorage.removeItem(KEYS.access);
    localStorage.removeItem(KEYS.refresh);
    localStorage.removeItem(KEYS.user);
  }

  function getAccessToken() { return localStorage.getItem(KEYS.access); }
  function getRefreshToken() { return localStorage.getItem(KEYS.refresh); }
  function getUser() {
    const raw = localStorage.getItem(KEYS.user);
    return raw ? JSON.parse(raw) : null;
  }
  function isAuthenticated() { return !!getAccessToken(); }

  window.SQMSApi = {
    post, authorizedGet,
    setSession, clearSession,
    getAccessToken, getRefreshToken, getUser, isAuthenticated,
  };
})();
