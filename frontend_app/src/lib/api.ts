import { getAccessToken, clearAccessToken } from "./token";

export class ConsentRequiredError extends Error {
  status: number;
  requiredScopes: string[];
  constructor(requiredScopes: string[] = [], message = "Consent required") {
    super(message);
    this.name = "ConsentRequiredError";
    this.status = 403;
    this.requiredScopes = requiredScopes;
  }
}

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
  if (resp.status === 403) {
    let payload: any = null;
    try {
      payload = await resp.clone().json();
    } catch {
      payload = null;
    }
    const code = payload?.code || payload?.detail?.error || payload?.detail?.code;
    const requiredScopes =
      payload?.required_scopes ||
      payload?.detail?.required_scopes ||
      payload?.detail?.scope ||
      [];
    if (code === "consent_required" || Array.isArray(requiredScopes)) {
      const scopes = Array.isArray(requiredScopes) ? requiredScopes : [];
      throw new ConsentRequiredError(scopes);
    }
  }
  return resp;
}
