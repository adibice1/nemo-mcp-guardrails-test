# Next Steps

## Current Milestone

The current prototype is now DB-backed through the main guardrail path:

```text
Postgres policies
-> policy_loader.py
-> policy_compiler.py
-> compiled_policy_rules
-> prompt_rule_loader.py
-> prompt_rule_compiler.py
-> config/prompts.yml template
-> NeMo input/output rails
-> tests/test_nemo_mcp.py terminal output
```

Completed pieces:

- The additive client-app foundation migration has created empty `users`,
  `llm_configs`, and `apps` tables.
- The connector terminology migration has renamed the former connector-shaped
  `apps` metadata to `connectors`, including related actions, resources, tool
  mappings, policy fields, and allowed-test joins.
- `app_users` and `app_connectors` now model user ownership/roles and
  app-specific connector access.
- Runtime construction checks `app_connectors` before GitHub MCP tools are
  built.
- `app_policy_assignments` and `global_policy_assignments` now reference the
  reusable policy definitions already stored in `policies`.
- FastAPI now exposes client-app CRUD, nested app-policy-assignment CRUD, and
  global-policy-assignment CRUD.
- GitHub MCP full-run tests stay read-only with `GITHUB_READ_ONLY=1`.
- NeMo input and output rails are enabled.
- Input/output rail diagnostics now use the same DB-injected prompt
  configuration as the full runner and distinguish a NeMo decision from an
  Azure `content_filter` block.
- The latest home-computer diagnostic run passed fully through NeMo: the safe
  input/output cases passed, and write, credential, fake-token, and fake
  environment-variable cases were blocked by NeMo.
- `tests/test_nemo_mcp.py` injects DB compiled prompt rules into NeMo config.
- FastAPI now has a reusable `require_authenticated_app` dependency that reads
  `X-App-ID` and `X-API-Key` and rejects every invalid case with the same
  generic `401`.
- `GET /v1/guardrails/auth-check` proves invalid requests are rejected before
  loading policies, rails, Docker, or MCP tools.
- `POST /v1/guardrails/run` now authenticates the caller, builds app-scoped
  rails and read-only guarded GitHub MCP tools, calls `execute_guarded_message()`,
  and returns a JSON execution response.
- `/v1/guardrails/run` now supports hybrid conversation history. Stored
  `conversation_messages` are loaded by `app_id + conversation_id`; client
  `conversation_history` bootstraps new conversations; older turns are trimmed
  by `NEMO_MAX_RUNTIME_CONTEXT_CHARS`.
- `src/nemo_mcp_guardrails/guarded_execution.py` now coordinates one message
  through the input rail, early block, agent/guarded tools with trimmed history,
  and output rail.
  `tests/test_nemo_mcp.py` consumes its structured result and preserves the
  existing terminal workflow display.
- `tests/test_app_auth_http.py` verifies the protected HTTP boundary and
  cleans up all temporary app rows.
- `tests/test_guardrails_run_http.py` verifies authenticated `/run` loads
  real app-scoped policy assignments, compiled prompt rules, and blocked tools
  while using fake rails/agent to avoid Docker and Azure.
- `tests/test_runtime_connector_access.py` verifies linked apps are allowed
  and unlinked or disabled-link apps are rejected before MCP construction.
- Runtime input policies come from Postgres through `policy_loader.py`.
- Policy and compiled-rule loaders now accept an optional app ID. App-scoped
  calls load enabled global assignments plus enabled assignments for that app.
- No-app calls intentionally preserve the current all-enabled testing behavior
  and the main test runners print a warning explaining that production must
  require an authenticated app ID.
- `tool_guard.py` blocks DB-derived restricted tool names before execution.
- `blocked_tool_names_for_app(app_id=...)` compiles an optional per-app
  blocked-tool set, and `guard_mcp_tool(..., blocked_tool_names=...)` applies
  that same set to each wrapped MCP tool.
- Allowed read tests come from `allowed_test_cases`, with fallback defaults.
- Blocked tests are generated from enabled DB policies.
- FastAPI exposes policy CRUD, allowed-test CRUD, compile-preview, compile-rules, and compiled-rules endpoints.
- Policy create/update automatically refreshes `compiled_policy_rules`;
  `compile-rules` remains a manual full-resync/debug endpoint.
- Normalized metadata tables now exist in SQLAlchemy models.
- `scripts/seed_normalized_policy_metadata.py` seeds:
  ```text
  connectors: global, github
  connector_actions: 11
  connector_resources: 10
  connector_tool_mappings: 33
  allowed_test_case_expected_tools: 3
  ```

Home-laptop setup warning:

```text
DBeaver and DATABASE_URL must use localhost:5433 on the home computer.
The Docker Postgres container still listens on port 5432 internally.
Host port 5432 belongs to the home computer's Windows PostgreSQL service.
DBeaver does not read .env and needs no VS Code extension.
Postgres Docker volumes retain their original database password.
Changing POSTGRES_PASSWORD in .env does not update an existing volume.
```

