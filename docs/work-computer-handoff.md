# Work Computer Handoff - 2026-06-16

## Read This First

This file records the exact home-computer project state to continue from on the
work computer.

Also follow the repository-level rules in `AGENTS.md`, especially the
requirement to preview exact non-doc code diffs and wait for approval.

Before starting new implementation:

```powershell
git pull
docker compose up -d postgres
python tests/test_app_auth_http.py
python tests/test_policy_assignment_api.py
python tests/test_policy_auto_compile.py
python tests/test_guardrails_run_http.py
python tests/test_runtime_connector_access.py
python tests/test_app_connector_api.py
python tests/test_runtime_connector_credentials.py
python tests/test_app_policy_scope.py
python tests/test_tool_guard.py
python tests/test_nemo_mcp.py
```

Before leaving the home computer, make sure this milestone is committed and
pushed. The work computer cannot see unpushed local files:

```powershell
git status
git add .
git commit -m "Prepare backend and frontend handoff for GMS demo"
git push
```

Review `git status` before committing and confirm `.env` is not staged.

The work computer may use Postgres host port `5432`. The home computer uses
host port `5433` because Windows PostgreSQL already owns `5432`. Keep each
computer's local `.env` correct and never commit it.

GitHub MCP read/write mode is controlled from `.env`:

```env
GITHUB_MCP_READ_ONLY=1  # safe default for scripted tests
GITHUB_MCP_READ_ONLY=0  # manual local write testing
```

Restart `scripts/run_api.py` after flipping this value. The committed
`.env.example` keeps the safe read-only default.

## Current Milestone

The authenticated, app-scoped runtime foundation is implemented:

```text
X-App-ID + X-API-Key
-> require_authenticated_app
-> authenticated AppRecord
-> app-scoped global + app policy assignments
-> app-scoped compiled NeMo prompt rules
-> app-scoped blocked MCP tool names
```

App/global policy assignment POST bodies now use `policy_ids`, so one endpoint
handles both single and bulk assignment. Bulk update/delete also uses
`policy_ids` and returns `404` if a requested policy is not assigned in that
scope:

```json
{
  "policy_ids": [26, 12, 13],
  "enabled": true
}
```

Assignment responses include readable app and policy labels beside numeric IDs
for Swagger and the future frontend.

Developer-friendly client-ID aliases are also available:

```text
GET  /apps/by-client-id/{client_id}
GET  /apps/by-client-id/{client_id}/policy-assignments
POST /apps/by-client-id/{client_id}/policy-assignments
PUT  /apps/by-client-id/{client_id}/policy-assignments/{assignment_id}
DELETE /apps/by-client-id/{client_id}/policy-assignments/{assignment_id}
GET  /apps/{app_id}/effective-policy-assignments
GET  /apps/by-client-id/{client_id}/effective-policy-assignments
```

These routes resolve `client_id` to the internal app ID and then use the same
assignment logic. The effective-policy routes are read-only summaries that show
mandatory global assignments and app-specific assignments for one app together.

Policy create/update now refreshes `compiled_policy_rules` automatically.
Old compiled rows are marked stale and disabled, and a fresh active row is
created when the policy remains enabled. `POST /policies/compile-rules` remains
available as a manual full resync/debug endpoint.

`POST /v1/guardrails/run` now builds that runtime context and executes the
submitted message through the reusable guarded flow. It also supports hybrid
conversation history: stored turns for `(app_id, conversation_id)` are loaded
when available, client-supplied `conversation_history` bootstraps a new
conversation, and older turns are trimmed by `NEMO_MAX_RUNTIME_CONTEXT_CHARS`
before the agent sees them.

Reusable single-request guardrail coordination is also implemented:

```text
execute_guarded_message()
-> NeMo input rail
-> stop before action execution when blocked
-> otherwise run LangChain agent with guarded MCP tools
-> return status=tool_error when a connector tool raises ToolException
-> NeMo output rail
-> return controlled blocked response when Azure filters output self-check
-> GuardedExecutionResult
```

`tests/test_nemo_mcp.py` calls this reusable function and still prints the
same detailed terminal workflow. The full read-only NeMo + GitHub MCP run
passed after the extraction.

`tests/test_guardrails_run_http.py` now proves authenticated
`POST /v1/guardrails/run` uses real temporary DB app assignments,
`compiled_policy_rules`, app-scoped prompt rules, and app-scoped blocked tools.
It fakes rails/agent so it does not start Docker, GitHub MCP, or Azure.

Runtime now checks `app_connectors` before building GitHub MCP tools. An app
must have an enabled link to the enabled GitHub connector, or `/run` returns
`403` before Docker/Azure/MCP startup.

App connector links can now be managed through HTTP instead of SQL:

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

`credential_reference="env:VAR_NAME"` is executable for GitHub PAT selection.
Blank references fall back to `GITHUB_PERSONAL_ACCESS_TOKEN`; `vault:...`
remains future production work.

Frontend planning docs are ready:

```text
docs/frontend-api-map.md
docs/frontend-screen-plan.md
docs/frontend-demo-flow.md
```

The first frontend backend-integration slice is also in place. The
`/policies` page now has a typed client-side API adapter:

```text
frontend/lib/api-client.ts
frontend/app/policies/page.tsx
frontend/.env.example
```

