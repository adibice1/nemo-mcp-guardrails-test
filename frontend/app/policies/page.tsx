"use client";

import { useEffect, useMemo, useState } from "react";
import { ChevronDown, Plus, Search, X } from "lucide-react";
import {
  CreatePolicyModal,
  type PolicyDraft
} from "@/components/policies/create-policy-modal";
import { PolicyTable, type PolicySort } from "@/components/policies/policy-table";
import { PolicySummaryModal } from "@/components/policies/policy-summary-modal";
import { AppTopNav } from "@/components/shared/app-top-nav";
import {
  deleteAppPolicyAssignment,
  deleteGlobalPolicyAssignment,
  editAppPolicyAssignment,
  editGlobalPolicyAssignment,
  getEffectivePolicyAssignments,
  hasApiBaseUrl,
  listApps,
  listGlobalPolicyAssignments,
  listPolicyOptions,
  listPolicies,
  resolvePolicyForApp,
  resolvePolicyGlobally,
  type ClientApp,
  type EffectivePolicyAssignment,
  type GlobalPolicyAssignment,
  type PolicyConnectorOption,
  type PolicyRecord
} from "@/lib/api-client";
import {
  appOptions,
  initialPolicies,
  mockPolicyOptions,
  type PolicyRow
} from "@/lib/mock-data";
import { loadManagementSession } from "@/lib/management-auth";

const SELECTED_APP_STORAGE_KEY = "gms:selected-app";
const PAGE_SIZE = 8;
type ApiStatus = "mock" | "loading" | "ready" | "error";
type Notice = {
  tone: "success" | "warning";
  message: string;
};

