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
-> scripts/test_nemo_mcp.py terminal output
```

Completed pieces:

- The additive client-app foundation migration has created empty `users`,
  `llm_configs`, and `apps` tables.
- The connector terminology migration has renamed the former connector-shaped
  `apps` metadata to `connectors`, including related actions, resources, tool
  mappings, policy fields, and allowed-test joins.
- `app_users` and `app_connectors` now model user ownership/roles and
  app-specific connector access.
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
- `scripts/test_nemo_mcp.py` injects DB compiled prompt rules into NeMo config.
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
  `scripts/test_nemo_mcp.py` consumes its structured result and preserves the
  existing terminal workflow display.
- `scripts/test_app_auth_http.py` verifies the protected HTTP boundary and
  cleans up all temporary app rows.
- `scripts/test_guardrails_run_http.py` verifies authenticated `/run` loads
  real app-scoped policy assignments, compiled prompt rules, and blocked tools
  while using fake rails/agent to avoid Docker and Azure.
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
.\.venv\Scripts\python.exe -m py_compile src\nemo_mcp_guardrails\app_auth.py src\nemo_mcp_guardrails\guarded_execution.py src\nemo_mcp_guardrails\api\auth.py src\nemo_mcp_guardrails\api\runtime.py src\nemo_mcp_guardrails\api\runtime_schemas.py src\nemo_mcp_guardrails\policy_compiler.py src\nemo_mcp_guardrails\policy_rule_service.py src\nemo_mcp_guardrails\tool_guard.py src\nemo_mcp_guardrails\database\models.py src\nemo_mcp_guardrails\database\policy_loader.py src\nemo_mcp_guardrails\database\test_case_loader.py src\nemo_mcp_guardrails\database\prompt_rule_loader.py src\nemo_mcp_guardrails\prompt_rule_compiler.py scripts\seed_normalized_policy_metadata.py scripts\test_nemo_mcp.py scripts\test_tool_guard.py scripts\test_policy_loader.py scripts\test_app_policy_scope.py scripts\test_app_auth.py scripts\test_app_auth_http.py scripts\test_policy_auto_compile.py scripts\test_guardrails_run_http.py scripts\debug_nemo_self_check.py scripts\debug_nemo_output_check.py
.\.venv\Scripts\python.exe scripts\seed_normalized_policy_metadata.py
.\.venv\Scripts\python.exe scripts\test_policy_loader.py
.\.venv\Scripts\python.exe scripts\test_policy_loader.py --app-id 999999
.\.venv\Scripts\python.exe scripts\test_app_policy_scope.py
.\.venv\Scripts\python.exe scripts\test_app_auth.py
.\.venv\Scripts\python.exe scripts\test_app_auth_http.py
.\.venv\Scripts\python.exe scripts\test_policy_auto_compile.py
.\.venv\Scripts\python.exe scripts\test_guardrails_run_http.py
.\.venv\Scripts\python.exe scripts\test_tool_guard.py
.\.venv\Scripts\python.exe scripts\test_nemo_mcp.py
.\.venv\Scripts\python.exe scripts\test_nemo_mcp.py --app-id 999999
```

Expected `scripts/test_nemo_mcp.py` proof lines:

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

The immediate top priority is to enforce app connector access during runtime
construction.

Recommended slice:

```text
1. Check `app_connectors` for the authenticated app before GitHub MCP tools are built.
2. Return a clear runtime error if the app is not linked to the GitHub connector.
3. Keep `.env` token usage for now, but leave the hook for future `credential_reference` resolution.
4. Add a fake-runtime or isolated service test proving linked apps can proceed and unlinked apps are rejected.
```

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
- `docs/runtime-flow-map.md`
- `docs/project-context.md`
- `docs/policy-schema-design.md`
- `docs/testing-notes.md`
- `docs/troubleshooting.md`
- `scripts/test_nemo_mcp.py`
- `scripts/seed_normalized_policy_metadata.py`
- `src/nemo_mcp_guardrails/policy_compiler.py`
- `src/nemo_mcp_guardrails/database/policy_loader.py`
- `src/nemo_mcp_guardrails/prompt_rule_compiler.py`
- `src/nemo_mcp_guardrails/guarded_execution.py`
- `src/nemo_mcp_guardrails/api/runtime.py`
- `src/nemo_mcp_guardrails/api/auth.py`

Before switching machines, commit and push the current milestone. Confirm
`.env` is not staged.
