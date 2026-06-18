# Guardrails Management System Target Architecture

## Status

This document records the confirmed target direction after supervisor review.
It describes the intended production Guardrails Management System (GMS), not
only the current GitHub research prototype.

The connector/app terminology migration has been completed. The current
database now uses `apps` for GMS client applications and `connectors` for
external integrations.

## Confirmed Product Decisions

- The GMS will primarily support GitHub and SharePoint, while remaining
  extensible to Outlook and other external tools.
- The near-term presentation/demo scope only needs GitHub MCP support.
  SharePoint, Outlook, and other connectors are lower-priority extensions.
- An **app** is a client application that consumes the GMS.
- A **connector** is an external system or tool integration used by an app,
  such as GitHub MCP, SharePoint, or Outlook.
- One app can use multiple connectors.
- One user can manage multiple apps, and one app can be managed by multiple
  users.
- The client app's main LLM and the GMS guardrail-classification LLM can be
  different.
- Mandatory global policies apply to every app and cannot be overridden by app
  owners.
- Prototype user authentication can use email and password.
- The GMS acts as a full proxy that owns the complete guarded agent sequence.
- Policy changes should automatically compile or invalidate their generated
  rules.
- Redis is a future optimization, not a current priority.
- The management frontend will use Next.js 13.

## Terminology

### App

A client application authorized to use the GMS.

Examples:

```text
Finance Assistant
Developer Support Bot
App A
App B
```

Each app has its own credentials, active policy assignments, connector access,
and LLM configuration.

### Connector

An external parent tool, MCP server, or integration that the GMS-controlled
agent can use.

Examples:

```text
github_mcp
sharepoint
outlook
```

The current database uses `connectors`, `connector_actions`,
`connector_resources`, and `connector_tool_mappings` for this concept.

### Policy Rule

A reusable rule definition independent of any one client app.

Example:

```text
GitHub + create + issue + block
```

### Policy Assignment

A link that applies one reusable policy rule to one client app.

Example:

```text
App A -> allow GitHub issue creation
App B -> block GitHub issue creation
```

Deleting App A's assignment must not delete the reusable rule or App B's
assignment.

## Full-Proxy Runtime Flow

```text
Client app sends request with app ID and API key
-> GMS authenticates app ID/API-key pair
-> verify app is authorized
-> load stored conversation history for the app conversation
-> bootstrap from client-supplied history when no stored history exists
-> trim older history to stay within the runtime context budget
-> load mandatory global policies
-> load app-specific policy assignments
-> load app connector access and credentials
-> load main-agent and guardrail LLM configurations
-> build NeMo rails with the selected guardrail LLM
-> build the GMS agent with the selected main-agent LLM
-> NeMo input rail checks user request
-> if passed, GMS agent decides whether to call a connector tool
-> tool guard checks proposed tool name, arguments, and context
-> if passed, external tool executes
-> tool result returns to GMS agent
-> agent generates final response
-> NeMo output rail checks final response
-> final safe response returns to client app and user
```

The tool guard is required even when input rails pass because it checks what the
agent actually attempts to execute, rather than only what the user appeared to
request.

Current implementation note: the runtime now respects separate
`main_llm_config_id` and `guardrail_llm_config_id` selections on each app.
Only Azure OpenAI-compatible provider rows are executable in the prototype.
Rows for providers such as Gemini can be stored as target metadata, but runtime
execution returns a clear unsupported-provider error until provider adapters are
implemented.

## Proposed Runtime Endpoint

The full-proxy entry point should be versioned:

```text
POST /v1/guardrails/run
```

Authentication:

```http
X-App-ID: <client app ID>
X-API-Key: <client app API key>
```

Example request:

```json
{
  "message": "Summarize the latest pull requests.",
  "conversation_id": "optional-conversation-id",
  "conversation_history": [
    {"role": "user", "content": "List recent pull requests."},
    {"role": "assistant", "content": "PR #1 and PR #2 are recent."}
  ]
}
```

Example response:

```json
{
  "status": "passed",
  "response": "Here is the pull request summary...",
  "history_truncated": false,
  "history_messages_received": 2,
  "history_messages_loaded": 0,
  "history_messages_used": 2,
  "matched_rule_ids": []
}
```

The endpoint must return safe refusal content when an input rail, tool guard,
or output rail blocks the sequence.

For the current implementation, runtime context sizing uses the configured
`NEMO_MAX_RUNTIME_CONTEXT_CHARS` character budget. If the latest message alone
exceeds that budget, the endpoint returns `413`. Otherwise, it keeps the newest
conversation history turns that fit and reports truncation metadata in the
response.

## Target Core Tables

### users

Developers or administrators who log into the Next.js management webapp.

```text
id
email
password_hash
enabled
created_at
updated_at
```

### apps

Client applications consuming the GMS.

```text
id
name
client_id
api_key_hash
authorized
main_llm_config_id
guardrail_llm_config_id
created_at
updated_at
```

API keys must be hashed, not stored as plaintext. Eventually, credentials
should use an organisation secrets manager.

### app_users

Many-to-many relationship between users and apps.

```text
user_id
app_id
role
```

Suggested future roles:

```text
owner
admin
viewer
```

