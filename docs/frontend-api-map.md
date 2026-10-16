# Frontend API Map

Patch 019 keeps the existing policy/assignment endpoints and conditions JSON.
PR create/merge options advertise source_branch and target_branch fields; the
shared builder supports equality/inequality with AND. Merge summaries and AI
explanations disclose that nonmatching branch-conditional merges are refused.
See [019 contract](branch-routing-patch-019.md); no selective merge guarantee is
implied by a saved policy or a field being available in the catalogue.

## Current Auth And Request Contracts - 2026-10-16

Login/current-user responses include `must_change_password`. Temporary credentials
receive a setup-only JWT; only `GET /management-auth/me` and
`PUT /management-auth/me/password` are allowed until successful replacement.
Other management endpoints return 403. Expired setup credentials return the same
401 as invalid credentials. `/setup-password` uses the existing password-change
endpoint, then clears the session and returns to Login. Normal password changes
retain the current-password check. Creation/reset secrets and login tokens use
`Cache-Control: no-store`.

Login, password change/reset and policy AI may return 429 with `Retry-After`.
Raw requests above 512 KiB return 413 from the proxy or API. Runtime schema limits
are message 16,000 characters, history 32 turns / 64,000 characters and ID 200
characters; invalid/control/null values return generic 422 without echoing input.
The proxy uses asynchronous Next route params and keeps credential headers and
manual redirects. See the [completion report](security-run-2026-10-16.md) for
history and timeout semantics and the prerequisite database rollout.
This map is for the Next.js 13 Guardrails Management System frontend. The
current backend base URL in local development is:

```text
http://127.0.0.1:8000
```

Management signup/login/current-user and management CRUD endpoints use JWT
authentication. Runtime requests from client applications separately require:

```text
X-App-ID: <client_id>
X-API-Key: <plaintext app api key>
```

## AI Policy Authoring

| Screen | Method | Endpoint | Purpose |
| --- | --- | --- | --- |
| Create Policy input/output form | `POST` | `/policy-assistant/suggest` | Generate validated draft, wording, illustrative cases and related suggestions |

This endpoint requires the current management JWT. Request body:

```json
{"policy_type": "input", "prompt": "Block merging pull request number 17"}
```

Response: `draft` (or null), `related` (at most two drafts), and `clarification`.
Every draft has a `policy_type` tag. Input drafts contain `name`, `connector`,
`action`, `resource`, `custom_resource`, `explanation`, and `examples` with
`prompt`/`expected` values. Examples are illustrative predictions, not tests.
Authenticated users may request suggestions;
policy mutation/global-assignment permissions remain enforced by existing CRUD.

For output requests send `policy_type: "output"` with a response restriction,
e.g. `Block any agent response that contains the word "hello"`. Output drafts
contain `policy_type`, `name`, `output_rule`, `explanation` and `examples`;
example `prompt` values represent assistant responses. Output `related` is empty.
The form stores the rule in `conditions.output_rule`, not `custom_resource`.
Output generation does not require GitHub metadata. The default request rail
remains input, and mismatched draft rails/unknown fields are rejected.

Only enabled GitHub action/resource combinations supported by the write-policy
compiler are accepted for input drafts; other-connector input authoring is deferred.
009c3a validates primary and related selectors through the same preparation used
by storage and returns canonical equality text. Related input suggestions must
retain the primary connector, resource and canonical selector. Unsupported
conditions or changed related scope return HTTP 200 with `draft: null`,
`related: []` and clarification; no partial draft or broader substitute is returned.
Compound/negated conditions, workflows and branch-based merge restrictions require
additional capabilities. Structural, rail and tuple errors retain controlled
errors. This validation proves executable shape, not faithful interpretation of
the user request; drafts still require review before saving.
The AI uses the backend Azure environment defaults and never receives assignment
scope or browser credentials. Generation reads
authentication rows and input metadata, but does not create policies/assignments
or invoke connector tools.
Responses use `no-store`. Provider failures, invalid drafts and timeouts produce
controlled errors. Current input samples cover PR 17 merges and PR creation
targeting exact branch Production. The unsupported compound-merge example returns
clarification with no draft; independent samples do not suggest one another as
related scopes. Output hello behavior is unchanged. Example buttons load saved previews immediately; edited
descriptions use live AI through the single Generate policy button.