export default function PoliciesPage() {
  const [selectedApp, setSelectedApp] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [editingPolicy, setEditingPolicy] = useState<PolicyRow | null>(null);
  const [summaryPolicy, setSummaryPolicy] = useState<PolicyRow | null>(null);
  const [policies, setPolicies] = useState<PolicyRow[]>(initialPolicies);
  const [apps, setApps] = useState<ClientApp[]>([]);
  const [globalAssignments, setGlobalAssignments] = useState<
    GlobalPolicyAssignment[]
  >([]);
  const [policyDefinitions, setPolicyDefinitions] = useState<PolicyRecord[]>([]);
  const [policyOptions, setPolicyOptions] = useState<PolicyConnectorOption[]>(
    mockPolicyOptions
  );
  const [apiStatus, setApiStatus] = useState<ApiStatus>(
    hasApiBaseUrl() ? "loading" : "mock"
  );
  const [backendLoaded, setBackendLoaded] = useState(!hasApiBaseUrl());
  const [apiError, setApiError] = useState("");
  const [notice, setNotice] = useState<Notice | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState<PolicySort>({
    key: "created",
    direction: "desc"
  });

  useEffect(() => {
    setIsAdmin(loadManagementSession()?.user.system_role === "admin");
    const savedApp = window.localStorage.getItem(SELECTED_APP_STORAGE_KEY);
    if (savedApp !== null) {
      setSelectedApp(savedApp);
    }
  }, []);

  useEffect(() => {
    if (!hasApiBaseUrl()) {
      return;
    }

    async function loadInitialData() {
      try {
        setApiStatus("loading");
        setApiError("");
        const [
          nextApps,
          nextGlobalAssignments,
          nextPolicyDefinitions,
          nextPolicyOptions
        ] =
          await Promise.all([
          listApps(),
          listGlobalPolicyAssignments(),
          listPolicies(),
          listPolicyOptions()
        ]);
        setApps(nextApps);
        setGlobalAssignments(nextGlobalAssignments);
        setPolicyDefinitions(nextPolicyDefinitions);
        setPolicyOptions(
          nextPolicyOptions.filter(
            (option) => option.value.toLowerCase() === "github"
          )
        );
        if (
          selectedApp &&
          !nextApps.some((app) => app.display_label === selectedApp)
        ) {
          setSelectedApp("");
          window.localStorage.setItem(SELECTED_APP_STORAGE_KEY, "");
        }
        setPolicies(
          nextGlobalAssignments.map((assignment) =>
            mapGlobalAssignmentToPolicyRow(assignment, nextPolicyDefinitions)
          )
        );
        setApiStatus("ready");
        setBackendLoaded(true);
      } catch (error) {
        setApiStatus("error");
        setBackendLoaded(true);
        setApiError(
          error instanceof Error ? error.message : "Could not load backend data."
        );
        setPolicies(initialPolicies);
      }
    }

    void loadInitialData();
  }, []);

  useEffect(() => {
    if (!hasApiBaseUrl()) {
      return;
    }

    if (!selectedApp) {
      setPolicies(
        globalAssignments.map((assignment) =>
          mapGlobalAssignmentToPolicyRow(assignment, policyDefinitions)
        )
      );
      return;
    }

    const selectedAppRecord = apps.find(
      (app) => app.display_label === selectedApp
    );
    if (!selectedAppRecord) {
      if (!backendLoaded) {
        return;
      }
      setSelectedApp("");
      window.localStorage.setItem(SELECTED_APP_STORAGE_KEY, "");
      return;
    }

    async function loadAppPolicies(app: ClientApp) {
      try {
        setApiStatus("loading");
        setApiError("");
        setPolicies([]);
        const effective = await getEffectivePolicyAssignments(app.client_id);
        setPolicies([
          ...effective.global_assignments.map((assignment) =>
            mapEffectiveAssignmentToPolicyRow(
              assignment,
              policyDefinitions
            )
          ),
          ...effective.app_assignments.map((assignment) =>
            mapEffectiveAssignmentToPolicyRow(
              assignment,
              policyDefinitions,
              app.display_label
            )
          )
        ]);
        setApiStatus("ready");
      } catch (error) {
        setApiStatus("error");
        setApiError(
          error instanceof Error ? error.message : "Could not load app policies."
        );
      }
    }

    void loadAppPolicies(selectedAppRecord);
  }, [apps, backendLoaded, globalAssignments, policyDefinitions, selectedApp]);

  async function reloadPolicyData() {
    const [nextApps, nextGlobalAssignments, nextPolicyDefinitions] =
      await Promise.all([
        listApps(),
        listGlobalPolicyAssignments(),
        listPolicies()
      ]);

    setApps(nextApps);
    setGlobalAssignments(nextGlobalAssignments);
    setPolicyDefinitions(nextPolicyDefinitions);

    const app = nextApps.find((item) => item.display_label === selectedApp);
    if (selectedApp && app) {
      const effective = await getEffectivePolicyAssignments(app.client_id);
      setPolicies([
        ...effective.global_assignments.map((assignment) =>
          mapEffectiveAssignmentToPolicyRow(assignment, nextPolicyDefinitions)
        ),
        ...effective.app_assignments.map((assignment) =>
          mapEffectiveAssignmentToPolicyRow(
            assignment,
            nextPolicyDefinitions,
            app.display_label
          )
        )
      ]);
    } else {
      setPolicies(
        nextGlobalAssignments.map((assignment) =>
          mapGlobalAssignmentToPolicyRow(assignment, nextPolicyDefinitions)
        )
      );
    }
  }

  async function handleCreatePolicy(draft: PolicyDraft): Promise<boolean> {
    if (!hasApiBaseUrl()) {
      setPolicies((current) => [
        {
          id: Date.now(),
          connector:
            draft.policyType === "output"
              ? "Output"
              : policyOptions.find(
                  (option) => option.value === draft.connector
                )?.label ?? draft.connector,
          name: draft.name,
          created: new Date().toISOString(),
          global: draft.global,
          app: draft.global ? null : selectedApp
        },
        ...current
      ]);
      setModalOpen(false);
      return true;
    }

    const app = apps.find((item) => item.display_label === selectedApp);
    if (!draft.global && !app) {
      showWarning("Select an app before creating an app-specific policy.");
      return false;
    }

    try {
      setApiStatus("loading");
      setApiError("");
      setNotice(null);
      const payload = buildPolicyPayload(draft);
      const resolution = draft.global
        ? await resolvePolicyGlobally(payload, draft.name)
        : await resolvePolicyForApp(app!.client_id, payload, draft.name);

      setNotice({
        tone:
          resolution.resolution === "already_assigned" ? "warning" : "success",
        message:
          resolution.resolution === "already_assigned"
            ? `${draft.name} is already active for this policy scope.`
            : `${draft.name} was created.`
      });
    } catch (error) {
      showWarning(
        error instanceof Error ? error.message : "Could not create policy."
      );
      return false;
    }

    try {
      await reloadPolicyData();
      setApiStatus("ready");
    } catch (error) {
      showWarning(
        error instanceof Error
          ? error.message
          : "Policy was created, but the list could not be refreshed."
      );
    }

    setModalOpen(false);
    return true;
  }

  function handleEditPolicy(policy: PolicyRow) {
    if (policy.scope === "global" && selectedApp) {
      setNotice({
        tone: "warning",
        message: "Switch to Global policies to edit a global assignment."
      });
      return;
    }
    setEditingPolicy(policy);
    setModalOpen(true);
  }

  async function handleUpdatePolicy(draft: PolicyDraft): Promise<boolean> {
    if (!editingPolicy) {
      return false;
    }

    if (!hasApiBaseUrl()) {
      setPolicies((current) =>
        current.map((policy) =>
          policy.id === editingPolicy.id
            ? {
                ...policy,
                connector: draft.connector,
                name: draft.name,
                global: editingPolicy.global
              }
            : policy
        )
      );
      setEditingPolicy(null);
      setModalOpen(false);
      return true;
    }

    if (
      editingPolicy.assignmentId === undefined ||
      editingPolicy.scope === undefined
    ) {
      showWarning("This policy row is missing assignment information.");
      return false;
    }

    const payload = buildPolicyPayload(draft);
    try {
      setApiStatus("loading");
      setApiError("");
      setNotice(null);
      const resolution =
        editingPolicy.scope === "global"
          ? await editGlobalPolicyAssignment(
              editingPolicy.assignmentId,
              payload,
              draft.name
            )
          : await editAppPolicyAssignment(
              getSelectedApp(apps, selectedApp).client_id,
              editingPolicy.assignmentId,
              payload,
              draft.name
            );

      await reloadPolicyData();
      setApiStatus("ready");
      setNotice({
        tone: "success",
        message: `${draft.name} was edited.`
      });
      setEditingPolicy(null);
      setModalOpen(false);
      return true;
    } catch (error) {
      showWarning(
        error instanceof Error ? error.message : "Could not update policy."
      );
      return false;
    }
  }

  async function handleDeletePolicy(policy: PolicyRow) {
    if (!hasApiBaseUrl()) {
      setPolicies((current) => current.filter((item) => item.id !== policy.id));
      setNotice({
        tone: "success",
        message: `${policy.name} was removed from the mock policy view.`
      });
      return;
    }

    if (policy.assignmentId === undefined || policy.scope === undefined) {
      showWarning("This policy row is missing assignment information.");
      return;
    }

    if (policy.scope === "global" && selectedApp) {
      setNotice({
        tone: "warning",
        message: "Switch to Global policies to remove a global assignment."
      });
      return;
    }

    const scopeLabel = policy.scope === "global" ? "every app" : selectedApp;
    const confirmed = window.confirm(
      `Remove "${policy.name}" from ${scopeLabel}? ` +
        "The reusable policy definition will remain in the database."
    );
    if (!confirmed) {
      return;
    }

    try {
      setApiStatus("loading");
      setApiError("");
      setNotice(null);
      if (policy.scope === "global") {
        await deleteGlobalPolicyAssignment(policy.assignmentId);
      } else {
        const app = apps.find((item) => item.display_label === selectedApp);
        if (!app) {
          throw new Error("Selected app was not found.");
        }
        await deleteAppPolicyAssignment(app.client_id, policy.assignmentId);
      }
      await reloadPolicyData();
      setApiStatus("ready");
      setNotice({
        tone: "success",
        message: `${policy.name} was deleted.`
      });
    } catch (error) {
      showWarning(
        error instanceof Error ? error.message : "Could not unassign policy."
      );
    }
  }

  function showWarning(message: string) {
    setApiStatus("ready");
    setApiError("");
    setNotice({ tone: "warning", message });
  }

  function handleSelectedAppChange(value: string) {
    setSelectedApp(value);
    setPolicies([]);
    setPage(1);
    window.localStorage.setItem(SELECTED_APP_STORAGE_KEY, value);
  }

  function handleSort(nextKey: PolicySort["key"]) {
    setSort((current) => ({
      key: nextKey,
      direction:
        current.key === nextKey && current.direction === "desc" ? "asc" : "desc"
    }));
    setPage(1);
  }

  const visiblePolicies = useMemo(() => {
    const scoped = selectedApp
      ? policies.filter((policy) => policy.global || policy.app === selectedApp)
      : policies.filter((policy) => policy.global);

    const filtered = search.trim()
      ? scoped.filter((policy) => {
          const needle = search.trim().toLowerCase();
          return (
            policy.name.toLowerCase().includes(needle) ||
            policy.connector.toLowerCase().includes(needle)
          );
        })
      : scoped;

    return [...filtered].sort((first, second) => {
      if (sort.key === "global") {
        const firstValue = first.global ? 1 : 0;
        const secondValue = second.global ? 1 : 0;
        return sort.direction === "asc"
          ? firstValue - secondValue
          : secondValue - firstValue;
      }

      const firstTime = new Date(first.created).getTime();
      const secondTime = new Date(second.created).getTime();
      return sort.direction === "asc"
        ? firstTime - secondTime
        : secondTime - firstTime;
    });
  }, [policies, search, selectedApp, sort]);

  const totalPages = Math.max(1, Math.ceil(visiblePolicies.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const appSelectOptions =
    hasApiBaseUrl() ? apps.map((app) => app.display_label) : appOptions;
  const paginatedPolicies = visiblePolicies.slice(
    (safePage - 1) * PAGE_SIZE,
    safePage * PAGE_SIZE
  );

  useEffect(() => {
    if (page > totalPages) {
      setPage(totalPages);
    }
  }, [page, totalPages]);

  return (
    <main className="min-h-screen bg-gms-bg px-6 py-8 lg:px-20">
      <AppTopNav active="policies" />

      <section className="mx-auto mt-4 min-h-[calc(100vh-112px)] max-w-[1480px] rounded-[24px] bg-white px-8 py-12 shadow-shell transition-colors dark:bg-[#1b1e25] lg:px-20">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h1 className="text-4xl font-extrabold tracking-normal text-gms-text lg:text-[42px]">
              Policies
            </h1>
            <p className="mt-3 max-w-2xl text-sm text-gms-muted">
              Create and manage app-specific or global guardrail policies for
              GitHub MCP runtime requests.
            </p>

            <div className="relative mt-12 w-[210px]">
              <label className="text-xs font-semibold uppercase tracking-wide text-gms-text">
                Apps
              </label>
              <select
                className="mt-2 h-9 w-full appearance-none border-b border-gms-line bg-transparent pr-8 text-sm text-gms-text outline-none dark:[color-scheme:dark]"
                value={selectedApp}
                onChange={(event) => handleSelectedAppChange(event.target.value)}
              >
                <option value="">Global policies</option>
                {appSelectOptions.map((app) => (
                  <option key={app} value={app}>
                    {app}
                  </option>
                ))}
              </select>
              <ChevronDown className="pointer-events-none absolute bottom-2 right-2 h-4 w-4 text-[#c0c8d7]" />
            </div>
          </div>

          <div className="flex flex-col items-stretch gap-9 lg:items-end">
            <label className="relative block w-full lg:w-[405px]">
              <input
                className="h-11 w-full rounded-xl border border-gms-line bg-white px-4 pr-11 text-sm text-gms-text shadow-field outline-none placeholder:text-gms-muted dark:bg-[#252932]"
                placeholder="Search"
                value={search}
                onChange={(event) => {
                  setSearch(event.target.value);
                  setPage(1);
                }}
              />
              <Search className="absolute right-5 top-3 h-5 w-5 text-gms-text" />
            </label>

            <button
              className="inline-flex h-10 w-full items-center justify-center gap-3 rounded-md bg-gms-blue px-4 text-sm font-medium text-white shadow-button lg:w-[170px]"
              type="button"
              onClick={() => {
                setEditingPolicy(null);
                setModalOpen(true);
              }}
            >
              <Plus className="h-5 w-5" />
              Create Policy
            </button>
          </div>
        </div>

        <PolicyTable
          page={safePage}
          pageSize={PAGE_SIZE}
          policies={paginatedPolicies}
          sort={sort}
          totalCount={visiblePolicies.length}
          onDelete={handleDeletePolicy}
          onEdit={handleEditPolicy}
          onOpen={setSummaryPolicy}
          onPageChange={setPage}
          onSort={handleSort}
        />

        {apiStatus === "loading" && (
          <p className="mt-3 text-xs text-gms-muted">
            Loading backend policies...
          </p>
        )}
        {apiStatus === "mock" && (
          <p className="mt-3 text-xs text-gms-muted">
            Using mock policy data.
          </p>
        )}
        {apiStatus === "error" && (
          <p className="mt-3 text-xs text-gms-danger">{apiError}</p>
        )}
      </section>

      <CreatePolicyModal
        appName={selectedApp || null}
        initialPolicy={
          editingPolicy
            ? policyRowToDraft(editingPolicy, policyDefinitions)
            : null
        }
        isAdmin={isAdmin}
        mode={editingPolicy ? "edit" : "create"}
        open={modalOpen}
        policyOptions={policyOptions}
        onClose={() => {
          setEditingPolicy(null);
          setModalOpen(false);
        }}
        onSubmit={editingPolicy ? handleUpdatePolicy : handleCreatePolicy}
      />

      <PolicySummaryModal
        displayName={summaryPolicy?.name}
        open={summaryPolicy !== null}
        policyId={summaryPolicy?.policyId ?? null}
        scope={summaryPolicy?.scope ?? null}
        onClose={() => setSummaryPolicy(null)}
      />

      {notice && (
        <div
          className={`fixed right-6 top-6 z-[100] flex max-w-md items-start gap-4 rounded-md border bg-white px-5 py-4 text-sm shadow-modal dark:bg-[#252932] ${
            notice.tone === "warning"
              ? "border-[#f1c66a] text-[#74510b]"
              : "border-[#8bc9a7] text-[#245d3b]"
          }`}
          role="alert"
        >
          <span>{notice.message}</span>
          <button
            aria-label="Dismiss notification"
            className="shrink-0"
            type="button"
            onClick={() => setNotice(null)}
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}
    </main>
  );
}

function mapGlobalAssignmentToPolicyRow(
  assignment: GlobalPolicyAssignment,
  definitions: PolicyRecord[]
): PolicyRow {
  return {
    id: `global-${assignment.id}`,
    policyId: assignment.policy_id,
    assignmentId: assignment.id,
    scope: "global",
    connector: assignment.connector ?? "Policy",
    name: assignment.display_name?.trim() || getPolicyDisplayName(
      assignment.policy_id,
      assignment.policy_label,
      definitions
    ),
    created: assignment.created_at,
    global: true,
    app: null
  };
}

function mapEffectiveAssignmentToPolicyRow(
  assignment: EffectivePolicyAssignment,
  definitions: PolicyRecord[],
  appName: string | null = null
): PolicyRow {
  return {
    id: `${assignment.scope}-${assignment.assignment_id}`,
    policyId: assignment.policy_id,
    assignmentId: assignment.assignment_id,
    scope: assignment.scope,
    connector: assignment.connector ?? "Policy",
    name: assignment.display_name?.trim() || getPolicyDisplayName(
      assignment.policy_id,
      assignment.policy_label,
      definitions
    ),
    created: assignment.created_at,
    global: assignment.scope === "global",
    app: assignment.scope === "app" ? appName : null
  };
}

function getPolicyDisplayName(
  policyId: number,
  fallback: string,
  definitions: PolicyRecord[]
) {
  return (
    definitions.find((policy) => policy.id === policyId)?.description?.trim() ||
    fallback
  );
}

function toApiKey(value: string) {
  return value.trim().toLowerCase().replace(/\s+/g, "_");
}

function buildPolicyPayload(draft: PolicyDraft) {
  if (draft.policyType === "output") {
    return {
      policy_type: "output" as const,
      category: "custom",
      description: draft.name,
      effect: "block" as const,
      priority: 100,
      conditions: { output_rule: draft.outputRule },
      enabled: true
    };
  }

  return {
    policy_type: "input" as const,
    connector: toApiKey(draft.connector),
    action: toApiKey(draft.action),
    resource: toApiKey(draft.resource),
    description: draft.name,
    effect: "block" as const,
    priority: 100,
    conditions: draft.customResource
      ? { custom_resource: draft.customResource }
      : {},
    enabled: true
  };
}

function getSelectedApp(apps: ClientApp[], selectedApp: string) {
  const app = apps.find((item) => item.display_label === selectedApp);
  if (!app) {
    throw new Error("Selected app was not found.");
  }
  return app;
}

function policyRowToDraft(
  row: PolicyRow,
  definitions: PolicyRecord[]
): PolicyDraft {
  const definition = definitions.find((policy) => policy.id === row.policyId);
  const customResource = definition?.conditions?.custom_resource;
  return {
    policyType: definition?.policy_type === "output" ? "output" : "input",
    connector: toApiKey(definition?.connector ?? row.connector),
    action: toApiKey(definition?.action ?? ""),
    resource: toApiKey(definition?.resource ?? ""),
    customResource:
      typeof customResource === "string" ? customResource : "",
    outputRule:
      definition?.policy_type === "output"
        ? typeof definition.conditions?.output_rule === "string"
          ? definition.conditions.output_rule
          : definition.description ?? ""
        : "",
    name: row.name,
    global: row.global
  };
}
