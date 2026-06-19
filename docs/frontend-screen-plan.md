# Frontend Screen Plan

Target stack:

```text
Next.js 13 App Router
TypeScript
Tailwind CSS
shadcn/ui
lucide-react
React Hook Form + Zod
TanStack Query or typed fetch wrappers
```

The first frontend should demonstrate GitHub MCP guardrail management. Other
connectors can appear as disabled/future UI affordances, but should not block
the MVP.

## Navigation

Suggested primary navigation:

```text
Dashboard
Apps
Policies
Runtime Tester
Settings
```

Use a quiet admin-console style rather than a marketing page:

- left sidebar
- top bar with API status and current mode
- compact tables
- detail pages with tabs
- modals or side sheets for create/edit forms

## Screen 1: Demo Login

Route:

```text
/login
```

Purpose:

- Placeholder for future user auth.
- Lets demo user enter a display name or choose `Developer` / `Admin` mode.
- No backend auth exists for management CRUD yet.

Components:

- centered login panel
- email field
- password field
- role toggle or demo-mode badge
- submit button

Notes:

- Runtime app auth is separate. Runtime tester still needs `X-App-ID` and
  `X-API-Key`.
- Keep labels honest: "Demo login" or "Local management session".

## Screen 2: Dashboard

Route:

```text
/
```

Purpose:

- Quick overview for presentation.

Data:

- `GET /health`
- `GET /health/db`
- `GET /apps`
- `GET /policies`
- `GET /global-policy-assignments`

Panels:

- API status
- Database status
- total apps
- authorized apps
- total policies
- global policy count
- latest demo checklist

Good empty state:

```text
No apps yet. Create a client app to connect it to GitHub MCP guardrails.
```

## Screen 3: Apps List

Route:

```text
/apps
```

Purpose:

- Manage client apps that consume the GMS.

Data:

- `GET /apps`

Table columns:

- app name
- client ID
- authorized
- main LLM config ID
- guardrail LLM config ID
- created at
- actions

Actions:

- create app: `POST /apps`
- edit app: `PUT /apps/{app_id}`
- delete app: `DELETE /apps/{app_id}`
- open detail: `/apps/[clientId]`

Create form fields:

- name
- client ID
- API key
- authorized
- main LLM config ID
- guardrail LLM config ID

UX note:

- After create, show a warning that the API key cannot be retrieved again.

## Screen 4: App Detail

Route:

```text
/apps/[clientId]
```

Purpose:

- Main workbench for one app.

Load:

- `GET /apps/by-client-id/{client_id}`
- `GET /apps/by-client-id/{client_id}/connectors`
- `GET /apps/by-client-id/{client_id}/effective-policy-assignments`

Header:

- app display label
- client ID
- authorized badge
- app ID
- quick runtime auth status

Tabs:

```text
Overview | Connectors | Policies | Runtime Tester
```

### Overview Tab

Show:

- effective policy counts
- global assignment count
- app assignment count
- enabled/disabled counts
- connector status summary

Useful callouts:

- "GitHub connector enabled"
- "No app-specific policies assigned"
- "Global output policy active"

### Connectors Tab

Data:

- `GET /apps/by-client-id/{client_id}/connectors`

For MVP, show GitHub as the primary connector.

Columns/cards:

- connector display name
- connector name
- enabled
- connector enabled
- credential reference
- updated at

Actions:

- link GitHub:
  `POST /apps/by-client-id/{client_id}/connectors`
- update GitHub:
  `PUT /apps/by-client-id/{client_id}/connectors/github`
- remove GitHub:
  `DELETE /apps/by-client-id/{client_id}/connectors/github`

Form fields:

- connector name: default `github`
- credential reference: `env:APP_A_GITHUB_PAT`
- enabled toggle

Helper text:

```text
Use env:VAR_NAME to select an app-specific GitHub PAT from the backend .env file.
```

### Policies Tab

Data:

- `GET /policies`
- `GET /apps/by-client-id/{client_id}/policy-assignments`
- `GET /apps/by-client-id/{client_id}/effective-policy-assignments`

Sections:

- assigned app policies
- global policies
- available policy library

Actions:

- assign selected policies:
  `POST /apps/by-client-id/{client_id}/policy-assignments`
- enable/disable selected policies:
  `PUT /apps/by-client-id/{client_id}/policy-assignments`
- remove selected app policies:
  `DELETE /apps/by-client-id/{client_id}/policy-assignments`

Recommended UI:

- policy table with checkboxes
- filter by connector/action/resource/category
- segmented filter: `All`, `Assigned`, `Unassigned`, `Global`
- badges for `input`, `output`, `enabled`, `disabled`

### Runtime Tester Tab

Data/actions:

- `GET /v1/guardrails/auth-check`
- `POST /v1/guardrails/run`

Inputs:

- app client ID
- API key
- conversation ID
- message
- optional conversation history JSON editor, hidden under advanced section

Outputs:

- status badge
- assistant response
- rail status row
- tool names
- blocked tools
- policy/rule counts
- history metadata

Good demo messages:

Allowed:

```text
Use GitHub MCP to list branches for owner github and repo github-mcp-server.
```

Blocked when issue-creation policy is assigned:

```text
Use GitHub MCP to create an issue titled "test mcp" and description "hello" under github/github-mcp-server.
```

## Screen 5: Policy Library

Route:

```text
/policies
```

Purpose:

- Create and manage reusable policy definitions.

Data:

- `GET /policies`
- `GET /policies/compiled-rules`

Table columns:

- ID
- type
- connector
- action
- resource
- category
- effect
- priority
- enabled
- version
- updated at

Actions:

- create policy: `POST /policies`
- edit policy: `PUT /policies/{policy_id}`
- delete policy: `DELETE /policies/{policy_id}`
- compile preview: `POST /policies/compile-preview`

Create forms:

Input/tool policy:

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

Output policy:

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

## Screen 6: Runtime Tester

Route:

```text
/runtime
```

Purpose:

- Standalone runtime test page, useful for demos and debugging.

This can reuse the same runtime tester component from app detail.

Extra controls:

- app client ID
- API key
- read/write warning if `GITHUB_MCP_READ_ONLY=0` backend is in use
- saved prompt examples

## Screen 7: Global Policies

Route:

```text
/global-policies
```

Purpose:

- Admin-only future screen.
- For now, useful as a demo/admin page without real auth.

Data:

- `GET /global-policy-assignments`
- `GET /policies`

Actions:

- assign global policies
- enable/disable global policies
- remove global assignment

Warning:

```text
Global policies apply to every app.
```

## Suggested Component Breakdown

```text
components/
  app-shell.tsx
  api-status-badge.tsx
  data-table.tsx
  app-form.tsx
  connector-form.tsx
  policy-form.tsx
  policy-assignment-table.tsx
  effective-policy-summary.tsx
  runtime-tester.tsx
  response-inspector.tsx
  empty-state.tsx
```

## Frontend Implementation Order

1. App shell and API client.
2. Apps list and create/edit forms.
3. App detail with connector tab.
4. App policy assignment tab.
5. Runtime tester.
6. Policy library create/edit.
7. Dashboard polish.

This order gets the core demo path working quickly:

```text
create app
-> link GitHub connector
-> assign policy
-> test runtime blocked/allowed behavior
```
