let accessTokenMemory: string | null = null;
const TOKEN_KEY = "vt_access_token";

export function setAccessToken(token: string) {
  accessTokenMemory = token;
  if (typeof localStorage !== "undefined") {
    localStorage.setItem(TOKEN_KEY, token);
  }
}

export function getAccessToken(): string | null {
  if (accessTokenMemory) return accessTokenMemory;
  if (typeof localStorage !== "undefined") {
    const stored = localStorage.getItem(TOKEN_KEY);
    accessTokenMemory = stored;
    return stored;
  }
  return null;
}

export function clearAccessToken() {
  accessTokenMemory = null;
  if (typeof localStorage !== "undefined") {
    localStorage.removeItem(TOKEN_KEY);
  }
}
