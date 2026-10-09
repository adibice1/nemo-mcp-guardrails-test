# Frontend Screen Plan

## Live AI Policy Authoring - 2026-10-09

The normal Create Policy input/output form uses live AI for custom descriptions
from a signed-in management user with a configured backend URL. `Generate policy` sends the
description to JWT-protected `POST /policy-assistant/suggest`. The backend uses
its existing Azure environment deployment, separate from app-selected runtime
models, and validates tagged JSON drafts against the requested rail. Input
combinations must match enabled GitHub write mappings; output is independent
of connector metadata.
The flowchart, custom-resource wording, explanations, illustrative outcomes,
and up to two related input drafts now render from the returned data.

The rail selector appears before the assistant. Output mode offers a hello
sample and a two-step `Output -> Custom resource` flowchart. Its rule checks the
assistant response, fills the existing Output Rule field, and uses response
examples. No additional output bans are suggested. Changing rails unmounts the
assistant and cancels/invalidates pending requests. Other connectors remain
future work.

Ambiguous/unsupported/allow-policy descriptions can return a clarification
instead of a draft. Generation failures show an error without substituting a
sample response. Related drafts remain independently reviewed; `Use this draft`
fills the editable form, preserves scope, and never saves a policy. Existing
Create and assignment-resolution endpoints still enforce persistence/RBAC.

Requests are cancelled when the prompt changes or the assistant unmounts;
late responses are ignored. Backend model calls have a 30-second outer timeout,
and the frontend cancels a stalled request after 45 seconds. Secrets remain on
the backend. No connector tool, runtime rail, or database mutation runs during
generation. The endpoint reads local metadata/authentication rows; it does not
require the hosted database or an app API key.

The drafting-mode selector and Yes/No outcome boxes have been removed. There
is one Generate policy button. Example buttons immediately display the saved
workflow and examples; editing that text clears the preview and custom text
uses live generation. `/policy-preview` disables live drafting even when a
management session exists, preserving its offline sandbox behaviour.
The following initial prototype section records the original sample-only slice.

## Account Password Controls - 2026-10-09

Settings now includes a separate Change password form with current/new/confirm
password fields. The replacement is 15-256 characters and may be a memorable
passphrase. Success clears the session and returns to Login with a confirmation.
Admin resets and self-service changes invalidate older sessions. Copy Password
in User Management handles unavailable/denied clipboard access and shows a
manual-copy message if both clipboard methods fail. Forced first-login setup
and temporary-password expiry remain future work.

## Local Policy Authoring Prototype - 2026-10-09

Create Policy now includes an AI Policy Assistant for input policies. This
first slice uses explicitly labelled sample responses, not live model calls.
It recognises the two supplied non-staging-to-production examples for PR merge
and PR creation, displays a flowchart and suggested custom-resource wording,
and previews a related policy separately. Arbitrary prompts show an explanatory
message instead of silently generating an unrelated draft.

`Use this draft` fills the existing editable form and focuses the policy name.
It preserves the selected app/global scope and checks the supplied policy
options before applying a combination. Saving remains an explicit Create
action; previewing a related suggestion never creates an additional policy.
Expected pass/block examples are illustrations, not runtime test results.
The enforcement model remains the existing semantic NeMo input rail.

For home-computer UI work, open `/policy-preview` on the local Next.js server.
This standalone page needs no management session, backend, database, Azure, or
GitHub connection, even when the frontend API URL is configured. It keeps the
latest mock draft only in React state and loses it on refresh. The normal
management routes retain their authentication and persistence behaviour.
The expanded modal scrolls within the viewport and supports narrow layouts
and the existing dark theme. No new dependency or backend change is required.

The live integration described above completes the next slice from this
initial prototype; deployed verification and broader regression coverage remain.

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
connectors should stay hidden from active selectors until their executable
runtime workflows exist.

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

- Runtime app auth is separate. The app backend still needs `X-App-ID` and
  `X-API-Key`; the local frontend Runtime Test has a key field only for
  manual testing convenience.
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
- connector count
- effective policy count
- created at
- actions

The backend retains `authorized` as a runtime kill switch. The normal developer
UI hides the status because managed apps are authorized by default.

Actions:

- create app: `POST /apps`
- edit app: `PUT /apps/{app_id}`
- delete app: `DELETE /apps/{app_id}`
- open detail: `/apps/[clientId]`

Create form fields:

- name
- main LLM config ID
- guardrail LLM config ID

UX note:

- Client IDs are generated server-side in GUID format.
- API keys are generated server-side and returned once.
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
Overview | Connectors | Policies | Runtime Test
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

Current implementation note:

- The Figma-matched `/policies` screen currently uses
  `GET /apps`, `GET /global-policy-assignments`, and
  `GET /apps/by-client-id/{client_id}/effective-policy-assignments` when
  `NEXT_PUBLIC_API_BASE_URL` is configured.
- Without `NEXT_PUBLIC_API_BASE_URL`, it intentionally falls back to mock data
  for static design demos.
- Create is backend-wired through duplicate-aware global/app resolution.
- Delete is backend-wired as assignment removal; shared definitions remain.
- Assignment-safe Edit is backend-wired through resolve-and-swap behavior.
- Optional custom-resource text is compiled into the input rule and enforced
  again against MCP tool arguments before execution.
- Custom-resource identity is canonicalized so case/plural/wording variants
  reuse one definition.
- Connector, action and resource dropdowns cascade from `GET /policy-options`.
- Mutation errors use top-right warning notices above open dialogs.

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

The app detail Runtime Test renders the runtime sequence as
`Input -> Tool guard -> Output`: green means the stage passed, red means the
stage blocked or errored, and grey means the stage did not run.

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

1. Figma-matched static shell and pages. Done in `frontend/` for `/login`,
   `/signup` admin-managed notice, `/apps`, `/apps/[clientId]`, `/policies`,
   `/user-management`, and `/settings`.
2. API client and typed fetch wrappers. Backend-backed Apps, Policies,
   Settings, Runtime Test, and User Management adapters are active.
3. Policy creation, assignment-safe Edit, and assignment-only Delete are
   backend-wired through duplicate-aware resolve endpoints.
4. Apps list/detail, connector management, effective policy list, and runtime
   test are backend-wired. LLM metadata editing is hidden from normal
   developer-facing app detail screens for now.
5. Admin-only User Management now mirrors the Apps list style. Rows show
   `name`, `email`, `role`, and `enabled`; Create User is a top-level button,
   and clicking a user opens a modal for role/status, temporary-password reset,
   and app links.
7. Runtime tester.
8. Policy library create/edit polish.
9. Dashboard polish.

This order gets the core demo path working quickly:

```text
create app
-> link GitHub connector
-> assign policy
-> test runtime blocked/allowed behavior
```
