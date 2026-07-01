"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Globe2, ShieldCheck } from "lucide-react";
import { PolicySummaryModal } from "@/components/policies/policy-summary-modal";
import {
  getEffectivePolicyAssignments,
  type ClientApp,
  type EffectivePolicyAssignment,
  type EffectivePolicyAssignmentsResponse
} from "@/lib/api-client";

const SELECTED_APP_STORAGE_KEY = "gms:selected-app";

export function AppPolicySummary({ app }: { app: ClientApp }) {
  const router = useRouter();
  const [summary, setSummary] = useState<EffectivePolicyAssignmentsResponse | null>(null);
  const [selectedPolicy, setSelectedPolicy] = useState<EffectivePolicyAssignment | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getEffectivePolicyAssignments(app.client_id)
      .then(setSummary)
      .catch((loadError) =>
        setError(loadError instanceof Error ? loadError.message : "Could not load policies.")
      );
  }, [app.client_id]);

  function managePolicies() {
    window.localStorage.setItem(SELECTED_APP_STORAGE_KEY, app.display_label);
    router.push("/policies");
  }

  return (
    <div>
      <div className="flex flex-col gap-5 md:flex-row md:items-start md:justify-between">
        <div>
          <h2 className="text-2xl font-extrabold text-gms-text">Effective Policies</h2>
          <p className="mt-2 text-sm text-gms-muted">
            Review mandatory global policies and policies assigned specifically to this app.
          </p>
        </div>
        <button
          className="inline-flex h-10 items-center gap-2 rounded-md bg-gms-blue px-5 text-sm font-semibold text-white shadow-button"
          type="button"
          onClick={managePolicies}
        >
          Manage Policies
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>

      {summary && (
        <>
          <div className="mt-8 grid gap-4 md:grid-cols-4">
            <Metric label="Global" value={summary.global_assignment_count} icon={<Globe2 />} />
            <Metric label="App-specific" value={summary.app_assignment_count} icon={<ShieldCheck />} />
            <Metric label="Enabled" value={summary.enabled_assignment_count} icon={<ShieldCheck />} />
            <Metric label="Disabled" value={summary.disabled_assignment_count} icon={<ShieldCheck />} />
          </div>
          <div className="mt-7 space-y-3">
            {[...summary.global_assignments, ...summary.app_assignments].map((assignment) => (
              <div
                key={`${assignment.scope}-${assignment.assignment_id}`}
                className="group grid min-h-[56px] cursor-pointer grid-cols-[110px_1fr_140px] items-center rounded-md border border-gms-line bg-white px-5 text-sm transition hover:border-gms-blue hover:bg-gms-blue hover:text-white dark:bg-[#20242c]"
                role="button"
                tabIndex={0}
                onClick={() => setSelectedPolicy(assignment)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    setSelectedPolicy(assignment);
                  }
                }}
              >
                <span className="font-semibold capitalize text-gms-blue group-hover:text-white">{assignment.scope}</span>
                <span>{assignment.display_name || assignment.policy_label}</span>
                <span className={`${assignment.enabled ? "text-[#3c8a58]" : "text-gms-muted"} group-hover:text-white`}>
                  {assignment.enabled ? "Enabled" : "Disabled"}
                </span>
              </div>
            ))}
          </div>
        </>
      )}
      {error && <p className="mt-4 text-sm text-gms-danger">{error}</p>}

      <PolicySummaryModal
        displayName={selectedPolicy?.display_name || selectedPolicy?.policy_label}
        open={selectedPolicy !== null}
        policyId={selectedPolicy?.policy_id ?? null}
        scope={selectedPolicy?.scope ?? null}
        onClose={() => setSelectedPolicy(null)}
      />
    </div>
  );
}

function Metric({ label, value, icon }: { label: string; value: number; icon: React.ReactNode }) {
  return (
    <div className="rounded-md border border-gms-line bg-[#f9fbff] p-5 dark:bg-[#20242c]">
      <div className="flex h-9 w-9 items-center justify-center rounded-md bg-gms-blue-soft text-gms-blue">
        {icon}
      </div>
      <p className="mt-4 text-3xl font-extrabold text-gms-text">{value}</p>
      <p className="mt-1 text-sm text-gms-muted">{label}</p>
    </div>
  );
}
