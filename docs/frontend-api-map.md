# Frontend API Map

This map is for the Next.js 13 Guardrails Management System frontend. The
current backend base URL in local development is:

```text
http://127.0.0.1:8000
```

Management endpoints are not authenticated yet. Runtime endpoints require:

```text
X-App-ID: <client_id>
X-API-Key: <plaintext app api key>
```

## Current Frontend Integration State

The frontend policy integration lives in:

```text
frontend/lib/api-client.ts
frontend/app/policies/page.tsx
```

Local backend mode is enabled by creating `frontend/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

If this env var is absent, the frontend remains in mock mode. This keeps the
Vercel/design preview working without a backend.

The current `/policies` page reads:

```text
GET /apps
GET /global-policy-assignments
GET /apps/by-client-id/{client_id}/effective-policy-assignments
```

The current `/policies` page reads and mutates through the backend. Creation
uses the resolve endpoints below, so equivalent reusable policies are reused
instead of inserted again. Edit resolves and swaps only the selected assignment;
Delete removes the assignment only.

The shared Create/Edit modal supports both rail types. Input policies submit
the selected connector/action/resource plus optional
`conditions.custom_resource`. Output policies omit connector metadata and
submit `policy_type: output`, `category: custom`, the policy name as
`description`, and the required free-text restriction as
`conditions.output_rule`. The assignment `display_name` remains the visible
app/global label and allows different apps to name one reusable definition
independently.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/apps/by-client-id/{client_id}/policy-assignments/resolve` | Create/reuse and assign one app policy |
| `POST` | `/global-policy-assignments/resolve` | Create/reuse and assign one global policy |
| `PUT` | `/apps/by-client-id/{client_id}/policy-assignments/{assignment_id}/resolve` | Edit one app assignment by resolving reusable behavior |
| `PUT` | `/global-policy-assignments/{assignment_id}/resolve` | Edit one global assignment by resolving reusable behavior |

Resolution responses return `created`, `reused`, or `already_assigned` plus
the reusable `policy_id`, concrete `assignment_id`, and assignment-specific
`display_name`.

Browser access from the local frontend is controlled by:

```env
NEMO_CORS_ORIGINS=http://127.0.0.1:3000,http://localhost:3000
```

Optional custom-resource text is stored under
`conditions.custom_resource`. The compiler includes it in the NeMo input rule,
and the execution-level tool guard recursively compares the normalized value
against exact MCP argument values. Leaving it blank keeps the action/resource
policy broad.

Before storage and duplicate resolution, custom-resource phrases are
canonicalized. For an Issue policy, `issue name test`, `Issue name test`,
`Issues name test`, and `issues named test` all resolve to `test` and reuse the
same policy definition.

## Policy Options

| Screen | Method | Endpoint | Purpose |
| --- | --- | --- | --- |
| Create/Edit Policy | `GET` | `/policy-options` | Enabled connector/action/resource combinations from normalized tool mappings |

The frontend filters actions by connector and resources by action. Connectors
without enabled mappings, including the current SharePoint placeholder, are not
offered in the policy form.

## Health

| Screen | Method | Endpoint | Purpose |
| --- | --- | --- | --- |
| Shell/status badge | `GET` | `/health` | API liveness |
| Shell/status badge | `GET` | `/health/db` | DB connectivity |

## Apps

These endpoints now power `/apps` and `/apps/[clientId]`. The list supports
search, pagination, create, delete, connector/policy counts, and row navigation.
The detail route provides Overview, Connectors, LLM, Policies, and Runtime Test
tabs.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/apps` | List client apps |
| `POST` | `/apps` | Create a client app |
| `GET` | `/apps/{app_id}` | Get app by numeric ID |
| `GET` | `/apps/by-client-id/{client_id}` | Get app by readable client ID |
| `PUT` | `/apps/{app_id}` | Update app |
| `DELETE` | `/apps/{app_id}` | Delete app |

Create app body:

```json
{
  "name": "Finance Bot",
  "client_id": "finance-bot",
  "api_key": "replace-with-strong-api-key",
  "authorized": true,
  "main_llm_config_id": null,
  "guardrail_llm_config_id": null
}
```

Important frontend behavior:

- The API key is only accepted on create/update; the backend never returns it.
- Store the plaintext API key only in local demo state or ask the user to paste
  it again for runtime testing.
- Prefer `client_id` routes in the UI because they are easier for developers to
  recognize than numeric IDs.

## App Connectors

Use these for the app detail connector tab. For the current demo, GitHub is the
main connector.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/apps/{app_id}/connectors` | List connector links |
| `POST` | `/apps/{app_id}/connectors` | Create/update connector link |
| `PUT` | `/apps/{app_id}/connectors/{connector_ref}` | Update connector link |
| `DELETE` | `/apps/{app_id}/connectors/{connector_ref}` | Delete connector link |
| `GET` | `/apps/by-client-id/{client_id}/connectors` | List links by client ID |
| `POST` | `/apps/by-client-id/{client_id}/connectors` | Create/update by client ID |
| `PUT` | `/apps/by-client-id/{client_id}/connectors/{connector_ref}` | Update by client ID |
| `DELETE` | `/apps/by-client-id/{client_id}/connectors/{connector_ref}` | Delete by client ID |

`connector_ref` can be `github` or the numeric connector ID.

Create/update body:

```json
{
  "connector_name": "github",
  "credential_reference": "env:APP_A_GITHUB_PAT",
  "enabled": true
}
```