If DBeaver rejects the correct-looking password on another laptop, read
`docs/troubleshooting.md` under **Home Laptop: DBeaver Password Fails** before
changing project code.

## Current Verification Commands

Run these from the repo root:

```powershell
.\.venv\Scripts\python.exe scripts\migrate_client_app_foundation.py
.\.venv\Scripts\python.exe scripts\migrate_connector_terminology.py
.\.venv\Scripts\python.exe scripts\migrate_app_relationships.py
.\.venv\Scripts\python.exe scripts\migrate_policy_assignments.py
.\.venv\Scripts\python.exe -m py_compile src\nemo_mcp_guardrails\app_auth.py src\nemo_mcp_guardrails\guarded_execution.py src\nemo_mcp_guardrails\api\auth.py src\nemo_mcp_guardrails\api\runtime.py src\nemo_mcp_guardrails\api\runtime_schemas.py src\nemo_mcp_guardrails\policy_compiler.py src\nemo_mcp_guardrails\policy_rule_service.py src\nemo_mcp_guardrails\tool_guard.py src\nemo_mcp_guardrails\database\models.py src\nemo_mcp_guardrails\database\policy_loader.py src\nemo_mcp_guardrails\database\test_case_loader.py src\nemo_mcp_guardrails\database\prompt_rule_loader.py src\nemo_mcp_guardrails\prompt_rule_compiler.py scripts\seed_normalized_policy_metadata.py tests\\test_nemo_mcp.py tests\\test_tool_guard.py tests\\test_policy_loader.py tests\\test_app_policy_scope.py tests\\test_app_auth.py tests\\test_app_auth_http.py tests\\test_policy_auto_compile.py tests\\test_guardrails_run_http.py tests\\test_runtime_connector_access.py scripts\debug_nemo_self_check.py scripts\debug_nemo_output_check.py
.\.venv\Scripts\python.exe scripts\seed_normalized_policy_metadata.py
.\.venv\Scripts\python.exe tests\\test_policy_loader.py
.\.venv\Scripts\python.exe tests\\test_policy_loader.py --app-id 999999
.\.venv\Scripts\python.exe tests\\test_app_policy_scope.py
.\.venv\Scripts\python.exe tests\\test_app_auth.py
.\.venv\Scripts\python.exe tests\\test_app_auth_http.py
.\.venv\Scripts\python.exe tests\\test_policy_auto_compile.py
.\.venv\Scripts\python.exe tests\\test_guardrails_run_http.py
.\.venv\Scripts\python.exe tests\\test_runtime_connector_access.py
.\.venv\Scripts\python.exe tests\\test_tool_guard.py
.\.venv\Scripts\python.exe tests\\test_nemo_mcp.py
.\.venv\Scripts\python.exe tests\\test_nemo_mcp.py --app-id 999999
```

Expected `tests/test_nemo_mcp.py` proof lines:

```text
NeMo prompt policy rules loaded
- input rules from compiled_policy_rules: 4
- output rules from compiled_policy_rules: 1

Runtime input policies loaded
- DB policy #...

Allowed test cases loaded
- DB allowed test #...
```

Expected seed counts:

```text
Normalized policy metadata seeded.
- connectors: global, github
- github connector actions: 11
- github connector resources: 10
- github connector tool mappings: 33
- allowed test expected-tool links: 3
```

## Recommended Next Step

Use `docs/open-work-backlog.md` as the source of truth for unfinished work.

The backend is ready enough to begin the frontend MVP for the GitHub MCP demo.
The next implementation slice should be the Next.js 13 management UI, guided by:

```text
docs/frontend-api-map.md
docs/frontend-screen-plan.md
docs/frontend-demo-flow.md
```

Recommended frontend slice from the current state:

```text
1. Keep the existing Next.js 13 scaffold in `frontend/`.
2. Use `frontend/.env.local` with NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 for local backend mode.
3. Wire /policies create/edit/delete to `POST/PUT/DELETE /policies` and app/global assignment endpoints.
4. Implement /apps with list/create/edit behavior.
5. Implement /apps/[clientId] with the Connectors tab first.
6. Wire GitHub connector linking with credential_reference="env:VAR_NAME".
7. Add the Runtime Tester tab after the connector tab is working.
```

Current frontend status:

```text
frontend/ implements /login, /signup, /policies, and /settings
/policies uses mock data by default
/policies reads GET /apps, GET /global-policy-assignments, and
GET /apps/by-client-id/{client_id}/effective-policy-assignments when
NEXT_PUBLIC_API_BASE_URL is configured
create/edit/delete controls are not backend-wired yet
```

The app connector management API slice is complete. Developers can now link
apps to GitHub through HTTP instead of DBeaver.

Implemented endpoints:

```text
GET    /apps/{app_id}/connectors
POST   /apps/{app_id}/connectors
PUT    /apps/{app_id}/connectors/{connector_ref}
DELETE /apps/{app_id}/connectors/{connector_ref}

GET    /apps/by-client-id/{client_id}/connectors
POST   /apps/by-client-id/{client_id}/connectors
PUT    /apps/by-client-id/{client_id}/connectors/{connector_ref}
DELETE /apps/by-client-id/{client_id}/connectors/{connector_ref}
```

