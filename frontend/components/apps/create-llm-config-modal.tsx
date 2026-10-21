"use client";

import { useMemo, useState } from "react";
import { Plus, X } from "lucide-react";
import { FormField } from "@/components/shared/form-field";
import { type AppMainModelCreatePayload, type LlmConfigCreatePayload } from "@/lib/api-client";

type CreateLlmConfigModalProps = {
  isAdmin: boolean;
  error?: string;
  onClose: () => void;
  onSubmit: (payload: AppMainModelCreatePayload) => Promise<boolean>;
  onSubmitManaged: (payload: LlmConfigCreatePayload) => Promise<boolean>;
};

export function CreateLlmConfigModal({
  isAdmin,
  error,
  onClose,
  onSubmit,
  onSubmitManaged
}: CreateLlmConfigModalProps) {
  const [provider, setProvider] = useState<"azure_openai" | "openai_compatible">("openai_compatible");
  const [name, setName] = useState("");
  const [modelName, setModelName] = useState("");
  const [endpoint, setEndpoint] = useState("");
  const [credentialEnvVar, setCredentialEnvVar] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [credentialSource, setCredentialSource] = useState<"api_key" | "backend">("api_key");
  const [submitting, setSubmitting] = useState(false);
  const managed = isAdmin && credentialSource === "backend";
  const endpointRequired = !managed || provider !== "azure_openai";

  const canCreate = useMemo(
    () => name.trim() && modelName.trim() && (!endpointRequired || endpoint.trim())
      && (managed ? provider === "azure_openai" || credentialEnvVar.trim() : apiKey.trim()),
    [name, modelName, endpointRequired, endpoint, managed, provider, credentialEnvVar, apiKey]
  );

  async function handleSubmit() {
    if (!canCreate || submitting) return;

    setSubmitting(true);
    try {
      const fields = { name: name.trim(), provider, model_name: modelName.trim() };
      const created = managed
        ? await onSubmitManaged({
          ...fields, endpoint: endpoint.trim() || null,
          credential_reference: credentialEnvVar.trim() ? `env:${credentialEnvVar.trim()}` : null,
          enabled: true
        })
        : await onSubmit({ ...fields, endpoint: endpoint.trim(), api_key: apiKey });
      if (created) onClose();
    } finally {
      setApiKey("");
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#171a22]/35 px-6 backdrop-blur-[2px]">
      <section role="dialog" aria-modal="true" aria-labelledby="model-profile-title" className="relative w-full max-w-[720px] rounded-[14px] bg-white px-8 pb-7 pt-16 shadow-modal dark:bg-[#20242c]">
        <button
          aria-label="Close create LLM configuration modal"
          className="absolute left-5 top-4 flex h-10 w-10 items-center justify-center rounded-xl bg-white text-gms-text shadow-[0_3px_12px_rgba(40,48,78,0.12)] dark:bg-[#2a2f39]"
          type="button"
          disabled={submitting}
          onClick={onClose}
        >
          <X className="h-4 w-4" />
        </button>

        <h2 id="model-profile-title" className="text-[22px] font-extrabold text-gms-text">
          Add model profile
        </h2>
        <p className="mt-2 text-sm text-gms-muted">
          {managed
            ? "Create a profile using backend credentials, then approve its main-agent or classifier access below."
            : "Add a model for this app’s main agent. Its API key is encrypted and cannot be viewed after saving."}
        </p>

        <FormField label="API Type:" className="mt-7" required>
          <select className="detail-input" value={provider}
            onChange={(event) => setProvider(event.target.value as typeof provider)}>
            <option value="azure_openai">Azure OpenAI</option>
            <option value="openai_compatible">Compatible API / Model Gateway</option>
          </select>
        </FormField>
        <div className="mt-7 grid gap-5 md:grid-cols-2">
          <FormField label="Profile Name:" required>
            <input
              className="detail-input"
              placeholder="Finance Bot GPT-4o"
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
          </FormField>
          <FormField label={provider === "azure_openai" ? "Deployment Name:" : "Model / Gateway Alias:"} required>
            <input
              className="detail-input"
              placeholder="gpt-4o-deployment"
              value={modelName}
              onChange={(event) => setModelName(event.target.value)}
            />
          </FormField>
        </div>

        <FormField label={provider === "azure_openai" ? "Azure Endpoint:" : "API Base URL:"} required={endpointRequired} className="mt-5">
          <input
            className="detail-input"
            placeholder={managed && provider === "azure_openai" ? "Uses the backend default when blank" : "https://llm-gateway.example.com/v1"}
            value={endpoint}
            onChange={(event) => setEndpoint(event.target.value)}
          />
        </FormField>

        {managed ? <FormField label="Credential Environment Variable:" className="mt-5" required={provider !== "azure_openai"}>
          <input
            className="detail-input font-mono text-xs"
            placeholder="FINANCE_BOT_AZURE_KEY"
            value={credentialEnvVar}
            onChange={(event) => setCredentialEnvVar(event.target.value)}
          />
          <p className="mt-2 text-xs font-normal text-gms-muted">
            {provider === "azure_openai"
              ? "Enter only the variable name. Leave blank to use AZURE_OPENAI_API_KEY."
              : "Enter the approved backend variable name for this service. Do not enter a key value."}
          </p>
        </FormField> : <FormField label="Provider API key:" className="mt-5" required>
          <input className="detail-input" type="password" autoComplete="new-password"
            value={apiKey} maxLength={8192} disabled={submitting}
            onChange={(event) => setApiKey(event.target.value)} />
          <p className="mt-2 text-xs font-normal text-gms-muted">
            Available only to this app’s main agent. Use a destination enabled by your GMS administrator.
          </p>
        </FormField>}

        {isAdmin && <details className="mt-5 text-sm text-gms-text">
          <summary className="cursor-pointer font-semibold">Advanced credentials</summary>
          <label className="mt-3 flex items-center gap-2">
            <input type="checkbox" checked={managed} disabled={submitting}
              onChange={(event) => {
                setCredentialSource(event.target.checked ? "backend" : "api_key");
                setApiKey("");
                setCredentialEnvVar("");
              }} />
            Use a backend-managed credential
          </label>
          <p className="mt-2 text-xs text-gms-muted">
            Use a key already configured on the backend for an admin-managed main-agent or classifier profile.
          </p>
        </details>}

        {error && <p role="alert" className="mt-4 text-sm text-gms-danger">{error}</p>}
        <div className="mt-8 flex justify-end">
          <button
            className="inline-flex h-10 items-center gap-2 rounded-md bg-gms-blue px-5 text-sm font-semibold text-white shadow-button disabled:opacity-50"
            disabled={!canCreate || submitting}
            type="button"
            onClick={handleSubmit}
          >
            <Plus className="h-4 w-4" />
            {submitting ? "Creating..." : "Add model profile"}
          </button>
        </div>
      </section>
    </div>
  );
}