## Runtime Logs

These screens require a system administrator's management JWT, not an app
API key. Backend permission checks apply to both list and detail requests.

| Screen | Method | Endpoint | Purpose |
| --- | --- | --- | --- |
| `/logs` | `GET` | `/apps` | Populate the app filter |
| `/logs` | `GET` | `/runtime-logs` | Read paginated request metadata |
| `/logs/[requestId]` | `GET` | `/runtime-logs/{request_id}` | Read ordered execution events |
| `/logs/[requestId]` | `GET` | `/runtime-logs/{request_id}/user-content` | Read captured input and final response when available |
| `/logs` Audit Logs tab | `GET` | `/audit-logs` | Read sanitized management mutation metadata |

The list uses `app_id`, `outcome`, `limit=25`, and `offset`. Pagination uses
`has_more`; no total count is available. Timestamps are displayed in UTC.
Traffic detail combines the prompt/final response with request metadata and
execution events. Audit list filtering uses `entity_type`, `outcome`,
`limit=25`, and `offset`. Audit records never include request/response bodies,
passwords, API keys, tool arguments, credentials, or private model reasoning.

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

Runtime Test asks for the selected app's plaintext API key for local/manual
testing convenience. Real client applications should never expose this key to
end users; they send `X-App-ID` and `X-API-Key` from their own backend. The
runtime result is displayed as a three-step progress bar:
`Input -> Tool guard -> Output`, with blocked stages shown in red and skipped
stages shown in grey.
Runtime debug is disabled in `.env.example`. With `NEMO_RUNTIME_DEBUG=1`,
Runtime Test displays tool event names and tool names only. Runtime responses
never expose raw agent output, tool arguments/results/errors, or output rule
text through debug fields. Legacy `debug_agent_response` and
`debug_output_rule_texts` fields remain null for response compatibility.

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
`display_name`. The frontend intentionally does not expose the internal
`reused` wording; users see simple create/edit/delete notices.

Browser access from the local frontend is controlled by:

```env
NEMO_CORS_ORIGINS=http://127.0.0.1:3000,http://localhost:3000
```

009c1 validates new input `conditions.custom_resource` values against the
supported GitHub action/field subset before storage or duplicate resolution.
Nonempty selectors store canonical field equality text with integer
`conditions.resource_condition_version: 1`. For issue creation, `issue name test`
and `Issues named test` resolve to the same canonical title equality. Path/branch
case is significant; title/repository-name case folds while punctuation and
Unicode remain intact. Blank selectors keep the action/resource policy broad.

Unsupported conditions, unknown condition keys, invalid markers and canonical
text exceeding 1,000 characters return HTTP 400. Metadata-only edits cannot
promote legacy literals: resubmit conditions explicitly to review them, or use
an exact disable-only update. Unversioned literal definitions are excluded from
automatic reuse/deduplication. Assignment-safe resolution can create a reviewed
definition without changing another app's legacy assignment. Output storage is
unchanged. The version marker describes serialization, not runtime enforcement.

009c2b now validates broad input combinations against the supported-write gate
too; unsupported read-block definitions return HTTP 400 even though read tools
remain in connector metadata. Conditional compiler text and generated blocked
prompts name the actual field/literal/comparison. Existing conditional compiled
rows need reviewed resync before eventual rollout; no live resync ran.

009c2c connects the field-bound matcher/catalogue and immutable snapshots to
execution and exact-content cache checks. A matched tool rule supplies its actual
policy ID/name. Indeterminate targets return `tool_error` with source
`gms_tool_guard_evaluation` and no matched policy ID. No frontend code changed
in 009c2c or 009c3a. 009c3b now aligns frontend samples, mock options, field help
and submission availability; focused selector submit/edit checks passed. The version marker alone proves no enforcement.

