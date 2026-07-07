import {
  clearManagementSession,
  loadManagementSession
} from "@/lib/management-auth";


const rawApiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

export const apiBaseUrl = rawApiBaseUrl.replace(/\/$/, "");

export function hasApiBaseUrl() {
  return apiBaseUrl.length > 0;
}

export type ManagementUser = {
  id: number;
  email: string;
  name: string;
  username: string;
  system_role: "developer" | "admin";
};

export type ManagedUser = ManagementUser & {
  enabled: boolean;
  created_at: string;
  updated_at: string;
};

export type ManagedUserCreatePayload = {
  email: string;
  name?: string | null;
  username?: string | null;
  system_role: "developer" | "admin";
  enabled: boolean;
};

export type ManagedUserCreateResponse = ManagedUser & {
  temporary_password: string;
  temporary_password_notice: string;
};

export type ManagedUserUpdatePayload = {
  name?: string;
  username?: string;
  system_role?: "developer" | "admin";
  enabled?: boolean;
};

export type ManagedUserPasswordResetResponse = {
  user_id: number;
  email: string;
  temporary_password: string;
  temporary_password_notice: string;
};

export type UserAppLink = {
  id: number;
  user_id: number;
  user_email: string;
  app_id: number;
  app_name: string;
  client_id: string;
  role: string;
  created_at: string;
  updated_at: string;
};

export type UserAppLinkCreatePayload = {
  app_id?: number;
  client_id?: string;
  role?: "admin";
};

export type ManagementSession = {
  access_token: string;
  token_type: "bearer";
  user: ManagementUser;
};

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

export type AppCreatePayload = {
  name: string;
  client_id: string;
  authorized: boolean;
  main_llm_config_id: number | null;
  guardrail_llm_config_id: number | null;
};

export type AppCreateResponse = ClientApp & {
  api_key: string;
  api_key_notice: string;
};

export type AppUpdatePayload = Partial<Omit<AppCreatePayload, "authorized">> & {
  authorized?: boolean;
};

export type AppApiKeyResponse = {
  app_id: number;
  client_id: string;
  api_key: string;
  api_key_notice: string;
};

export type LlmConfig = {
  id: number;
  name: string;
  provider: string;
  model_name: string;
  endpoint: string | null;
  enabled: boolean;
};

export type LlmConfigCreatePayload = {
  name: string;
  provider: "azure" | "azure_openai";
  model_name: string;
  endpoint: string | null;
  credential_reference: string | null;
  enabled: boolean;
};

export type AppConnector = {
  id: number;
  app_id: number;
  app_label: string;
  connector_id: number;
  connector_name: string;
  connector_display_name: string;
  credential_reference: string | null;
  enabled: boolean;
  connector_enabled: boolean;
  created_at: string;
  updated_at: string;
};

