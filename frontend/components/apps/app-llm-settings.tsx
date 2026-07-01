"use client";

import { useEffect, useState } from "react";
import { Save } from "lucide-react";
import { type ClientApp, updateApp } from "@/lib/api-client";

export function AppLlmSettings({
  app,
  onUpdated
}: {
  app: ClientApp;
  onUpdated: (app: ClientApp) => void;
}) {
  const [mainId, setMainId] = useState("");
  const [guardrailId, setGuardrailId] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    setMainId(app.main_llm_config_id?.toString() ?? "");
    setGuardrailId(app.guardrail_llm_config_id?.toString() ?? "");
  }, [app.guardrail_llm_config_id, app.main_llm_config_id]);

  async function handleSave() {
    try {
      const updated = await updateApp(app.id, {
        main_llm_config_id: mainId ? Number(mainId) : null,
        guardrail_llm_config_id: guardrailId ? Number(guardrailId) : null
      });
      onUpdated(updated);
      setMessage("LLM selections saved.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not save LLM settings.");
    }
  }

  return (
    <div className="max-w-[850px]">
      <h2 className="text-2xl font-extrabold text-gms-text">LLM Configuration</h2>
      <p className="mt-2 text-sm text-gms-muted">
        Choose separate configurations for the application agent and guardrail classifiers.
      </p>
      <div className="mt-8 grid gap-6 md:grid-cols-2">
        <label className="text-sm font-bold text-gms-text">
          Main Agent LLM Config ID
          <input
            className="detail-input mt-2"
            min={1}
            placeholder="Uses environment default when blank"
            type="number"
            value={mainId}
            onChange={(event) => setMainId(event.target.value)}
          />
        </label>
        <label className="text-sm font-bold text-gms-text">
          Guardrail LLM Config ID
          <input
            className="detail-input mt-2"
            min={1}
            placeholder="Uses environment default when blank"
            type="number"
            value={guardrailId}
            onChange={(event) => setGuardrailId(event.target.value)}
          />
        </label>
      </div>
      <p className="mt-4 text-xs text-gms-muted">
        A readable LLM catalogue endpoint is not available yet, so this screen uses existing database IDs.
      </p>
      <div className="mt-7 flex items-center gap-4">
        <button
          className="inline-flex h-10 items-center gap-2 rounded-md bg-gms-blue px-5 text-sm font-semibold text-white shadow-button"
          type="button"
          onClick={handleSave}
        >
          <Save className="h-4 w-4" />
          Save LLM Settings
        </button>
        {message && <p className="text-sm text-gms-muted">{message}</p>}
      </div>
    </div>
  );
}