Runtime behavior:

- `credential_reference="env:APP_A_GITHUB_PAT"` reads that PAT from `.env`.
- A blank credential reference falls back to `GITHUB_PERSONAL_ACCESS_TOKEN`.
- `vault:...` is not supported yet and will fail clearly.

## Policies

Use these for the policy library screen.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/policies` | List reusable policies |
| `POST` | `/policies` | Create a reusable policy and auto-compile it |
| `GET` | `/policies/{policy_id}` | Get one policy |
| `PUT` | `/policies/{policy_id}` | Update policy and auto-refresh compiled rules |
| `DELETE` | `/policies/{policy_id}` | Delete policy and cascaded compiled rules |
| `POST` | `/policies/compile-preview` | Preview compiler output |
| `GET` | `/policies/compiled-rules` | Inspect active compiled rules |
| `POST` | `/policies/compile-rules` | Manual full compiled-rule resync |

GitHub issue-creation block example:

```json
{
  "policy_type": "input",
  "connector": "github",
  "action": "create",
  "resource": "issue",
  "description": "Block GitHub issue creation",
  "effect": "block",
  "priority": 100,
  "conditions": {},
  "enabled": true
}
```

Credential output block example:

```json
{
  "policy_type": "output",
  "category": "credentials",
  "description": "Block actual sensitive credential or secret configuration values",
  "effect": "block",
  "priority": 100,
  "conditions": {},
  "enabled": true
}
```

## App Policy Assignments

Use these in the app detail policies tab.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/apps/{app_id}/policy-assignments` | List app-specific assignments |
| `POST` | `/apps/{app_id}/policy-assignments` | Assign one or more policies |
| `PUT` | `/apps/{app_id}/policy-assignments` | Enable/disable multiple assignments by policy IDs |
| `DELETE` | `/apps/{app_id}/policy-assignments` | Delete multiple assignments by policy IDs |
| `PUT` | `/apps/{app_id}/policy-assignments/{assignment_id}` | Enable/disable one assignment |
| `DELETE` | `/apps/{app_id}/policy-assignments/{assignment_id}` | Delete one assignment |
| `GET` | `/apps/by-client-id/{client_id}/policy-assignments` | List by client ID |
| `POST` | `/apps/by-client-id/{client_id}/policy-assignments` | Assign by client ID |
| `PUT` | `/apps/by-client-id/{client_id}/policy-assignments` | Bulk update by client ID |
| `DELETE` | `/apps/by-client-id/{client_id}/policy-assignments` | Bulk delete by client ID |

Assign policies body:

```json
{
  "policy_ids": [12, 13, 26],
  "enabled": true
}
```

Bulk disable body:

```json
{
  "policy_ids": [12, 13],
  "enabled": false
}
```

Bulk delete body:

```json
{
  "policy_ids": [12, 13]
}
```

## Effective Policy Summary

Use this for a read-only summary panel in the app detail page.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/apps/{app_id}/effective-policy-assignments` | App + global assignments |
| `GET` | `/apps/by-client-id/{client_id}/effective-policy-assignments` | App + global assignments by client ID |

The response includes:

- app label
- global assignment count
- app assignment count
- enabled/disabled counts
- global assignments
- app assignments

## Global Policy Assignments

Use these on an admin-only global policy screen later. Current backend does not
enforce admin auth yet.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/global-policy-assignments` | List global assignments |
| `POST` | `/global-policy-assignments` | Assign one or more global policies |
| `PUT` | `/global-policy-assignments` | Bulk enable/disable by policy IDs |
| `DELETE` | `/global-policy-assignments` | Bulk delete by policy IDs |
| `PUT` | `/global-policy-assignments/{assignment_id}` | Enable/disable one global assignment |
| `DELETE` | `/global-policy-assignments/{assignment_id}` | Delete one global assignment |

## Runtime

Use this for the runtime tester panel.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/v1/guardrails/auth-check` | Check runtime app credentials |
| `POST` | `/v1/guardrails/run` | Execute guarded request |

Headers:

```text
X-App-ID: finance-bot
X-API-Key: replace-with-strong-api-key
```

Run request:

```json
{
  "message": "List recent pull requests in github/github-mcp-server.",
  "conversation_id": "demo-conversation-1",
  "conversation_history": []
}
```

Run response fields to display:

- `status`
- `response`
- `input_rail_status`
- `input_rail_source`
- `input_rail_categories`
- `output_rail_status`
- `output_rail_source`
- `output_rail_categories`
- `tool_guard_status`
- `tool_guard_source`
- `tool_names`
- `input_policy_count`
- `input_rule_count`
- `output_rule_count`
- `blocked_tools`
- `history_truncated`

Runtime Test formats confirmed provider filtering as
`blocked (Azure: category)` and NeMo/deterministic enforcement as
`blocked (GMS)`. If Azure does not report a category, show `blocked (Azure)`.

## Allowed Test Cases

This screen is optional for the frontend MVP. These are safe prompts used by
the backend test runner, not allow/block policy records.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/allowed-test-cases` | List safe allowed test prompts |
| `POST` | `/allowed-test-cases` | Create allowed test prompt |
| `GET` | `/allowed-test-cases/{test_case_id}` | Get one allowed test prompt |
| `PUT` | `/allowed-test-cases/{test_case_id}` | Update allowed test prompt |
| `DELETE` | `/allowed-test-cases/{test_case_id}` | Delete allowed test prompt |