## Policy Options

| Screen | Method | Endpoint | Purpose |
| --- | --- | --- | --- |
| Create/Edit Policy | `GET` | `/policy-options` | Enabled supported input-block combinations and conditional fields |

009c3a excludes unsupported read-block combinations and connector-inconsistent
metadata. Connectors, actions, resources and mappings must all be enabled. Each
resource includes additive `condition_fields`, such as `["number"]` for PR merges
or `["title", "source_branch", "target_branch"]` for PR creation. An empty list
means broad scope only; it does not permit arbitrary conditions. Field names
describe available selector bindings, not all remote state or argument values.
The frontend filters actions by connector and resources by action. 009c3b consumes
these field names in help/placeholders and prevents submission of unavailable
combinations or nonempty conditions on broad-only combinations. Existing condition
text is retained for explicit review/clearing; backend validation remains authoritative. The demo UI currently offers only GitHub; SharePoint remains hidden
until its executable runtime workflow is implemented.

## Health

| Screen | Method | Endpoint | Purpose |
| --- | --- | --- | --- |
| Shell/status badge | `GET` | `/health` | API liveness |
| Shell/status badge | `GET` | `/health/db` | DB connectivity |

## Management Authentication

The Login screen uses real management identities. Public signup is disabled:
GMS administrators create user accounts from the admin-only User Management
screen, then issue a generated temporary password displayed once.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/management-auth/signup` | Reject public signup with `403` |
| `POST` | `/management-auth/login` | Authenticate email/password and return a JWT |
| `GET` | `/management-auth/me` | Restore the current bearer-token identity |
| `PUT` | `/management-auth/me` | Save the current user's name and username |
| `PUT` | `/management-auth/me/password` | Verify current password and change the signed-in user's password |

The browser stores the prototype token in session storage, or local storage
when Remember Me is selected. `api-client.ts` automatically attaches it as a
Bearer token. Settings displays the real read-only email, persists
name/username, offers Change password and the Dark Mode preference toggle, and clears the session
on the red Logout action. Runtime app-auth failures such as invalid app API
keys must not clear the management login; the frontend only clears the stored
management session when the backend returns the management-auth detail
`Authentication required`.

## User Management

These endpoints power `/user-management`. The shared top nav shows that tab only
for management users with `system_role = admin`. The screen now mirrors the
Apps layout: users are listed in rows with `name`, `email`, `role`, and
`enabled` status; clicking a user opens a details modal for role/status,
temporary-password reset, and app links.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/management-users` | Admin list of all GMS users |
| `POST` | `/management-users` | Admin-created user with a temporary password displayed once |
| `PUT` | `/management-users/{user_id}` | Update system role or enabled/blocked state |
| `DELETE` | `/management-users/{user_id}` | Delete one user and their app links; admins cannot delete their own current account |
| `POST` | `/management-users/{user_id}/password` | Generate a replacement temporary password |
| `GET` | `/management-users/{user_id}/apps` | List app-role links for one user |
| `POST` | `/management-users/{user_id}/apps` | Link or relink a user to an app as an app developer |
| `DELETE` | `/management-users/{user_id}/apps/{app_id}` | Remove one app-role link |

Temporary passwords are returned only in the create/reset responses. Admins
must copy them before closing the notice.

### Password Changes And Remaining Lifecycle Work - 2026-10-09

Settings sends `current_password` and `new_password` to the JWT-protected
`PUT /management-auth/me/password`. New passwords are 15-256 characters;
incorrect current passwords, unchanged/all-whitespace replacements and
concurrent hash changes are rejected. Successful changes return `204` with
`Cache-Control: no-store`, clear the browser session and return to Login.
The endpoint changes only the authenticated user; target-user fields are rejected.

