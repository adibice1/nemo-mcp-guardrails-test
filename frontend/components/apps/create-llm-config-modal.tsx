"use client";

import { useEffect, useMemo, useState } from "react";
import { Plus, X } from "lucide-react";
import { FormField } from "@/components/shared/form-field";
import { type LlmConfigCreatePayload } from "@/lib/api-client";

type CreateLlmConfigModalProps = {
  open: boolean;
  onClose: () => void;
  onSubmit: (payload: LlmConfigCreatePayload) => Promise<boolean>;
};

export function CreateLlmConfigModal({
  open,
  onClose,
  onSubmit
}: CreateLlmConfigModalProps) {
  const [name, setName] = useState("");
  const [modelName, setModelName] = useState("");
  const [endpoint, setEndpoint] = useState("");
  const [credentialEnvVar, setCredentialEnvVar] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!open) {
      setName("");
      setModelName("");
      setEndpoint("");
      setCredentialEnvVar("");
    }
  }, [open]);

  const canCreate = useMemo(
    () => name.trim() && modelName.trim(),
    [modelName, name]
  );

  if (!open) return null;

  async function handleSubmit() {
    if (!canCreate || submitting) return;

    setSubmitting(true);
    const created = await onSubmit({
      name: name.trim(),
      provider: "azure_openai",
      model_name: modelName.trim(),
      endpoint: endpoint.trim() || null,
      credential_reference: credentialEnvVar.trim()
        ? `env:${credentialEnvVar.trim()}`
        : null,
      enabled: true
    });
    setSubmitting(false);
    if (created) onClose();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#171a22]/35 px-6 backdrop-blur-[2px]">
      <section className="relative w-full max-w-[720px] rounded-[14px] bg-white px-8 pb-7 pt-16 shadow-modal dark:bg-[#20242c]">
        <button
          aria-label="Close create LLM configuration modal"
          className="absolute left-5 top-4 flex h-10 w-10 items-center justify-center rounded-xl bg-white text-gms-text shadow-[0_3px_12px_rgba(40,48,78,0.12)] dark:bg-[#2a2f39]"
          type="button"
          onClick={onClose}
        >
          <X className="h-4 w-4" />
        </button>

        <h2 className="text-[22px] font-extrabold text-gms-text">
          Add Azure LLM Configuration:
        </h2>
        <p className="mt-2 text-sm text-gms-muted">
          Save deployment metadata and reference a key already configured on the backend.
        </p>

        <div className="mt-7 grid gap-5 md:grid-cols-2">
          <FormField label="Configuration Name:" required>
            <input
              className="detail-input"
              placeholder="Finance Bot GPT-4o"
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
          </FormField>
          <FormField label="Deployment Name:" required>
            <input
              className="detail-input"
              placeholder="gpt-4o-deployment"
              value={modelName}
              onChange={(event) => setModelName(event.target.value)}
            />
          </FormField>
        </div>

        <FormField label="Azure Endpoint:" className="mt-5">
          <input
            className="detail-input"
            placeholder="Uses the backend default when blank"
            value={endpoint}
            onChange={(event) => setEndpoint(event.target.value)}
          />
        </FormField>

        <FormField label="Credential Environment Variable:" className="mt-5">
          <input
            className="detail-input font-mono text-xs"
            placeholder="FINANCE_BOT_AZURE_KEY"
            value={credentialEnvVar}
            onChange={(event) => setCredentialEnvVar(event.target.value)}
          />
          <p className="mt-2 text-xs font-normal text-gms-muted">
            Enter only the variable name. Leave blank to use AZURE_OPENAI_API_KEY.
          </p>
        </FormField>

        <div className="mt-8 flex justify-end">
          <button
            className="inline-flex h-10 items-center gap-2 rounded-md bg-gms-blue px-5 text-sm font-semibold text-white shadow-button disabled:opacity-50"
            disabled={!canCreate || submitting}
            type="button"
            onClick={handleSubmit}
          >
            <Plus className="h-4 w-4" />
            {submitting ? "Creating..." : "Add Configuration"}
          </button>
        </div>
      </section>
    </div>
  );
}
