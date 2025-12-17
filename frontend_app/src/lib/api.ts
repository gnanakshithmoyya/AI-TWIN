import { getAccessToken, clearAccessToken } from "./token";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

export async function apiFetch(path: string, options: RequestInit = {}) {
  const token = getAccessToken();
  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  const resp = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });
  if (resp.status === 401) {
    clearAccessToken();
    // redirect to login
    window.location.href = "/";
    return Promise.reject(new Error("Unauthorized"));
  }
  return resp;
}
