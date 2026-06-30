const rawApiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

export const apiBaseUrl = rawApiBaseUrl.replace(/\/$/, "");

export function hasApiBaseUrl() {
  return apiBaseUrl.length > 0;
}

export type ClientApp = {
  id: number;
  name: string;
  client_id: string;
  display_label: string;
  authorized: boolean;
  main_llm_config_id: number | null;
  guardrail_llm_config_id: number | null;
  created_at: string;
  updated_at: string;
};

export type GlobalPolicyAssignment = {
  id: number;
  policy_id: number;
  policy_label: string;
  policy_type: string;
  connector: string | null;
  action: string | null;
  resource: string | null;
  category: string | null;
  display_name: string | null;
  enabled: boolean;
  created_at: string;
  updated_at: string;
};

export type EffectivePolicyAssignment = {
  assignment_id: number;
  scope: "global" | "app";
  policy_id: number;
  policy_label: string;
  policy_type: string;
  connector: string | null;
  action: string | null;
  resource: string | null;
  category: string | null;
  display_name: string | null;
  enabled: boolean;
  created_at: string;
  updated_at: string;
};

export type EffectivePolicyAssignmentsResponse = {
  app_id: number;
  app_label: string;
  global_assignment_count: number;
  app_assignment_count: number;
  enabled_assignment_count: number;
  disabled_assignment_count: number;
  global_assignments: EffectivePolicyAssignment[];
  app_assignments: EffectivePolicyAssignment[];
};

export type PolicyRecord = {
  id: number;
  policy_type: string;
  connector: string | null;
  action: string | null;
  resource: string | null;
  category: string | null;
  description: string | null;
  effect: string;
  priority: number;
  conditions: Record<string, unknown>;
  enabled: boolean;
  created_at: string;
  updated_at: string;
};

export type PolicyCreatePayload = {
  policy_type: "input" | "output";
  connector?: string | null;
  action?: string | null;
  resource?: string | null;
  category?: string | null;
  description?: string | null;
  effect: "allow" | "block";
  priority: number;
  conditions: Record<string, unknown>;
  enabled: boolean;
};

export type PolicyAssignmentResolution = {
  resolution: "created" | "reused" | "already_assigned";
  scope: "app" | "global";
  policy_id: number;
  assignment_id: number;
  display_name: string | null;
  policy_label: string;
};

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  if (!hasApiBaseUrl()) {
    throw new Error("NEXT_PUBLIC_API_BASE_URL is not configured.");
  }

  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json"
    },
    cache: "no-store"
  });

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as {
      detail?: string | { code?: string; policy_id?: number };
    } | null;
    const detail = body?.detail;
    const message =
      typeof detail === "string"
        ? detail
        : detail?.code === "equivalent_policy_exists"
        ? `An equivalent policy already exists as policy ${detail.policy_id}.`
        : `API request failed: ${response.status}`;
    throw new Error(message);
  }

  return response.status === 204
    ? (undefined as T)
    : ((await response.json()) as T);
}

export function listApps() {
  return apiRequest<ClientApp[]>("/apps");
}

export function listGlobalPolicyAssignments() {
  return apiRequest<GlobalPolicyAssignment[]>("/global-policy-assignments");
}

export function getEffectivePolicyAssignments(clientId: string) {
  return apiRequest<EffectivePolicyAssignmentsResponse>(
    `/apps/by-client-id/${encodeURIComponent(
      clientId
    )}/effective-policy-assignments`
  );
}

export function listPolicies() {
  return apiRequest<PolicyRecord[]>("/policies");
}

export function createPolicy(payload: PolicyCreatePayload) {
  return apiRequest<PolicyRecord>("/policies", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function deletePolicy(policyId: number) {
  return apiRequest<void>(`/policies/${policyId}`, { method: "DELETE" });
}

export function assignPoliciesGlobally(policyIds: number[]) {
  return apiRequest<GlobalPolicyAssignment[]>("/global-policy-assignments", {
    method: "POST",
    body: JSON.stringify({ policy_ids: policyIds, enabled: true })
  });
}

export function assignPoliciesToApp(clientId: string, policyIds: number[]) {
  return apiRequest(
    `/apps/by-client-id/${encodeURIComponent(clientId)}/policy-assignments`,
    {
      method: "POST",
      body: JSON.stringify({ policy_ids: policyIds, enabled: true })
    }
  );
}

export function resolvePolicyForApp(
  clientId: string,
  policy: PolicyCreatePayload,
  displayName: string
) {
  return apiRequest<PolicyAssignmentResolution>(
    `/apps/by-client-id/${encodeURIComponent(
      clientId
    )}/policy-assignments/resolve`,
    {
      method: "POST",
      body: JSON.stringify({ policy, display_name: displayName })
    }
  );
}

export function resolvePolicyGlobally(
  policy: PolicyCreatePayload,
  displayName: string
) {
  return apiRequest<PolicyAssignmentResolution>(
    "/global-policy-assignments/resolve",
    {
      method: "POST",
      body: JSON.stringify({ policy, display_name: displayName })
    }
  );
}

export function editAppPolicyAssignment(
  clientId: string,
  assignmentId: number,
  policy: PolicyCreatePayload,
  displayName: string
) {
  return apiRequest<PolicyAssignmentResolution>(
    `/apps/by-client-id/${encodeURIComponent(
      clientId
    )}/policy-assignments/${assignmentId}/resolve`,
    {
      method: "PUT",
      body: JSON.stringify({ policy, display_name: displayName })
    }
  );
}

export function editGlobalPolicyAssignment(
  assignmentId: number,
  policy: PolicyCreatePayload,
  displayName: string
) {
  return apiRequest<PolicyAssignmentResolution>(
    `/global-policy-assignments/${assignmentId}/resolve`,
    {
      method: "PUT",
      body: JSON.stringify({ policy, display_name: displayName })
    }
  );
}

export function deleteAppPolicyAssignment(
  clientId: string,
  assignmentId: number
) {
  return apiRequest<void>(
    `/apps/by-client-id/${encodeURIComponent(
      clientId
    )}/policy-assignments/${assignmentId}`,
    { method: "DELETE" }
  );
}

export function deleteGlobalPolicyAssignment(assignmentId: number) {
  return apiRequest<void>(`/global-policy-assignments/${assignmentId}`, {
    method: "DELETE"
  });
}
