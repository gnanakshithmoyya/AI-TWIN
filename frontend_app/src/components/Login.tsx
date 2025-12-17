import React, { useState } from "react";
import { setAccessToken, clearAccessToken } from "../lib/token";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

type Props = {
  onAuth: () => void;
};

export function Login({ onAuth }: Props) {
  const [email, setEmail] = useState("test@vitatwin.ai");
  const [password, setPassword] = useState("StrongPass123");
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const resp = await fetch(`${API_BASE}/auth/${mode === "login" ? "login" : "signup"}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!resp.ok) {
        const msg = await resp.text();
        throw new Error(msg || "Auth failed");
      }
      const data = await resp.json();
      if (data.access_token) {
        setAccessToken(data.access_token);
      }
      setLoading(false);
      onAuth();
    } catch (err: any) {
      setLoading(false);
      setError(err?.message || "Auth error");
      clearAccessToken();
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-vita-bg px-4">
      <form
        onSubmit={submit}
        className="bg-white rounded-3xl shadow-md border border-vita-border p-8 w-full max-w-md space-y-4"
      >
        <h1 className="text-2xl font-semibold text-vita-text text-center">VitaTwin Login</h1>
        <div className="space-y-2">
          <label className="text-sm text-vita-text-muted">Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full border border-vita-border rounded-xl p-3 focus:outline-none focus:ring-1 focus:ring-vita-sage"
            required
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm text-vita-text-muted">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full border border-vita-border rounded-xl p-3 focus:outline-none focus:ring-1 focus:ring-vita-sage"
            required
          />
        </div>
        {error && <p className="text-sm text-red-500">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-vita-text text-white rounded-xl py-3 font-semibold hover:bg-vita-text/90 disabled:opacity-50"
        >
          {loading ? "Please wait..." : mode === "login" ? "Login" : "Sign up"}
        </button>
        <button
          type="button"
          onClick={() => setMode(mode === "login" ? "signup" : "login")}
          className="w-full text-sm text-vita-text-muted underline"
        >
          {mode === "login" ? "Need an account? Sign up" : "Already have an account? Log in"}
        </button>
      </form>
    </div>
  );
}
