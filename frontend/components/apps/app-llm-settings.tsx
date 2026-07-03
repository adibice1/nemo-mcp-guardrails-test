"use client";

import { useEffect, useState } from "react";
import { Plus, Save } from "lucide-react";
import { CreateLlmConfigModal } from "@/components/apps/create-llm-config-modal";
import {
  type ClientApp,
  type LlmConfig,
  type LlmConfigCreatePayload,
  createLlmConfig,
  listLlmConfigs,
  updateApp
} from "@/lib/api-client";
import { loadManagementSession } from "@/lib/management-auth";

export function AppLlmSettings({
  app,
  onUpdated
}: {
  app: ClientApp;
  onUpdated: (app: ClientApp) => void;
}) {
  const [mainId, setMainId] = useState("");
  const [guardrailId, setGuardrailId] = useState("");
  const [configs, setConfigs] = useState<LlmConfig[]>([]);
  const [loadingConfigs, setLoadingConfigs] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    setIsAdmin(loadManagementSession()?.user.system_role === "admin");
  }, []);

  useEffect(() => {
    setMainId(app.main_llm_config_id?.toString() ?? "");
    setGuardrailId(app.guardrail_llm_config_id?.toString() ?? "");
  }, [app.guardrail_llm_config_id, app.main_llm_config_id]);

  useEffect(() => {
    let active = true;

    listLlmConfigs()
      .then((items) => {
        if (active) setConfigs(items);
      })
      .catch((error) => {
        if (active) {
          setMessage(
            error instanceof Error
              ? error.message
              : "Could not load LLM configurations."
          );
        }
      })
      .finally(() => {
        if (active) setLoadingConfigs(false);
      });

    return () => {
      active = false;
    };
  }, []);

  async function handleSave() {
    try {
      const payload = {
        main_llm_config_id: mainId ? Number(mainId) : null,
        ...(isAdmin
          ? { guardrail_llm_config_id: guardrailId ? Number(guardrailId) : null }
          : {})
      };
      const updated = await updateApp(app.id, payload);
      onUpdated(updated);
      setMessage("LLM selections saved.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not save LLM settings.");
    }
  }

  async function handleCreate(payload: LlmConfigCreatePayload) {
    try {
      const created = await createLlmConfig(payload);
      setConfigs((current) =>
        [...current, created].sort((left, right) => left.name.localeCompare(right.name))
      );
      setMessage(`LLM configuration "${created.name}" created.`);
      return true;
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Could not create LLM configuration."
      );
      return false;
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
          Main Agent LLM
          <select
            className="detail-input mt-2"
            disabled={loadingConfigs}
            value={mainId}
            onChange={(event) => setMainId(event.target.value)}
          >
            <option value="">Environment default</option>
            {configs.map((config) => (
              <option key={config.id} value={config.id} disabled={!config.enabled}>
                {formatConfigLabel(config)}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm font-bold text-gms-text">
          Guardrail LLM {isAdmin ? "" : "(admin managed)"}
          <select
            className="detail-input mt-2"
            disabled={loadingConfigs || !isAdmin}
            value={guardrailId}
            onChange={(event) => setGuardrailId(event.target.value)}
          >
            <option value="">Environment default</option>
            {configs.map((config) => (
              <option key={config.id} value={config.id} disabled={!config.enabled}>
                {formatConfigLabel(config)}
              </option>
            ))}
          </select>
        </label>
      </div>
      <p className="mt-4 text-xs text-gms-muted">
        {loadingConfigs
          ? "Loading saved LLM configurations..."
          : configs.length
          ? "Disabled configurations remain visible but cannot be newly selected."
          : "No saved configurations are available; environment defaults will be used."}
      </p>
      <div className="mt-7 flex flex-wrap items-center gap-4">
        <button
          className="inline-flex h-10 items-center gap-2 rounded-md bg-gms-blue px-5 text-sm font-semibold text-white shadow-button"
          type="button"
          onClick={handleSave}
        >
          <Save className="h-4 w-4" />
          Save LLM Settings
        </button>
        <button
          className="inline-flex h-10 items-center gap-2 rounded-md border border-gms-blue px-5 text-sm font-semibold text-gms-blue"
          type="button"
          onClick={() => setCreateOpen(true)}
        >
          <Plus className="h-4 w-4" />
          Add Configuration
        </button>
        {message && <p className="text-sm text-gms-muted">{message}</p>}
      </div>
      <CreateLlmConfigModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onSubmit={handleCreate}
      />
    </div>
  );
}

function formatConfigLabel(config: LlmConfig) {
  const status = config.enabled ? "" : " (disabled)";
  return `${config.name} - ${config.provider} - ${config.model_name}${status}`;
}
