# Guardrails Management System Target Architecture

## PR Branch Conditions - Patch 019

The input selector contract now includes bounded source/target equality and
inequality with AND for PR creation and merge policies. Immutable parsed
comparisons are reused across compilation and execution; canonical selectors
remain in existing conditions JSON. New conjunction/inequality uses format 2;
existing single equality uses format 1. No table migration is added.
Creation checks head/base arguments. Merge checks trusted PR metadata but refuses
nonmatching conditional merges because the pinned connector lacks an atomic
target-branch precondition. Selective merge capability remains unfinished.
See [019 design and verification](branch-routing-patch-019.md).

## Current Security Foundation - 2026-10-16

Patches 010-018 are implemented; source uses Next.js 16 rather than the historical
Next.js 13 choice below. Existing app/connector/policy architecture and ACI ports
are retained. Users add `must_change_password` (false for existing accounts) and
nullable `temporary_password_expires_at`. New/reset accounts require a personal
password within 24 hours; setup-only JWTs can read their identity and replace the
password, and cannot access management CRUD/runtime testing. Password replacement
atomically clears setup state and invalidates old sessions.

A single explicit schema helper also adds a composite conversation tail index.
Membership backfill never grants all-to-all access. Throttling matches the current
single-process backend; scaling requires a shared limit. Request/history bounds,
verification results and operational limits are in the
[completion report](security-run-2026-10-16.md). No live schema/data rollout ran.
## Current Input Selector Storage - 2026-10-15

009c1 validates new input selectors against the supported GitHub action/field
subset and stores canonical field equality text plus integer
`resource_condition_version: 1` in existing conditions JSON. Path/branch case is
preserved; title/repository-name case folds without dropping literal punctuation
or Unicode. No schema migration is introduced. Unreviewed legacy literals are
excluded from automatic definition reuse/deduplication; ambiguous old values
require explicit review rather than automatic conversion.

This marker describes serialization, not runtime enforcement or admin approval.
009c2a's immutable snapshot reader and 009c2b's execution contract/compiler changes
are implemented and offline-checked. Conditional artifacts name actual fields and
literals; broad input combinations pass the supported-write capability gate too.
009c2c connects the matcher/catalogue and snapshots to runtime/cache. Rails,
tools, attribution and output phrases use one validated immutable snapshot;
exact contents are rechecked before reuse, after lock waits and after builds.
Indeterminate targets produce controlled evaluation errors without a false policy
match. 009c3a now validates/canonicalizes primary and related AI input selectors
through the storage capability gate, clears all drafts for unsupported conditions
or changed related scope, and filters authoring options to enabled supported
writes with conditional field names. 009c3b now uses those fields in modal help
and submission availability, aligns authoring mocks and supported/unsupported
samples, and preserves selector text through existing submit/edit paths. Planned
009 source work/offline verification is complete; patch 010 is next. See the single backlog for the supported
subset, checks and outstanding live-policy/PostgreSQL verification.

## Current Authoring Slice - 2026-10-09

The implemented management plane now offers live GitHub input drafting and
connector-independent output drafting. Output previews use
`Output -> Custom resource` and existing `conditions.output_rule` storage;
generation requires review and never saves a policy or executes connectors.
This addition does not implement SharePoint, Outlook or other-connector input
authoring and does not change the target schema or runtime topology below.
See `frontend-api-map.md` and `open-work-backlog.md` for current scope.

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
- The ACI frontend listens directly on public HTTP port `80`, proxies
  same-origin `/api/gms` requests to private backend port `8000` over
  `localhost`, and does not rely on unsupported ACI port remapping.

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
The model boundary supports the existing Azure API and an approved
openai_compatible chat API profile. A separately operated gateway translates
native provider APIs (for example Gemini or Claude); GMS does not infer a native
protocol from a URL. Both runtime choices retain purpose grants and independent
selection. Compatible classifiers validate complete yes/no decisions before
NeMo parses them. See model-gateway-integration.md for gateway controls and
required live model acceptance tests.

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
Existing profile names and usernames initially default to the user's email and
can be changed later through authenticated Settings.

