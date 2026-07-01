"use client";

import { useEffect, useMemo, useState } from "react";
import { Copy, Eye, EyeOff, KeyRound, Plus, X } from "lucide-react";
import { FormField } from "@/components/shared/form-field";

export type AppDraft = {
  name: string;
  clientId: string;
  apiKey: string;
};

type CreateAppModalProps = {
  open: boolean;
  onClose: () => void;
  onSubmit: (draft: AppDraft) => Promise<boolean>;
};

export function CreateAppModal({
  open,
  onClose,
  onSubmit
}: CreateAppModalProps) {
  const [name, setName] = useState("");
  const [clientId, setClientId] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!open) {
      setName("");
      setClientId("");
      setApiKey("");
      setShowKey(false);
    }
  }, [open]);

  const canCreate = useMemo(
    () => name.trim() && clientId.trim() && apiKey.length >= 16,
    [apiKey.length, clientId, name]
  );

  if (!open) {
    return null;
  }

  function generateApiKey() {
    const value = `gms_${crypto.randomUUID().replace(/-/g, "")}`;
    setApiKey(value);
    setShowKey(true);
  }

  async function handleSubmit() {
    if (!canCreate || submitting) {
      return;
    }
    setSubmitting(true);
    await onSubmit({
      name: name.trim(),
      clientId: clientId.trim(),
      apiKey
    });
    setSubmitting(false);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#171a22]/35 px-6 backdrop-blur-[2px]">
      <section className="relative w-full max-w-[720px] rounded-[14px] bg-white px-8 pb-7 pt-16 shadow-modal dark:bg-[#20242c]">
        <button
          aria-label="Close create app modal"
          className="absolute left-5 top-4 flex h-10 w-10 items-center justify-center rounded-xl bg-white text-gms-text shadow-[0_3px_12px_rgba(40,48,78,0.12)] dark:bg-[#2a2f39]"
          type="button"
          onClick={onClose}
        >
          <X className="h-4 w-4" />
        </button>

        <h2 className="text-[22px] font-extrabold text-gms-text">
          Create Application:
        </h2>
        <p className="mt-2 text-sm text-gms-muted">
          Register an application that will send guarded requests through GMS.
        </p>

        <div className="mt-7 grid gap-5 md:grid-cols-2">
          <FormField label="Application Name:" required>
            <input
              className="h-11 w-full rounded border border-gms-blue bg-white px-3 text-sm text-gms-text outline-none placeholder:text-[#a9bdff] dark:bg-[#252932]"
              placeholder="Finance Bot"
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
          </FormField>
          <FormField label="Client ID:" required>
            <input
              className="h-11 w-full rounded border border-gms-blue bg-white px-3 text-sm text-gms-text outline-none placeholder:text-[#a9bdff] dark:bg-[#252932]"
              placeholder="finance-bot"
              value={clientId}
              onChange={(event) => setClientId(event.target.value)}
            />
          </FormField>
        </div>

        <FormField label="API Key:" required className="mt-5">
          <div className="flex gap-2">
            <div className="relative min-w-0 flex-1">
              <KeyRound className="absolute left-3 top-3 h-5 w-5 text-gms-muted" />
              <input
                className="h-11 w-full rounded border border-gms-blue bg-white px-10 pr-12 text-sm text-gms-text outline-none placeholder:text-[#a9bdff] dark:bg-[#252932]"
                minLength={16}
                placeholder="Minimum 16 characters"
                type={showKey ? "text" : "password"}
                value={apiKey}
                onChange={(event) => setApiKey(event.target.value)}
              />
              <button
                aria-label={showKey ? "Hide API key" : "Show API key"}
                className="absolute right-3 top-3 text-gms-muted hover:text-gms-blue"
                type="button"
                onClick={() => setShowKey((current) => !current)}
              >
                {showKey ? (
                  <EyeOff className="h-5 w-5" />
                ) : (
                  <Eye className="h-5 w-5" />
                )}
              </button>
            </div>
            <button
              className="rounded-md border border-gms-blue px-4 text-sm font-semibold text-gms-blue hover:bg-gms-blue-soft"
              type="button"
              onClick={generateApiKey}
            >
              Generate
            </button>
            <button
              aria-label="Copy API key"
              className="flex h-11 w-11 items-center justify-center rounded-md border border-gms-line text-gms-muted hover:text-gms-blue"
              disabled={!apiKey}
              type="button"
              onClick={() => navigator.clipboard.writeText(apiKey)}
            >
              <Copy className="h-4 w-4" />
            </button>
          </div>
          <p className="mt-2 text-xs font-normal text-gms-muted">
            Store this key securely. GMS saves only its hash and cannot display
            it again.
          </p>
        </FormField>

        <div className="mt-8 flex justify-end">
          <button
            className="inline-flex h-10 items-center gap-3 rounded-md bg-gms-blue px-5 text-sm font-medium text-white shadow-button disabled:opacity-50"
            disabled={!canCreate || submitting}
            type="button"
            onClick={handleSubmit}
          >
            <Plus className="h-4 w-4" />
            {submitting ? "Creating..." : "Create App"}
          </button>
        </div>
      </section>
    </div>
  );
}
