"use client";

import { useEffect, useState } from "react";
import { Copy, KeyRound, RefreshCcw, Save } from "lucide-react";
import {
  regenerateAppApiKey,
  type AppApiKeyResponse,
  type ClientApp,
  updateApp
} from "@/lib/api-client";

type AppOverviewProps = {
  app: ClientApp;
  onUpdated: (app: ClientApp) => void;
};

export function AppOverview({ app, onUpdated }: AppOverviewProps) {
  const [name, setName] = useState(app.name);
  const [generatedKey, setGeneratedKey] = useState<AppApiKeyResponse | null>(null);
  const [saving, setSaving] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [copiedKey, setCopiedKey] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    setName(app.name);
    setGeneratedKey(null);
    setCopiedKey(false);
  }, [app.client_id, app.name]);

  const dirty = name.trim() !== app.name;

  async function handleSave() {
    if (!dirty) {
      return;
    }
    setSaving(true);
    setMessage("");
    try {
      const updated = await updateApp(app.id, {
        name: name.trim()
      });
      onUpdated(updated);
      setMessage("Application details saved.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not save app.");
    } finally {
      setSaving(false);
    }
  }

  async function handleRegenerateKey() {
    const confirmed = window.confirm(
      "Regenerate this app API key? The existing key will stop working."
    );
    if (!confirmed) {
      return;
    }
    setRegenerating(true);
    setMessage("");
    try {
      const result = await regenerateAppApiKey(app.id);
      setGeneratedKey(result);
      setCopiedKey(false);
      setMessage("API key regenerated. Copy it before leaving this page.");
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Could not regenerate API key."
      );
    } finally {
      setRegenerating(false);
    }
  }

  async function handleCopyGeneratedKey() {
    if (!generatedKey) {
      return;
    }
    await navigator.clipboard.writeText(generatedKey.api_key);
    setCopiedKey(true);
    window.setTimeout(() => setCopiedKey(false), 1800);
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
            readOnly
            value={app.client_id}
          />
        </DetailField>
      </div>

      <div className="mt-8 rounded-xl border border-gms-line bg-[#f7f9ff] p-5 dark:bg-[#20242c]">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="flex items-center gap-3 text-gms-text">
              <KeyRound className="h-5 w-5 text-gms-blue" />
              <h3 className="text-sm font-extrabold">App API key</h3>
            </div>
            <p className="mt-2 text-xs text-gms-muted">
              Regenerate a key when the current key is lost or exposed. The new
              key is shown once and the old key stops working immediately.
            </p>
          </div>
          <button
            className="inline-flex h-10 items-center gap-2 rounded-md border border-gms-blue px-4 text-sm font-semibold text-gms-blue hover:bg-gms-blue-soft disabled:opacity-50"
            disabled={regenerating}
            type="button"
            onClick={handleRegenerateKey}
          >
            <RefreshCcw className="h-4 w-4" />
            {regenerating ? "Regenerating..." : "Regenerate Key"}
          </button>
        </div>

        {generatedKey && (
          <div className="mt-5 rounded-lg border border-[#9bb5ff] bg-white p-4 dark:bg-[#252932]">
            <p className="text-xs font-semibold text-gms-blue">
              {generatedKey.api_key_notice}
            </p>
            <div className="mt-3 flex gap-2">
              <input
                className="h-10 min-w-0 flex-1 rounded border border-gms-blue bg-white px-3 font-mono text-xs text-gms-text outline-none dark:bg-[#20242c]"
                readOnly
                value={generatedKey.api_key}
              />
              <button
                className="inline-flex h-10 items-center gap-2 rounded-md bg-gms-blue px-4 text-sm font-semibold text-white shadow-button"
                type="button"
                onClick={handleCopyGeneratedKey}
              >
                <Copy className="h-4 w-4" />
                {copiedKey ? "Copied!" : "Copy"}
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="mt-8 flex items-center gap-4">
        <button
          className="inline-flex h-10 items-center gap-2 rounded-md bg-gms-blue px-5 text-sm font-semibold text-white shadow-button disabled:opacity-50"
          disabled={!dirty || saving}
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
