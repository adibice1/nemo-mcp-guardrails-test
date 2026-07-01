"use client";

import { useEffect, useState } from "react";
import { Eye, EyeOff, KeyRound, Save } from "lucide-react";
import { type ClientApp, updateApp } from "@/lib/api-client";

type AppOverviewProps = {
  app: ClientApp;
  onUpdated: (app: ClientApp) => void;
};

export function AppOverview({ app, onUpdated }: AppOverviewProps) {
  const [name, setName] = useState(app.name);
  const [clientId, setClientId] = useState(app.client_id);
  const [newApiKey, setNewApiKey] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    setName(app.name);
    setClientId(app.client_id);
  }, [app.client_id, app.name]);

  const dirty =
    name.trim() !== app.name ||
    clientId.trim() !== app.client_id ||
    newApiKey.length > 0;

  async function handleSave() {
    if (!dirty || (newApiKey.length > 0 && newApiKey.length < 16)) {
      return;
    }
    setSaving(true);
    setMessage("");
    try {
      const updated = await updateApp(app.id, {
        name: name.trim(),
        client_id: clientId.trim(),
        ...(newApiKey ? { api_key: newApiKey } : {})
      });
      onUpdated(updated);
      setNewApiKey("");
      setMessage("Application details saved.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not save app.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="max-w-[850px]">
      <div>
        <h2 className="text-2xl font-extrabold text-gms-text">Overview</h2>
        <p className="mt-2 text-sm text-gms-muted">
          Update the identity used by this application to access GMS.
        </p>
      </div>

      <div className="mt-8 grid gap-6 md:grid-cols-2">
        <DetailField label="Application Name">
          <input
            className="detail-input"
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
        </DetailField>
        <DetailField label="Client ID">
          <input
            className="detail-input font-mono"
            value={clientId}
            onChange={(event) => setClientId(event.target.value)}
          />
        </DetailField>
      </div>

      <DetailField label="Rotate API Key" className="mt-6">
        <div className="relative">
          <KeyRound className="absolute left-3 top-3 h-5 w-5 text-gms-muted" />
          <input
            className="detail-input px-10 pr-12"
            minLength={16}
            placeholder="Leave blank to keep the current key"
            type={showKey ? "text" : "password"}
            value={newApiKey}
            onChange={(event) => setNewApiKey(event.target.value)}
          />
          <button
            aria-label={showKey ? "Hide API key" : "Show API key"}
            className="absolute right-3 top-3 text-gms-muted hover:text-gms-blue"
            type="button"
            onClick={() => setShowKey((current) => !current)}
          >
            {showKey ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
          </button>
        </div>
        <p className="mt-2 text-xs text-gms-muted">
          A rotated key cannot be recovered after saving. Minimum 16 characters.
        </p>
      </DetailField>

      <div className="mt-8 flex items-center gap-4">
        <button
          className="inline-flex h-10 items-center gap-2 rounded-md bg-gms-blue px-5 text-sm font-semibold text-white shadow-button disabled:opacity-50"
          disabled={!dirty || saving || (newApiKey.length > 0 && newApiKey.length < 16)}
          type="button"
          onClick={handleSave}
        >
          <Save className="h-4 w-4" />
          {saving ? "Saving..." : "Save Changes"}
        </button>
        {message && <p className="text-sm text-gms-muted">{message}</p>}
      </div>
    </div>
  );
}

function DetailField({
  label,
  className = "",
  children
}: {
  label: string;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <label className={`block text-sm font-bold text-gms-text ${className}`}>
      {label}
      <div className="mt-2">{children}</div>
    </label>
  );
}