export type GuardrailsRunResponse = {
  status: string;
  app_id: number;
  client_id: string;
  conversation_id: string | null;
  response: string;
  input_rail_status: string;
  input_rail_source: string | null;
  input_rail_categories: string[];
  output_rail_status: string | null;
  output_rail_source: string | null;
  output_rail_categories: string[];
  tool_guard_status: string;
  tool_guard_source: string | null;
  block_stage: string | null;
  block_reason: string | null;
  blocked_policy_id: number | null;
  blocked_policy_name: string | null;
  tool_names: string[];
  input_policy_count: number;
  input_rule_count: number;
  output_rule_count: number;
  blocked_tools: string[];
  history_truncated: boolean;
  history_messages_received: number;
  history_messages_loaded: number;
  history_messages_used: number;
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

export type PolicyConnectorOption = {
  value: string;
  label: string;
  actions: Array<{
    value: string;
    label: string;
    resources: Array<{
      value: string;
      label: string;
    }>;
  }>;
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

  const headers = new Headers(init?.headers);
  if (!headers.has("Accept")) headers.set("Accept", "application/json");
  if (!headers.has("Content-Type")) headers.set("Content-Type", "application/json");

  const session = loadManagementSession();
  if (session && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${session.access_token}`);
  }

  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers,
    cache: "no-store"
  });

  if (!response.ok) {
    if (response.status === 401) clearManagementSession();
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

export function signupManagementUser(email: string, password: string) {
  return apiRequest<ManagementSession>("/management-auth/signup", {
    method: "POST",
    body: JSON.stringify({ email, password })
  });
}

export function loginManagementUser(email: string, password: string) {
  return apiRequest<ManagementSession>("/management-auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password })
  });
}

export function getCurrentManagementUser(token: string) {
  return apiRequest<ManagementUser>("/management-auth/me", {
    headers: { Authorization: `Bearer ${token}` }
  });
}

export function updateCurrentManagementUser(
  token: string,
  profile: { name: string; username: string }
) {
  return apiRequest<ManagementUser>("/management-auth/me", {
    method: "PUT",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(profile)
  });
}

export function listManagedUsers() {
  return apiRequest<ManagedUser[]>("/management-users");
}

export function createManagedUser(payload: ManagedUserCreatePayload) {
  return apiRequest<ManagedUserCreateResponse>("/management-users", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateManagedUser(
  userId: number,
  payload: ManagedUserUpdatePayload
) {
  return apiRequest<ManagedUser>(`/management-users/${userId}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function resetManagedUserPassword(userId: number) {
  return apiRequest<ManagedUserPasswordResetResponse>(
    `/management-users/${userId}/password`,
    { method: "POST" }
  );
}

export function listManagedUserApps(userId: number) {
  return apiRequest<UserAppLink[]>(`/management-users/${userId}/apps`);
}

export function linkManagedUserApp(
  userId: number,
  payload: UserAppLinkCreatePayload
) {
  return apiRequest<UserAppLink>(`/management-users/${userId}/apps`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function unlinkManagedUserApp(userId: number, appId: number) {
  return apiRequest<void>(`/management-users/${userId}/apps/${appId}`, {
    method: "DELETE"
  });
}

export function listApps() {
  return apiRequest<ClientApp[]>("/apps");
}

export function createApp(payload: AppCreatePayload) {
  return apiRequest<AppCreateResponse>("/apps", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getApp(clientId: string) {
  return apiRequest<ClientApp>(
    `/apps/by-client-id/${encodeURIComponent(clientId)}`
  );
}

export function updateApp(appId: number, payload: AppUpdatePayload) {
  return apiRequest<ClientApp>(`/apps/${appId}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function regenerateAppApiKey(appId: number) {
  return apiRequest<AppApiKeyResponse>(`/apps/${appId}/api-key`, {
    method: "POST"
  });
}

export function deleteApp(appId: number) {
  return apiRequest<void>(`/apps/${appId}`, { method: "DELETE" });
}

export function listLlmConfigs() {
  return apiRequest<LlmConfig[]>("/llm-configs");
}

export function createLlmConfig(payload: LlmConfigCreatePayload) {
  return apiRequest<LlmConfig>("/llm-configs", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function listAppConnectors(clientId: string) {
  return apiRequest<AppConnector[]>(
    `/apps/by-client-id/${encodeURIComponent(clientId)}/connectors`
  );
}

export function saveAppConnector(
  clientId: string,
  payload: {
    connector_name: string;
    credential_reference: string | null;
    enabled: boolean;
  }
) {
  return apiRequest<AppConnector>(
    `/apps/by-client-id/${encodeURIComponent(clientId)}/connectors`,
    {
      method: "POST",
      body: JSON.stringify(payload)
    }
  );
}

export function updateAppConnector(
  clientId: string,
  connectorName: string,
  payload: { credential_reference?: string | null; enabled?: boolean }
) {
  return apiRequest<AppConnector>(
    `/apps/by-client-id/${encodeURIComponent(
      clientId
    )}/connectors/${encodeURIComponent(connectorName)}`,
    {
      method: "PUT",
      body: JSON.stringify(payload)
    }
  );
}

export function deleteAppConnector(
  clientId: string,
  connectorName: string
) {
  return apiRequest<void>(
    `/apps/by-client-id/${encodeURIComponent(
      clientId
    )}/connectors/${encodeURIComponent(connectorName)}`,
    { method: "DELETE" }
  );
}

export function runGuardrails(
  clientId: string,
  apiKey: string,
  payload: {
    message: string;
    conversation_id?: string | null;
    conversation_history?: Array<{
      role: "user" | "assistant";
      content: string;
    }>;
  }
) {
  return apiRequest<GuardrailsRunResponse>("/v1/guardrails/run", {
    method: "POST",
    headers: {
      "X-App-ID": clientId,
      "X-API-Key": apiKey
    },
    body: JSON.stringify(payload)
  });
}

export async function runGuardrailsViaProxy(
  clientId: string,
  payload: {
    message: string;
    conversation_id?: string | null;
    conversation_history?: Array<{
      role: "user" | "assistant";
      content: string;
    }>;
  }
) {
  const response = await fetch("/api/guardrails/run", {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ client_id: clientId, ...payload }),
    cache: "no-store"
  });

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    throw new Error(body?.detail ?? `Runtime request failed: ${response.status}`);
  }

  return (await response.json()) as GuardrailsRunResponse;
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

export function listPolicyOptions() {
  return apiRequest<PolicyConnectorOption[]>("/policy-options");
}

export function getPolicy(policyId: number) {
  return apiRequest<PolicyRecord>(`/policies/${policyId}`);
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
