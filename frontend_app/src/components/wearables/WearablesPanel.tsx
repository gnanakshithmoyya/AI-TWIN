import React, { useEffect, useState } from "react";
import { apiFetch, ConsentRequiredError } from "../../lib/api";

interface WearablesPanelProps {
  onConsentRequired: (scopes?: string[], retry?: () => void) => void;
}

export function WearablesPanel({ onConsentRequired }: WearablesPanelProps) {
  const [status, setStatus] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [syncResult, setSyncResult] = useState<any | null>(null);

  const loadStatus = async () => {
    try {
      const resp = await apiFetch("/wearables/status");
      if (resp.ok) {
        setStatus(await resp.json());
      }
    } catch (err: any) {
      if (err instanceof ConsentRequiredError) {
        onConsentRequired(err.requiredScopes, () => loadStatus());
      }
    }
  };

  useEffect(() => {
    loadStatus();
  }, []);

  const connectFitbit = async () => {
    setError(null);
    try {
      const resp = await apiFetch("/wearables/connect", {
        method: "POST",
        body: JSON.stringify({ provider: "fitbit" }),
      });
      if (!resp.ok) {
        setError("Unable to connect Fitbit");
        return;
      }
      const data = await resp.json();
      if (data.connect_url) {
        window.open(data.connect_url, "_blank");
      }
      await loadStatus();
    } catch (err: any) {
      if (err instanceof ConsentRequiredError) {
        onConsentRequired(err.requiredScopes, () => connectFitbit());
        return;
      }
      setError("Unable to connect Fitbit");
    }
  };

  const syncFitbit = async () => {
    setError(null);
    setLoading(true);
    setSyncResult(null);
    try {
      const resp = await apiFetch("/wearables/sync", {
        method: "POST",
        body: JSON.stringify({
          provider: "fitbit",
          signals: ["activity_steps", "heart_rate", "sleep_duration"],
        }),
      });
      setLoading(false);
      if (!resp.ok) {
        setError("Unable to sync");
        return;
      }
      const data = await resp.json();
      setSyncResult(data.health_state || {});
      await loadStatus();
    } catch (err: any) {
      setLoading(false);
      if (err instanceof ConsentRequiredError) {
        onConsentRequired(err.requiredScopes, () => syncFitbit());
        return;
      }
      setError("Unable to sync");
    }
  };

  const renderHealthState = () => {
    if (!syncResult) return null;
    return (
      <div className="mt-4 p-4 bg-white border border-vita-border rounded-2xl">
        <h4 className="font-semibold text-vita-text mb-2">Synced health data</h4>
        {Object.keys(syncResult).length === 0 && (
          <p className="text-sm text-vita-text-muted">No data returned (stub).</p>
        )}
        <ul className="space-y-1 text-sm text-vita-text">
          {Object.entries(syncResult).map(([k, v]) => (
            <li key={k}>
              <span className="font-medium">{k}:</span> {JSON.stringify(v)}
            </li>
          ))}
        </ul>
      </div>
    );
  };

  return (
    <div className="max-w-5xl mx-auto p-6 md:p-12 space-y-8">
      <div className="space-y-2">
        <h1 className="text-3xl font-semibold text-vita-text">Wearables</h1>
        <p className="text-vita-text-muted">
          Connect Fitbit and control consents for data sync. Apple Health shown as future (iOS only).
        </p>
      </div>

      {error && <div className="p-4 border border-red-200 bg-red-50 rounded-xl text-sm text-red-700">{error}</div>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white border border-vita-border rounded-2xl p-6 space-y-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xl font-semibold text-vita-text">Fitbit</h3>
              <p className="text-sm text-vita-text-muted">Connect and sync activity, sleep, heart rate.</p>
            </div>
            <span className="px-3 py-1 rounded-full bg-vita-sage-light text-vita-sage text-xs font-medium">
              Active
            </span>
          </div>
          <button
            onClick={connectFitbit}
            className="w-full bg-vita-text text-white rounded-xl py-3 font-semibold hover:bg-vita-text/90 transition"
          >
            Connect Fitbit
          </button>
          <button
            onClick={syncFitbit}
            disabled={loading}
            className="w-full bg-white border border-vita-border text-vita-text rounded-xl py-3 font-semibold hover:bg-vita-bg transition disabled:opacity-50"
          >
            {loading ? "Syncing..." : "Sync now"}
          </button>
          <div>
            <h4 className="font-semibold text-vita-text mb-1">Status</h4>
            <ul className="text-sm text-vita-text-muted space-y-1">
              {status.length === 0 && <li>No providers connected.</li>}
              {status.map((s) => (
                <li key={s.provider}>
                  {s.provider}: connected_at {s.connected_at || "n/a"}, last_sync {s.last_sync_at || "n/a"}
                </li>
              ))}
            </ul>
          </div>
          {renderHealthState()}
        </div>

        <div className="bg-white border border-vita-border rounded-2xl p-6 space-y-4 shadow-sm opacity-70">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xl font-semibold text-vita-text">Apple Health</h3>
              <p className="text-sm text-vita-text-muted">Requires iOS app. Not available on web.</p>
            </div>
            <span className="px-3 py-1 rounded-full bg-gray-100 text-gray-500 text-xs font-medium">
              Coming soon
            </span>
          </div>
          <button disabled className="w-full bg-gray-200 text-gray-500 rounded-xl py-3 font-semibold cursor-not-allowed">
            Connect (iOS only)
          </button>
        </div>
      </div>
    </div>
  );
}
