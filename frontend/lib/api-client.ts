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

async function apiGet<T>(path: string): Promise<T> {
  if (!hasApiBaseUrl()) {
    throw new Error("NEXT_PUBLIC_API_BASE_URL is not configured.");
  }

  const response = await fetch(`${apiBaseUrl}${path}`, {
    headers: { Accept: "application/json" },
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error(
      `API request failed: ${response.status} ${response.statusText}`
    );
  }

  return response.json() as Promise<T>;
}

export function listApps() {
  return apiGet<ClientApp[]>("/apps");
}

export function listGlobalPolicyAssignments() {
  return apiGet<GlobalPolicyAssignment[]>("/global-policy-assignments");
}

export function getEffectivePolicyAssignments(clientId: string) {
  return apiGet<EffectivePolicyAssignmentsResponse>(
    `/apps/by-client-id/${encodeURIComponent(
      clientId
    )}/effective-policy-assignments`
  );
}