```text
id
email
name
username
password_hash
system_role
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

Active app-link role:

```text
admin
```

Current implementation status: active. App creation is system-admin-only.
Linked developers use the internal `admin` app role and can manage their
assigned apps; system admins bypass app membership. Legacy `owner` links are
still treated as app-developer links for compatibility, but new UI/API flows do
not create owner or viewer links.

Management identities now also have a system-wide `developer` or `admin` role.
Public signup is disabled. System admins create users, issue one-time
temporary passwords, reset passwords, block/enable users, and link users to
apps through `/management-users` and the frontend `/user-management` tab.

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

The prototype now lists and creates Azure or standard compatible `llm_configs` through the
API. Credential references are limited to backend `env:VARIABLE_NAME` values;
raw LLM keys are never accepted by or returned to the frontend.

The former temporary `client_apps` table is now the target `apps` table.

The additive foundation schema is created by:

```powershell
python scripts/migrate_client_app_foundation.py
```

It initially created empty tables. App CRUD, API-key hashing, reusable app
authentication, management email/password login, and protected runtime proof
endpoints are now implemented. Management CRUD authorization, API-key rotation,
and production secrets-manager integration remain unfinished.

Current credential-storage decisions:

```text
users.password_hash              -> password hash, never plaintext password
apps.api_key_hash                -> API-key hash, never plaintext API key
llm_configs.credential_reference -> secrets-manager reference, never LLM key
```

### app_llm_grants

Patch 008a adds the ORM/storage foundation for explicit app-specific model use.
Each row identifies an app, a constrained `main` or `guardrail` purpose, and a
named `llm_config_id`; null explicitly identifies the Azure environment default.
`enabled` defaults to false. Separate unique indexes prevent duplicate named
and default grants for an app/purpose. Foreign keys cascade on app/configuration
deletion, and rows carry created/updated timestamps.

`scripts/migrate_app_llm_grants.py` previews DDL and a selection inventory with
approval off. Schema creation and reviewed-manifest seeding require separate
explicit apply flags. The helper never changes existing grants or app selections.
No live migration has been run. Startup table creation may create this additive
table but must not seed grants.

008b adds admin-managed grant APIs, app/purpose options and management selection
checks using shared validation helpers. Null/default and unchanged explicit
choices need grants too; app creation does not grant model access. DELETE
retains a disabled row so bootstrap replay cannot restore access.
008c enforces both purpose grants on every runtime build request, including
warm-cache and cache-disabled paths. The validated model/grant snapshot is part
of cache reuse checks and is rechecked after lock waits and construction. Legacy
credential references are validated before lookup; unavailable model access
returns a generic setup 503. The unmounted selector uses app-scoped options.
Offline checks passed; PostgreSQL and browser verification remain open. No live
migration or deployment has been run. Already admitted requests may finish
after concurrent revocation; environment/credential changes require restart.
Existing selections require explicit administrator review before rollout; never
grant all apps every configuration. See the single design and migration/rollback
plan in `open-work-backlog.md#008-app-specific-modelcredential-grants`.

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

For developer convenience, the API also exposes a `client_id` alias:

```text
/apps/by-client-id/{client_id}/policy-assignments
```

This resolves the app first and stores the same `app_id` relationship.

### global_policy_assignments

Mandatory rules applied to every app.

```text
id
policy_id
enabled
```

Global rules cannot be overridden by linked app developers.

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
completed: make prompts.yml generic and DB-policy driven
completed: automate policy CRUD compilation and invalidation
completed: add allowed/blocked HTTP runtime integration coverage
completed: enforce app connector access during runtime construction
completed: add app connector management APIs
completed: resolve env:VAR_NAME connector credentials through credential_reference
next:      add production secrets-manager credential resolution
```

See `docs/open-work-backlog.md` for the active backlog and unfinished
implementation slices.