Current implementation status: created. The relationship defaults to `viewer`
until role-management endpoints and validation are implemented.

### connectors

External parent tools and integrations.

```text
id
name
display_name
enabled
```

### app_connectors

Connectors enabled for each client app.

```text
app_id
connector_id
enabled
credential_reference
```

Different apps may use the same connector with different credentials and
permissions.

Current implementation status: created. `credential_reference` stores only a
reference to external secret storage, never the connector credential itself.

### connector_actions

Actions supported by one connector.

Examples:

```text
GitHub: create, merge, read
SharePoint: upload, download, share
Outlook: send, read, forward
```

### connector_resources

Resources supported by one connector.

Examples:

```text
GitHub: issue, pull_request, repository
SharePoint: file, folder, site
Outlook: email, attachment, calendar_event
```

### connector_tool_mappings

Maps valid connector/action/resource combinations to concrete MCP or API tool
names. Only supported capabilities need mapping rows.

### llm_configs

Configurable main-agent and guardrail-classification LLM definitions.

```text
id
name
provider
model_name
endpoint
credential_reference
enabled
```

Current implementation status:

```text
users       -> created
llm_configs -> created
apps        -> created
connectors  -> migrated from the former connector-shaped apps table
```

The former temporary `client_apps` table is now the target `apps` table.

The additive foundation schema is created by:

```powershell
python scripts/migrate_client_app_foundation.py
```

It initially created empty tables. App CRUD, API-key hashing, reusable app
authentication, and the first protected runtime proof endpoint are now
implemented. User login, API-key issuance/rotation workflows, and LLM
credential management are not implemented yet.

Current credential-storage decisions:

```text
users.password_hash              -> password hash, never plaintext password
apps.api_key_hash                -> API-key hash, never plaintext API key
llm_configs.credential_reference -> secrets-manager reference, never LLM key
```

### policy_rules

Reusable policy definitions.

```text
id
connector_id
action_id
resource_id
policy_type
effect
conditions
priority
version
enabled
```

### app_policy_assignments

Applies reusable policy rules to specific client apps.

```text
id
app_id
policy_id
enabled
created_at
updated_at
```

Current implementation status: created. It references the existing `policies`
table, which currently serves as the reusable policy-definition table.
FastAPI CRUD is available under `/apps/{app_id}/policy-assignments`. The POST
body accepts `policy_ids` so one endpoint handles both single and bulk
assignment. Existing assignments are updated in place instead of duplicating
rows.

### global_policy_assignments

Mandatory rules applied to every app.

```text
id
policy_id
enabled
```

Global rules cannot be overridden by app owners.

Current implementation status: created. The existing connector-independent
credential output policy is globally assigned. Existing GitHub write policies
remain unassigned until they are explicitly linked to an app or made global.
FastAPI CRUD is available under `/global-policy-assignments`. The POST body
also accepts `policy_ids` for single or bulk global assignment.

### compiled_policy_rules

Generated NeMo rule artifacts. These are derived data, while `policy_rules`
remain the source of truth.

## Policy Reuse Example

```text
Reusable rule R1:
GitHub + create + issue + block

App A assignments:
R1 disabled or absent

App B assignments:
R1 enabled
```

App A can create issues while App B cannot. Removing App B's assignment does
not delete R1.

## Automatic Policy Compilation

Manual calls to compile policy tables should not be required in the target
system.

```text
policy rule created or updated
or app/global assignment changed
-> increment rule version when appropriate
-> mark old compiled artifacts stale
-> compile current active rules
-> store compiled artifacts
-> invalidate runtime cache
```

The first implementation can compile synchronously inside the FastAPI service.
A background worker and Redis-backed invalidation can be introduced later.

## Management Webapp Flow

```text
User logs into Next.js 13 frontend
-> sees apps they are authorized to manage
-> selects App A
-> sees App A connectors and policy assignments
-> adds, removes, enables, or disables App A policies
-> changes affect App A only
```

## Recommended Conflict Rule

Recommended default:

```text
deny overrides allow
```

Examples:

```text
global block + app allow -> blocked
app block + app allow    -> blocked
```

This recommendation should be confirmed before implementing policy conflict
resolution.

## Low-Priority Future Enhancements

- Redis caching for app-specific active compiled rules.
- Policy-template reuse and deduplication optimization.
- Background compilation workers.
- Organisation SSO.
- Argument-level and workflow-state policies.
- Full audit and analytics platform.

## Immediate Migration Sequence

```text
completed: add users, llm_configs, and apps
completed: migrate connector metadata to connector terminology
completed: add app_users and app_connectors
completed: add app/global assignments referencing policies
completed: add client-app and assignment CRUD APIs
completed: add app-aware policy and prompt-rule loading
completed: add reusable app authentication and protected auth-check endpoint
completed: extract reusable single-request guarded execution
completed: execute authenticated POST /v1/guardrails/run through guarded runtime
completed: add conversation history persistence/truncation to runtime endpoint
completed: select separate app main-agent and guardrail LLM configs
next:      make prompts.yml generic and DB-policy driven
then:      add allowed/blocked HTTP runtime integration coverage
then:      automate policy compilation and invalidation
```

See `docs/open-work-backlog.md` for the active backlog and unfinished
implementation slices.
