"use client";

import { useState } from "react";
import { CreatePolicyModal, type PolicyDraft } from "@/components/policies/create-policy-modal";
import { mockPolicyOptions } from "@/lib/mock-data";

export default function PolicyPreviewPage() {
  const [open, setOpen] = useState(true);
  const [saved, setSaved] = useState<PolicyDraft | null>(null);

  return (
    <main className="min-h-screen bg-gms-bg p-6 text-gms-text">
      <section className="mx-auto max-w-3xl rounded-xl border border-gms-line bg-white p-6 dark:bg-[#20242c]">
        <h1 className="text-2xl font-bold">Policy authoring preview</h1>
        <p className="mt-2 text-sm text-gms-muted">
          Local UI prototype. No login, database, live AI, or GitHub connection.
          Created drafts stay in this page until it is refreshed.
        </p>
        {saved && (
          <div role="status" className="mt-4 space-y-2 rounded-lg border border-gms-line p-4">
            <h2 className="font-bold">Mock policy created: {saved.name}</h2>
            <p>{saved.policyType === "input"
              ? `${saved.connector} → ${saved.action} → ${saved.resource}`
              : "Output policy"}</p>
            <p className="break-words">{saved.policyType === "input" ? saved.customResource : saved.outputRule}</p>
          </div>
        )}
        <button type="button" className="mt-4 rounded-md bg-gms-blue px-4 py-2 text-white" onClick={() => setOpen(true)}>
          Create preview policy
        </button>
      </section>
      <CreatePolicyModal open={open} appName="Preview app" policyOptions={mockPolicyOptions}
        enableLiveAssistant={false}
        onClose={() => setOpen(false)}
        onSubmit={(draft) => {
          setSaved(draft);
          setOpen(false);
          return true;
        }}
      />
    </main>
  );
}
