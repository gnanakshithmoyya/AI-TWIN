import React, { useEffect, useMemo, useState } from "react";
import { apiFetch } from "../lib/api";

export const FULL_RECOMMENDED_SCOPES = [
  "wearables_connect",
  "wearables_sync",
  "chat_history",
  "memory_personalization",
  "steps_activity_data",
  "heart_rate_data",
  "sleep_data",
];

type Step = "intro" | "mode" | "customize";

interface ConsentModalProps {
  open: boolean;
  requiredScopes?: string[];
  onClose: () => void;
  onGranted: () => void;
}

export function ConsentModal({ open, requiredScopes, onClose, onGranted }: ConsentModalProps) {
  const [step, setStep] = useState<Step>("intro");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const initialSelected = useMemo(() => {
    if (requiredScopes && requiredScopes.length > 0) return [...new Set(requiredScopes)];
    return FULL_RECOMMENDED_SCOPES;
  }, [requiredScopes]);

  const [selectedScopes, setSelectedScopes] = useState<string[]>(initialSelected);

  useEffect(() => {
    if (open) {
      setStep("intro");
      setSelectedScopes(initialSelected);
      setError(null);
    }
  }, [open, initialSelected]);

  if (!open) return null;

  const toggleScope = (scope: string) => {
    setSelectedScopes((prev) =>
      prev.includes(scope) ? prev.filter((s) => s !== scope) : [...prev, scope]
    );
  };

  const grantScopes = async (scopes: string[]) => {
    if (!scopes.length) {
      setError("Select at least one option to continue.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const resp = await apiFetch("/consent/grant-bulk", {
        method: "POST",
        body: JSON.stringify({ scopes }),
      });
      if (!resp.ok) throw new Error(`Consent update failed (${resp.status})`);
      onGranted();
    } catch (err: any) {
      setError(err?.message || "Unable to save your choices right now.");
    } finally {
      setSaving(false);
    }
  };

  const handleAcceptAll = () => {
    grantScopes(FULL_RECOMMENDED_SCOPES);
  };

  const handleSaveCustom = () => {
    grantScopes(selectedScopes);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm px-4">
      <div className="bg-white rounded-3xl shadow-2xl w-full max-w-xl p-8 space-y-6 relative">
        <button
          aria-label="Close"
          className="absolute right-4 top-4 text-sm text-vita-text-muted hover:text-vita-text"
          onClick={onClose}
          disabled={saving}
        >
          ✕
        </button>

        {step === "intro" && (
          <>
            <h2 className="text-2xl font-semibold text-vita-text">
              Allow VitaTwin to access your health data?
            </h2>
            <p className="text-vita-text-muted leading-relaxed">
              We only use your data to provide educational insights. We don’t diagnose, prescribe, or
              share your data. You can change this anytime in Settings.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 sm:justify-end pt-2">
              <button
                className="px-5 py-3 rounded-xl border border-vita-border text-vita-text font-medium hover:bg-vita-bg"
                onClick={onClose}
                disabled={saving}
              >
                Reject
              </button>
              <button
                className="px-5 py-3 rounded-xl bg-vita-text text-white font-semibold hover:bg-vita-text/90"
                onClick={() => setStep("mode")}
                disabled={saving}
              >
                Accept
              </button>
            </div>
          </>
        )}

        {step === "mode" && (
          <>
            <h2 className="text-2xl font-semibold text-vita-text">
              Choose how much access you want to allow
            </h2>
            <div className="space-y-4">
              <button
                className="w-full text-left p-4 rounded-2xl border border-vita-border hover:border-vita-sage/60 hover:shadow-sm transition flex items-center justify-between"
                onClick={handleAcceptAll}
                disabled={saving}
              >
                <div>
                  <div className="font-semibold text-vita-text">Accept All (Recommended)</div>
                  <p className="text-sm text-vita-text-muted">
                    Enables wearables syncing, chat history, and personalization.
                  </p>
                </div>
                <span className="text-sm text-vita-sage font-semibold">Grant</span>
              </button>

              <button
                className="w-full text-left p-4 rounded-2xl border border-vita-border hover:border-vita-sage/60 hover:shadow-sm transition"
                onClick={() => setStep("customize")}
                disabled={saving}
              >
                <div className="font-semibold text-vita-text">Limit Access (Customize)</div>
                <p className="text-sm text-vita-text-muted">Select only the data you’re comfortable sharing.</p>
              </button>
            </div>
            <div className="flex justify-end gap-3 pt-3">
              <button
                className="px-4 py-2 rounded-xl text-sm text-vita-text-muted hover:text-vita-text"
                onClick={() => setStep("intro")}
                disabled={saving}
              >
                Back
              </button>
            </div>
          </>
        )}

        {step === "customize" && (
          <>
            <h2 className="text-2xl font-semibold text-vita-text">Customize access</h2>
            <p className="text-vita-text-muted text-sm">
              Select the data VitaTwin can use. You can change this later.
            </p>

            <div className="space-y-4">
              <div className="border border-vita-border rounded-2xl p-4">
                <div className="font-semibold text-vita-text mb-3">Wearables</div>
                {[
                  { id: "wearables_connect", label: "Allow connecting wearables" },
                  { id: "wearables_sync", label: "Allow syncing wearable data" },
                  { id: "steps_activity_data", label: "Steps & activity" },
                  { id: "heart_rate_data", label: "Heart rate" },
                  { id: "sleep_data", label: "Sleep" },
                ].map((item) => (
                  <label key={item.id} className="flex items-center justify-between py-2">
                    <span className="text-sm text-vita-text">{item.label}</span>
                    <input
                      type="checkbox"
                      className="w-5 h-5 accent-vita-text"
                      checked={selectedScopes.includes(item.id)}
                      onChange={() => toggleScope(item.id)}
                      disabled={saving}
                    />
                  </label>
                ))}
              </div>

              <div className="border border-vita-border rounded-2xl p-4">
                <div className="font-semibold text-vita-text mb-3">Personalization</div>
                {[
                  { id: "chat_history", label: "Store chat history" },
                  { id: "memory_personalization", label: "Personalized memory" },
                ].map((item) => (
                  <label key={item.id} className="flex items-center justify-between py-2">
                    <span className="text-sm text-vita-text">{item.label}</span>
                    <input
                      type="checkbox"
                      className="w-5 h-5 accent-vita-text"
                      checked={selectedScopes.includes(item.id)}
                      onChange={() => toggleScope(item.id)}
                      disabled={saving}
                    />
                  </label>
                ))}
              </div>
            </div>

            {error && <div className="text-sm text-red-600">{error}</div>}

            <div className="flex justify-end gap-3 pt-4">
              <button
                className="px-4 py-2 rounded-xl text-sm text-vita-text-muted hover:text-vita-text"
                onClick={() => setStep("mode")}
                disabled={saving}
              >
                Back
              </button>
              <button
                className="px-5 py-3 rounded-xl bg-vita-text text-white font-semibold hover:bg-vita-text/90 disabled:opacity-60"
                onClick={handleSaveCustom}
                disabled={saving}
              >
                {saving ? "Saving..." : "Save choices"}
              </button>
            </div>
          </>
        )}

        <p className="text-xs text-vita-text-muted border-t border-vita-border pt-4">
          We don’t diagnose, prescribe, or share your data. You can change this anytime in Settings.
        </p>
      </div>
    </div>
  );
}