By default, the deployed/mock frontend still uses local mock policy data. To
switch local development to real FastAPI data, create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Then restart the frontend with `npm run dev:clean`. With the API base URL set,
`/policies` reads:

```text
GET /apps
GET /global-policy-assignments
GET /apps/by-client-id/{client_id}/effective-policy-assignments
```

Create/edit/delete buttons are still local UI behavior and are not wired to the
backend yet.

## Important Current Files

- `src/nemo_mcp_guardrails/app_auth.py`: API-key hashing and app verification.
- `src/nemo_mcp_guardrails/api/auth.py`: `require_authenticated_app`.
- `src/nemo_mcp_guardrails/api/runtime.py`: protected auth-check and run endpoints.
- `src/nemo_mcp_guardrails/api/runtime_schemas.py`: runtime request/execution response models.
- `src/nemo_mcp_guardrails/database/conversation_store.py`: conversation history load/append helpers.
- `src/nemo_mcp_guardrails/database/models.py`: includes `conversation_messages`.
- `src/nemo_mcp_guardrails/runtime_factory.py`: Azure, NeMo, MCP, and agent construction. It uses the authenticated app's `guardrail_llm_config_id` for NeMo rails and `main_llm_config_id` for the LangChain agent, with `.env` Azure fallback when either ID is missing.
- `src/nemo_mcp_guardrails/guarded_execution.py`: reusable single-request guardrail workflow.
- `src/nemo_mcp_guardrails/tool_guard.py`: app-scoped execution-level MCP tool guard.
- `tests/test_nemo_mcp.py`: full read-only integration runner and terminal display.
- `tests/test_app_auth_http.py`: protected HTTP boundary and runtime-execution reachability test.
- `tests/test_guardrails_run_http.py`: app-scoped allowed/blocked `/run` HTTP integration test with fake rails/agent and real DB scope.
- `tests/test_runtime_connector_access.py`: isolated runtime connector access check for linked, unlinked, and disabled-link apps.
- `tests/test_app_connector_api.py`: app connector CRUD API test for app ID
  and client ID routes.
- `tests/test_runtime_connector_credentials.py`: env-based GitHub PAT
  reference resolution test.
- `tests/test_app_policy_scope.py`: real temporary app-assignment scope test.

## Verified Current Results

```text
service app authentication: passed
HTTP app authentication: passed
authenticated runtime execution reachability: passed
runtime LLM selection: passed
conversation history storage/reload/truncation: passed
oversized latest-message rejection: passed
controlled connector tool-error responses: passed
controlled Azure output-filter responses: passed
authenticated /run allowed/blocked app-scope HTTP coverage: passed
runtime connector access enforcement: passed
temporary authentication rows cleanup: passed
temporary app policy-scope rows cleanup: passed
App A issue_write blocked / App B issue_write allowed: passed
tool guard isolated checks: passed
full read-only NeMo + GitHub MCP test: passed
Python compilation: passed
git diff --check: passed
```

The full runner still displays:

```text
NEMO INPUT RAIL RESULT
REQUEST STOPPED BEFORE ACTION EXECUTION, when blocked
MCP TOOLS CALLED, when allowed
NEMO OUTPUT RAIL RESULT
FINAL RESPONSE
```

The output looks unchanged because only coordination moved from the test loop
into `execute_guarded_message()`.

## Exact Next Implementation Step

Read `docs/open-work-backlog.md` first. It is the source of truth for
unfinished plans and prevents half-completed ideas from being lost between
machines.

Immediate top priority: continue the Next.js 13 frontend MVP for the GitHub MCP
demo. The first frontend scaffold now exists in `frontend/` and recreates the
uploaded Figma pages:

```text
/login
/signup
/policies
/settings
```

Run it with:

```powershell
cd frontend
npm install
npm run dev:clean
```

Open:

```text
http://127.0.0.1:3000/policies
```

`npm run build` passed on the work computer. If Codex sandboxing blocks Next's
worker process with `spawn EPERM`, rerun the build outside the sandbox.

To use backend data locally, also run the API:

```powershell
.\.venv\Scripts\python.exe scripts\run_api.py
```

Then add `frontend/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Recommended incremental slice:

```text
1. Read docs/frontend-api-map.md.
2. Read docs/frontend-screen-plan.md.
3. Read docs/frontend-demo-flow.md.
4. Wire `/policies` create to `POST /policies` plus app/global assignment endpoints.
5. Wire edit/delete buttons to policy and assignment update/delete endpoints.
6. Implement `/apps` with list/create/edit behavior.
7. Implement `/apps/[clientId]` with the Connectors tab first.
8. Wire GitHub connector linking with credential_reference="env:VAR_NAME".
9. Add app policy assignment and runtime tester tabs after connector flow works.
```

Keep `GITHUB_MCP_READ_ONLY=1` for scripted tests. Do not add write-capable
endpoint testing to the normal harness.

## Boundaries Not Yet Implemented

- Admin CRUD endpoints are not authenticated.
- User login and role authorization are not implemented.
- Connector credentials and LLM credentials are not managed through a secrets
  manager yet.
- Argument-level and workflow-state policies are not implemented.

## Editing Rules

- Preview exact non-doc code diffs and wait for user approval.
- Docs-only updates can be applied directly.
- Add short docstrings to new Python functions/classes.
- Update relevant docs after every completed change.
- Never commit `.env`, real API keys, PATs, or plaintext connector credentials.
