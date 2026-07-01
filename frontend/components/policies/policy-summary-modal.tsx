"use client";

import { useEffect, useState } from "react";
import { Blocks, X } from "lucide-react";
import { getPolicy, type PolicyRecord } from "@/lib/api-client";

type PolicySummaryModalProps = {
  open: boolean;
  policyId: number | null;
  displayName?: string | null;
  scope?: "app" | "global" | null;
  onClose: () => void;
};

export function PolicySummaryModal({
  open,
  policyId,
  displayName,
  scope,
  onClose
}: PolicySummaryModalProps) {
  const [policy, setPolicy] = useState<PolicyRecord | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) {
      setPolicy(null);
      setError("");
      return;
    }

    if (policyId === null) {
      setPolicy(null);
      setError("Detailed policy structure is available in backend mode.");
      return;
    }

    let active = true;
    getPolicy(policyId)
      .then((record) => {
        if (active) {
          setPolicy(record);
          setError("");
        }
      })
      .catch((loadError) => {
        if (active) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Could not load policy details."
          );
        }
      });

    return () => {
      active = false;
    };
  }, [open, policyId]);

  if (!open) {
    return null;
  }

  const customResource = policy?.conditions?.custom_resource;
  const policyName =
    displayName?.trim() || policy?.description?.trim() || "Policy Summary";

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center bg-[#171a22]/35 px-6 backdrop-blur-[2px]">
      <section className="relative w-full max-w-[720px] rounded-[14px] bg-white px-8 pb-8 pt-16 shadow-modal dark:bg-[#20242c]">
        <button
          aria-label="Close policy summary"
          className="absolute left-5 top-4 flex h-10 w-10 items-center justify-center rounded-xl bg-white text-gms-text shadow-[0_3px_12px_rgba(40,48,78,0.12)] dark:bg-[#2a2f39]"
          type="button"
          onClick={onClose}
        >
          <X className="h-4 w-4" />
        </button>

        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="text-sm font-semibold text-gms-blue">Policy Summary</p>
            <h2 className="mt-1 text-2xl font-extrabold text-gms-text">
              {policyName}
            </h2>
          </div>
          {scope && (
            <span className="inline-flex min-h-10 min-w-[126px] items-center justify-center whitespace-nowrap rounded-full bg-gms-blue-soft px-4 py-2 text-center text-xs font-semibold capitalize text-gms-blue">
              {scope === "global" ? "Global policy" : "App-specific policy"}
            </span>
          )}
        </div>

        {!policy && !error && (
          <p className="mt-8 text-sm text-gms-muted">Loading policy details...</p>
        )}

        {policy && (
          <div className="mt-8">
            <div className="grid gap-4 sm:grid-cols-3">
              <SummaryField label="Connector" value={toDisplayValue(policy.connector)} />
              <SummaryField label="Action" value={toDisplayValue(policy.action)} />
              <SummaryField label="Resource Type" value={toDisplayValue(policy.resource)} />
            </div>

            <div className="mt-5 rounded-md border border-gms-line bg-[#f9fbff] p-5 dark:bg-[#252932]">
              <div className="flex items-start gap-4">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-gms-blue-soft text-gms-blue">
                  <Blocks className="h-5 w-5" />
                </span>
                <div>
                  <p className="text-xs font-semibold uppercase text-gms-muted">
                    Custom Resource
                  </p>
                  <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-gms-text">
                    {typeof customResource === "string" && customResource.trim()
                      ? customResource
                      : "Any resource"}
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-5 grid gap-4 sm:grid-cols-3">
              <SummaryField label="Policy Type" value={toDisplayValue(policy.policy_type)} />
              <SummaryField label="Effect" value={toDisplayValue(policy.effect)} />
              <SummaryField label="Status" value={policy.enabled ? "Enabled" : "Disabled"} />
            </div>
          </div>
        )}

        {error && <p className="mt-8 text-sm text-gms-danger">{error}</p>}
      </section>
    </div>
  );
}

function SummaryField({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-gms-line bg-white p-4 dark:bg-[#252932]">
      <p className="text-xs font-semibold uppercase text-gms-muted">{label}</p>
      <p className="mt-2 text-sm font-semibold text-gms-text">{value}</p>
    </div>
  );
}

function toDisplayValue(value: string | null | undefined) {
  if (!value) {
    return "Not specified";
  }
  if (value.toLowerCase() === "github") {
    return "GitHub";
  }
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