Management tokens carry an HMAC-derived password version, so both self-service
changes and admin resets invalidate earlier sessions. Tokens predating this
version are rejected; sign in again after updating. Password-change audit
capture stores metadata only. User Management copy now tries a clipboard
fallback and displays a manual-copy message when copying fails.

Admin reset remains the fallback for forgotten passwords. Forced first-login
replacement, temporary-password expiry, throttling, compromised-password
screening and recovery remain unfinished. The older schema-only preview was
not applied and should be revisited against the current implementation. See
`work-computer-handoff.md` and section 6 of `open-work-backlog.md`.

## Apps

These endpoints now power `/apps` and `/apps/[clientId]`. The list supports
search, pagination, admin-only create, delete, connector/policy counts, and row navigation.
The detail route provides Overview, Connectors, Policies, and Runtime Test
tabs.

Developers see only apps linked through `app_users` with the active app
developer role. App creation is system-admin-only. Linked app developers can
mutate their assigned apps; system admins can access every app. Only system
admins can submit `authorized`, change `guardrail_llm_config_id`, or mutate global policy
assignments. Normal developer-facing app detail screens currently hide direct
LLM editing; app LLM metadata remains a backend/admin concern until the
workflow is confirmed.

Developer update bodies must omit `authorized`; even unchanged values or null
return 403, and mixed requests are rejected before other fields are assigned.
Administrators can enable/disable through `PUT /apps/{app_id}`. The client-ID
alias has no general app metadata PUT route. Existing developer API name/client-ID
edits remain available and do not restore runtime access to a disabled app.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/apps` | List client apps |
| `POST` | `/apps` | Create a client app |
| `GET` | `/apps/{app_id}` | Get app by numeric ID |
| `GET` | `/apps/by-client-id/{client_id}` | Get app by readable client ID |
| `PUT` | `/apps/{app_id}` | Update app |
| `POST` | `/apps/{app_id}/api-key` | Regenerate and display one app API key once |
| `POST` | `/apps/by-client-id/{client_id}/api-key` | Regenerate by readable client ID |
| `DELETE` | `/apps/{app_id}` | Delete app |
| `GET` | `/llm-configs` | System-admin-only model catalogue without credentials |
| `POST` | `/llm-configs` | System-admin-only Azure LLM metadata creation with an env reference |
| `GET` | `/apps/{app_id}/llm-grants` | List this app's grants, including disabled rows, without credential references |
| `GET` | `/apps/{app_id}/llm-options?purpose=main` | Read enabled, valid choices and default approval for `main` or `guardrail` |
| `PUT` | `/apps/{app_id}/llm-grants/{purpose}/{config_ref}` | System-admin-only explicit grant enable/disable; config reference is an ID or `default` |
| `DELETE` | `/apps/{app_id}/llm-grants/{purpose}/{config_ref}` | System-admin-only revocation retaining a disabled row |

All grant/options routes also exist under `/apps/by-client-id/{client_id}` and
use the same app access checks. Grant PUT requires an explicit boolean `enabled`;
unknown fields are rejected. Developers cannot create/re-enable/revoke grants,
including when their app link role is admin/owner. System admins need no app
membership, but must explicitly grant a choice before selecting it.

Every explicitly supplied app model selection needs an enabled app/purpose
grant, including null and unchanged values. Missing/unavailable choices return
generic 403 responses before any field mutation; grant-store failures return
generic 503 responses. Omitted selections are untouched. New apps must be
created without named selections, then granted choices and updated separately.
Null initial values do not create environment-default grants. Removing a grant
does not silently change selections or prevent ordinary app metadata edits.

LLM metadata creation rejects unapproved endpoints with HTTP 400. Runtime
construction rechecks stored endpoints and returns a controlled HTTP 503 when
approval is missing. `AZURE_OPENAI_ENDPOINT` is automatically approved; extra
exact HTTPS origins require backend `GMS_ALLOWED_LLM_ENDPOINTS` and a restart.
Runtime model clients refuse redirects. The reusable app LLM settings component
restricts Add Configuration to administrators, but is currently unmounted by
application routes; management API provisioning and assignment remain available.
LLM credential names require backend approval in
`GMS_ALLOWED_LLM_CREDENTIAL_ENV_VARS`; `AZURE_OPENAI_API_KEY` is approved
automatically. Provisioning validates names without reading secret values.
Invalid references return 400; invalid granted configurations are excluded from
app options. The unmounted selector now uses separate app-scoped options for
each purpose and disables unavailable choices. It is not mounted by a route.
008c checks live grants on every runtime build request, including warm caches
and disabled caching, and validates legacy credential references before lookup.
Unavailable runtime model grants/credentials return a generic 503. Before
rollout, administrators must review and grant both named/default selections;
PostgreSQL and browser verification remain open. Auth-check remains identity-only.

Create app body:

```json
{
  "name": "Finance Bot",
  "authorized": true,
  "main_llm_config_id": null,
  "guardrail_llm_config_id": null
}
```

Important frontend behavior:

- The backend generates GUID-format client IDs and app API keys. Users do not
  type either value when creating apps.
- Create and regenerate responses return the plaintext API key once with a
  notice to copy it before closing the UI.
- GMS stores only the SHA-256 key hash. Lost keys cannot be recovered; users
  must regenerate them, which invalidates the previous key.
- Store the plaintext API key in the consuming app backend `.env`; never expose
  it to end users or commit it.
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

New links and explicit `credential_reference` fields are system-admin-only,
including null/blank/unchanged values. Linked developers can toggle/unlink
existing links and POST an upsert without that field; omitted credentials are
preserved for admins too. Creating a link without credentials still requires an
admin, preventing delete/relink from switching to the shared default PAT.
The frontend disables provisioning controls for developers.

Create/update body:

```json
{
  "connector_name": "github",
  "credential_reference": "env:APP_A_GITHUB_PAT",
  "enabled": true
}
```

Runtime behavior:

- `credential_reference="env:APP_A_GITHUB_PAT"` reads that PAT only after its name
  is approved in backend `GMS_ALLOWED_GITHUB_CREDENTIAL_ENV_VARS`.
- A blank credential reference falls back to `GITHUB_PERSONAL_ACCESS_TOKEN`.
- The default PAT name is automatically approved. Extra names are exact and
  comma-separated; wildcard/unsupported references are rejected. Restart the
  backend after approval changes because MCP clients are cached.
- Invalid/unapproved GitHub API writes return 400. Runtime checks existing rows;
  unapproved/missing credentials return a generic setup 503 before model/MCP startup.
- `vault:...` is not supported. Other connector types remain metadata-only.

## Policies

Use these for the policy library screen.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/policies` | List reusable policies |
| `POST` | `/policies` | Create a reusable policy and auto-compile it |
| `GET` | `/policies/{policy_id}` | Get one policy |
| `PUT` | `/policies/{policy_id}` | Update policy and auto-refresh compiled rules |
| `DELETE` | `/policies/{policy_id}` | Admin-only delete of an unassigned reusable policy definition |
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

`DELETE /policies/{policy_id}` returns `409` with
`code: policy_still_assigned` when the policy is still referenced by any
global or app assignment. Developers should normally delete assignments, not
the reusable policy definition. A future admin force-delete flow can remove
assignment references first if the organization wants that behavior.

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
- `block_stage`
- `block_reason`
- `blocked_policy_id`
- `blocked_policy_name`
- `tool_names`
- `input_policy_count`
- `input_rule_count`
- `output_rule_count`
- `blocked_tools`
- `history_truncated`

Runtime Test formats confirmed provider filtering as
`blocked (Azure: category)` and NeMo/deterministic enforcement as
`blocked (GMS)`. If Azure does not report a category, show `blocked (Azure)`.
When `block_reason` is present, show it near the guarded response so developers
can see why the request or output was stopped, for example "Blocked due to
request to merge a GitHub pull request."

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
