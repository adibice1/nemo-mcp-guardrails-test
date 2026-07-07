"use client";

import { useEffect, useMemo, useState } from "react";
import { Copy, KeyRound, Plus, X } from "lucide-react";
import { FormField } from "@/components/shared/form-field";

export type AppDraft = {
  name: string;
  clientId: string;
};

export type CreatedAppSecret = {
  name: string;
  apiKey: string;
  notice: string;
};

type CreateAppModalProps = {
  open: boolean;
  onClose: () => void;
  onSubmit: (draft: AppDraft) => Promise<CreatedAppSecret | null>;
};

export function CreateAppModal({
  open,
  onClose,
  onSubmit
}: CreateAppModalProps) {
  const [name, setName] = useState("");
  const [clientId, setClientId] = useState("");
  const [createdSecret, setCreatedSecret] = useState<CreatedAppSecret | null>(null);
  const [copied, setCopied] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!open) {
      setName("");
      setClientId("");
      setCreatedSecret(null);
      setCopied(false);
    }
  }, [open]);

  const canCreate = useMemo(
    () => name.trim() && clientId.trim() && !createdSecret,
    [clientId, createdSecret, name]
  );

  if (!open) {
    return null;
  }

  async function handleSubmit() {
    if (!canCreate || submitting) {
      return;
    }
    setSubmitting(true);
    const result = await onSubmit({
      name: name.trim(),
      clientId: clientId.trim()
    });
    if (result) {
      setCreatedSecret(result);
    }
    setSubmitting(false);
  }

  async function handleCopyApiKey() {
    if (!createdSecret) {
      return;
    }
    await navigator.clipboard.writeText(createdSecret.apiKey);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
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
              disabled={Boolean(createdSecret)}
              placeholder="Finance Bot"
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
          </FormField>
          <FormField label="Client ID:" required>
            <input
              className="h-11 w-full rounded border border-gms-blue bg-white px-3 text-sm text-gms-text outline-none placeholder:text-[#a9bdff] dark:bg-[#252932]"
              disabled={Boolean(createdSecret)}
              placeholder="finance-bot"
              value={clientId}
              onChange={(event) => setClientId(event.target.value)}
            />
          </FormField>
        </div>

        {createdSecret ? (
          <div className="mt-6 rounded-xl border border-[#9bb5ff] bg-[#f4f7ff] p-5 dark:border-[#4d66a8] dark:bg-[#202b45]">
            <div className="flex items-center gap-3 text-gms-blue">
              <KeyRound className="h-5 w-5" />
              <p className="text-sm font-extrabold">API key generated</p>
            </div>
            <p className="mt-2 text-xs text-gms-muted">{createdSecret.notice}</p>
            <div className="mt-4 flex gap-2">
              <input
                className="h-11 min-w-0 flex-1 rounded border border-gms-blue bg-white px-3 font-mono text-xs text-gms-text outline-none dark:bg-[#252932]"
                readOnly
                value={createdSecret.apiKey}
              />
              <button
                aria-label="Copy generated API key"
                className="inline-flex h-11 min-w-[96px] items-center justify-center gap-2 rounded-md bg-gms-blue px-4 text-sm font-semibold text-white shadow-button"
                type="button"
                onClick={handleCopyApiKey}
              >
                <Copy className="h-4 w-4" />
                {copied ? "Copied!" : "Copy"}
              </button>
            </div>
          </div>
        ) : (
          <p className="mt-6 rounded-xl border border-gms-line bg-[#f7f9ff] p-4 text-sm text-gms-muted dark:bg-[#20242c]">
            GMS will generate a secure API key after creation. Copy it before
            closing this dialog because it will not be shown again.
          </p>
        )}

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