`connector_ref` accepts either a numeric connector ID or connector name such as
`github`. `credential_reference="env:VAR_NAME"` is now executable for GitHub
PAT selection. Production secrets-manager references such as `vault:...`
remain future work.

The normalized policy-reference migration is complete:

```text
policies.connector_id/action_id/resource_id backfilled
policy_loader.py prefers normalized relationships
compiled_policy_rules tracks policy_version and stale
policy create/update accepts readable names and resolves normalized IDs
policy create/update validates combinations against enabled tool mappings
policy create/update automatically refreshes compiled_policy_rules
allowed-test create/update accepts readable tool-name lists and maintains joins
users, llm_configs, and apps foundation tables exist
connector terminology migration complete
app_users and app_connectors relationship tables exist
runtime_factory.py enforces enabled app_connectors access before GitHub MCP construction
app_policy_assignments and global_policy_assignments exist
app and assignment CRUD endpoints exist
policy and compiled-rule loaders accept optional app IDs
tool guard accepts optional app-scoped blocked-tool sets
test_app_policy_scope.py verifies real temporary app assignments and cleanup
test_nemo_mcp.py accepts testing-only --app-id scope
app_auth.py verifies authorized client ID/API-key pairs
test_app_auth.py verifies valid and rejected cases with cleanup
api/auth.py provides reusable HTTP credential enforcement
GET /v1/guardrails/auth-check proves the protected runtime boundary
test_app_auth_http.py verifies valid and rejected HTTP cases with cleanup
test_guardrails_run_http.py verifies allowed/blocked app-scoped /run behavior
test_runtime_connector_access.py verifies runtime connector access enforcement
test_app_connector_api.py verifies app connector CRUD by app ID and client ID
test_runtime_connector_credentials.py verifies env:VAR_NAME PAT resolution
POST /v1/guardrails/run executes authenticated app-scoped guarded requests
runtime_schemas.py defines the run request and execution response
guarded_execution.py owns reusable single-request guardrail coordination
test_nemo_mcp.py prints GuardedExecutionResult while preserving terminal output
runtime_factory.py selects app main/guardrail LLM configs, then builds NeMo rails, read-only GitHub MCP tools, and the LangChain agent
```

Current assignment counts:

```text
app policy assignments: 0
global policy assignments: 1
```

The global assignment points to the connector-independent credential output
policy. Existing GitHub write policies remain unassigned.

Latest assignment-aware loader verification:

```text
legacy no-app scope: 4 input rules + 1 output rule
unassigned/nonexistent app scope: 0 input rules + 1 global output rule
temporary App A: issue_write blocked
temporary App B: issue_write allowed
temporary apps/assignments after cleanup: 0
valid authorized app credentials: accepted
wrong key / unknown client / unauthorized app: rejected
temporary authentication-test apps after cleanup: 0
missing headers / wrong key / unknown client / unauthorized app over HTTP: 401
valid authorized app over HTTP: accepted
temporary HTTP authentication-test apps after cleanup: 0
```

Latest foundation migration result:

```text
Client-app foundation migration complete.
- users: 0
- llm configs: 0
- apps: 0
```

The empty counts are expected. The migration establishes the schema only; seed
records and authentication endpoints belong to later slices.

Do not remove the old `policies.app`, `policies.action`, or
`policies.resource` columns yet. They remain the compatibility fallback while
policy creation and update flows are moved fully onto normalized IDs.

Metadata endpoints can now distinguish client apps from external connectors.

## After That

Once normalized policy loading is stable:

- Move more GitHub metadata out of hardcoded compiler constants and into DB metadata tables.
- Remove legacy policy text columns only after all policy writes use normalized IDs.
- Add argument-policy and workflow-policy schema slices.
- Keep write-capable MCP tests separate, opt-in, and pointed at a throwaway repo with a limited token.

## Files To Read First On Another Machine

- `docs/work-computer-handoff.md`
- `AGENTS.md`
- `docs/frontend-api-map.md`
- `docs/frontend-screen-plan.md`
- `docs/frontend-demo-flow.md`
- `docs/runtime-flow-map.md`
- `docs/project-context.md`
- `docs/policy-schema-design.md`
- `docs/testing-notes.md`
- `docs/troubleshooting.md`
- `tests/test_nemo_mcp.py`
- `scripts/seed_normalized_policy_metadata.py`
- `src/nemo_mcp_guardrails/policy_compiler.py`
- `src/nemo_mcp_guardrails/database/policy_loader.py`
- `src/nemo_mcp_guardrails/prompt_rule_compiler.py`
- `src/nemo_mcp_guardrails/guarded_execution.py`
- `src/nemo_mcp_guardrails/api/runtime.py`
- `src/nemo_mcp_guardrails/api/auth.py`

Before switching machines, commit and push the current milestone. Confirm
`.env` is not staged.
