# Work/Home Computer Handoff

## Current Deployment Milestone - 2026-08-28

The backend and frontend are ready to be built as separate Linux AMD64 images
for Azure Container Registry and Azure Container Instances:

```text
guardrail.azurecr.io/guardrail-be:latest  -> internal port 8000
guardrail.azurecr.io/guardrail-fe:latest  -> public/internal port 80
```

The backend image now bundles the pinned official GitHub MCP executable and
launches it natively over stdio. No Docker socket mount, nested Docker daemon,
or root runtime user is required. Direct local Python runs still default to the
existing Docker-based MCP launcher.

Build from the repository root without Compose:

```powershell
docker build --platform linux/amd64 -t guardrail-be:latest .
docker build --platform linux/amd64 --build-arg NEXT_PUBLIC_API_BASE_URL=/api/gms -t guardrail-fe:latest .\frontend
```

For ACI, place both images in one container group, expose only frontend port
`80`, and set frontend `GMS_API_BASE_URL=http://127.0.0.1:8000`. The frontend
process listens directly on `80`; ACI is not expected to map `80` to `3000`.
The backend remains on internal port `8000`, and browser calls use the
same-origin `/api/gms` route. An Azure ingress service is optional future work
for TLS, a custom domain, WAF behavior, or other production ingress features.

Read `docs/containerisation.md` before building, pushing, or changing ports. It
contains direct `docker run`, ACR tag/push, ACI topology, secrets, and health
check instructions. Actual ACI resource creation remains with the supervisor's
deployment team; this developer handoff contains the verified backend image
and the contract for producing the final matching image pair.

Run the new launch-mode check after pulling this milestone:

```powershell
.\.venv\Scripts\python.exe tests\test_runtime_mcp_launch.py
```

### Latest Local Verification - 2026-08-28

The backend image was rebuilt after expanding deterministic output-rule phrase
parsing. The local container verification proved:

```text
backend /health: ok
backend /health/db: reachable
frontend /api/gms/health proxy: ok
backend GitHub MCP launch mode: native
GITHUB_MCP_READ_ONLY=0 manual mode: write tools offered
explicit output rule "Do not allow the word 'hello'": compiled to "hello"
output guard and HTTP authentication regression tests: passed
```

The corrected backend image currently exists locally as
`guardrail-be:latest`; it has not yet been pushed to ACR. Rebuild and verify
the frontend before pushing one matching frontend/backend release pair.

## Read This First

This file records the exact project state needed to continue safely between
the work and home computers.

Also follow the repository-level rules in `AGENTS.md`, especially the
requirement to preview exact non-doc code diffs and wait for approval.

After pulling on the home computer, use host port `5433` for project Postgres.
Start the database and run the fast regression checks before new work:

```powershell
git pull
docker compose up -d postgres
.\.venv\Scripts\python.exe tests\test_app_auth_http.py
.\.venv\Scripts\python.exe tests\test_policy_assignment_api.py
.\.venv\Scripts\python.exe tests\test_policy_auto_compile.py
.\.venv\Scripts\python.exe tests\test_guardrails_run_http.py
.\.venv\Scripts\python.exe tests\test_output_guard.py
.\.venv\Scripts\python.exe tests\test_runtime_connector_access.py
.\.venv\Scripts\python.exe tests\test_app_connector_api.py
.\.venv\Scripts\python.exe tests\test_runtime_connector_credentials.py
.\.venv\Scripts\python.exe tests\test_app_policy_scope.py
.\.venv\Scripts\python.exe tests\test_tool_guard.py
```

Keep `tests/test_nemo_mcp.py` as the slower opt-in live Azure/GitHub check after
the fast suite is green. Normal scripted runs must use
`GITHUB_MCP_READ_ONLY=1`.

### Home Computer Direct-Docker Resume

The home computer's host tools use Postgres port `5433`. A backend container
must instead reach that host database through `host.docker.internal:5433`.
After substituting the local database username and password, the direct-image
workflow is:

```powershell
docker build --platform linux/amd64 -t guardrail-be:latest .
docker build --platform linux/amd64 --build-arg NEXT_PUBLIC_API_BASE_URL=/api/gms -t guardrail-fe:latest .\frontend

docker rm -f guardrail-be guardrail-fe
docker run -d --name guardrail-be --env-file .env -e DATABASE_URL="postgresql+psycopg://<user>:<password>@host.docker.internal:5433/nemo_mcp_guardrails" -p 8000:8000 guardrail-be:latest
docker run -d --name guardrail-fe -e GMS_API_BASE_URL=http://host.docker.internal:8000 -p 80:80 guardrail-fe:latest

Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/health/db
Invoke-RestMethod http://127.0.0.1/api/gms/health
```

Open `http://127.0.0.1/login`. Swagger is available locally at
`http://127.0.0.1:8000/docs`. If host port `80` is occupied, publish the
frontend with `-p 3000:80` and use `http://127.0.0.1:3000`; the image still
listens on port `80` internally.

Before leaving the home computer, make sure this milestone is committed and
pushed. The work computer cannot see unpushed local files:

```powershell
git status
git add .
git commit -m "Prepare backend and frontend handoff for GMS demo"
git push
```

The frontend and backend are now containerized too. To run the complete local
stack instead of separate Python/npm development servers:

```powershell
docker compose build backend frontend
docker compose up -d
docker compose ps
```

Open `http://127.0.0.1/login`. Backend health is available at
`http://127.0.0.1:8000/health`, and the frontend proxy can be checked at
`http://127.0.0.1/api/gms/health`. Read `docs/containerisation.md` before
changing the Docker or Azure Container Instances layout.

If local host port `80` is occupied, set `FRONTEND_PORT=3000` in `.env` and use
the previous `http://127.0.0.1:3000` local URLs. This override does not change
the deployed image contract: the frontend container still listens on `80`.

Review `git status` before committing and confirm `.env` is not staged.

The work computer may use Postgres host port `5432`. The home computer uses
host port `5433` because Windows PostgreSQL already owns `5432`. Keep each
computer's local `.env` correct and never commit it.

GitHub MCP read/write mode is controlled from `.env`:

```env
GITHUB_MCP_READ_ONLY=1  # safe default for scripted tests
GITHUB_MCP_READ_ONLY=0  # manual local write testing
```

For a direct Python API run, restart `scripts/run_api.py` after flipping this
value. For a containerized API, remove and recreate the backend container;
`docker restart` does not reload values from `--env-file`. Rebuilding the image
is required only when code or dependencies changed, not for an `.env`-only
change. Verify the live container value with:

```powershell
docker exec guardrail-be printenv GITHUB_MCP_READ_ONLY
```

The committed `.env.example` keeps the safe read-only default.

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
-> deterministically check explicit quoted prohibited output phrases
-> NeMo output rail
-> return controlled blocked response when Azure filters output self-check
-> GuardedExecutionResult
```

`runtime_factory.py` loads app-scoped output policy objects and uses
`output_guard.py` to compile explicit quoted prohibitions such as
`Cannot say 'hello'`. `guarded_execution.py` checks those phrases
case-insensitively before NeMo classifies broader semantic rules. A match uses
the normal output safety refusal and debug source
`deterministic_output_phrase`.

`POST /v1/guardrails/run` now exposes `output_rail_source` and
`output_rail_categories` outside debug mode. The app Runtime Test displays
`blocked (Azure: category)` for confirmed Azure completion filtering,
`blocked (Azure)` when no category is available, and `blocked (GMS)` for NeMo
or deterministic GMS enforcement. A normal polite model refusal is not an
Azure filter event and may still pass the output rail.

Azure can also filter the prompt used by NeMo `self_check_input`. Those
`LLMCallException` failures are caught in `execute_guarded_message()` and
returned as `Input: blocked (Azure: category)`, with output marked `not run`,
instead of surfacing to the frontend as `Failed to fetch` from an HTTP `500`.

When Azure filters the main agent completion, the current LangChain Azure
adapter may raise a plain `ValueError` and discard category metadata. The
runtime recognizes its exact provider-filter message and returns
`Output: blocked (Azure)` rather than an HTTP `500`.

Tool-guard policy matches now raise `ToolGuardViolation` before the wrapped MCP
tool executes. Runtime Test displays `Tool guard: blocked (GMS)` and leaves the
output rail as `not run`; connector failures remain the separate `tool_error`
path. `Guarded tool types` is a policy-coverage count, not a count of calls made
by the current request.

The frontend Runtime Test has an app API key field for local/manual testing
convenience. Real apps still call `POST /v1/guardrails/run` from their own
backend with `X-App-ID` and `X-API-Key`.
The app Runtime Test now displays the request path as an
`Input -> Tool guard -> Output` progress bar: green means passed, red means the
blocked/error stage, and grey means the stage did not run.

When `.env` sets `NEMO_RUNTIME_DEBUG=1`, `/v1/guardrails/run` includes a
sanitized `debug_tool_trace` and the app Runtime Test displays it under
Connector debug trace. Use this only for local troubleshooting of GitHub MCP
tool calls/results, such as branch or pull-request validation failures.

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

The normal-developer Apps workflow is now implemented:

```text
/apps
-> real app list, search, pagination, create and delete
-> click row to open /apps/[clientId]

/apps/[clientId]
-> Overview: edit name and rotate API key
-> Connectors: link/enable/disable/unlink GitHub
-> LLM: update main and guardrail config IDs
-> Policies: effective summary and link to filtered policy management
-> Runtime Test: authenticated POST /v1/guardrails/run
```

SharePoint is hidden from active connector selectors because only GitHub has
normalized runtime metadata and an executable adapter. The LLM tab uses numeric
config IDs until a readable LLM-config listing endpoint is added.

App creation no longer accepts user-entered client IDs or API keys. The backend
generates GUID-format client IDs and high-entropy API keys, returns the API key
once, and stores only the hash.

User Management now mirrors the Apps screen: rows show name, email, role, and
enabled status. Create User is a button, and clicking a user opens a modal for
role/status changes, password reset, and app links.

The Settings dark-mode toggle now applies an app-wide Tailwind `dark` class.
Saving writes `gms:theme` to browser `localStorage`; `app/layout.tsx` restores
the class before rendering to reduce theme flashing.

The policy builder loads valid connector/action/resource choices from
`GET /policy-options`; the frontend filters this to GitHub for the current
demo. In the policy table, global assignments use a globe icon, app-specific
GitHub assignments use the GitHub connector mark, and unknown connector values
fall back to the folder icon.

The shared Create/Edit Policy modal now has an Input/Output rail selector.
Policy naming is unlocked immediately. Input mode keeps the cascading GitHub
fields and optional custom resource; output mode hides connector fields and
requires a free-text output rule. Output definitions use category `custom`,
while their app/global assignment display name remains independent.

The stored output rule lives in `policies.conditions.output_rule`; the
`description` column holds the policy name consistently with input policies.
Run `python scripts/migrate_output_policy_rules.py` after pulling this change
to backfill legacy output rows and regenerate active compiled rules. Runtime
loaders fall back to legacy `description` values until migration is run.
Compiled output rules must remain restriction statements; do not add `Answer
no otherwise` to each individual rule because multiple active policies would
produce contradictory classifier instructions. The outer output prompt owns
the single combined yes/no decision.

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

Create is now backend-wired and duplicate-aware. In backend mode it performs:

```text
POST /global-policy-assignments/resolve
or POST /apps/by-client-id/{client_id}/policy-assignments/resolve
-> create a new definition or reuse an equivalent definition
-> return created, reused, or already_assigned
-> reload DB-backed policy assignments
```

The modal closes only after resolution succeeds and shows a visible result
notice. Delete removes only the app/global assignment; it does not delete the
reusable policy definition. Edit is now assignment-safe through:

```text
PUT /apps/by-client-id/{client_id}/policy-assignments/{assignment_id}/resolve
or PUT /global-policy-assignments/{assignment_id}/resolve
-> reuse an existing equivalent policy or create a new definition
-> switch only the selected assignment
-> leave every other app assignment unchanged
```

Assignments now have optional `display_name` values. Run
`python scripts/migrate_policy_assignment_display_names.py` after pulling this
schema change. Legacy duplicate definitions can be previewed with
`python scripts/deduplicate_policies.py` and applied with `--apply`.

Clicking a policy row now opens
`frontend/components/policies/policy-summary-modal.tsx`. The shared modal is
used by both `/policies` and `/apps/[clientId]` Policies, loads
`GET /policies/{policy_id}`, and shows connector/action/resource/custom-resource
metadata plus effect and status. Row Edit/Delete buttons stop propagation.

Direct `POST /policies` and `PUT /policies/{policy_id}` now return `409` when
the requested enforcement behavior is equivalent to another enabled policy.
Equivalence ignores description/name and compares normalized policy structure,
effect, priority, conditions, and enabled state.

FastAPI now enables local frontend CORS through `NEMO_CORS_ORIGINS`. The
committed default allows ports used by the local frontend:

```env
NEMO_CORS_ORIGINS=http://127.0.0.1:3000,http://localhost:3000
```

The modal stores optional custom resource text in
`conditions.custom_resource`. The compiler includes it in the NeMo input rule,
and `tool_guard.py` checks normalized exact MCP argument values before execution.
Blank custom resources continue to apply to the whole action/resource class.
The backend canonicalizes equivalent natural-language variants before policy
reuse checks, so capitalization and phrases such as `Issues named test` do not
create duplicate definitions.

`GET /policy-options` supplies the frontend policy builder from enabled
connector tool mappings. Its dropdown sequence is connector -> action -> valid
resource; SharePoint remains absent until it has executable mappings.

## Important Current Files

- `src/nemo_mcp_guardrails/app_auth.py`: API-key hashing and app verification.
- `src/nemo_mcp_guardrails/api/auth.py`: `require_authenticated_app`.
- `src/nemo_mcp_guardrails/api/runtime.py`: protected auth-check and run endpoints.
- `src/nemo_mcp_guardrails/api/runtime_schemas.py`: runtime request/execution response models.
- `src/nemo_mcp_guardrails/database/conversation_store.py`: conversation history load/append helpers.
- `src/nemo_mcp_guardrails/database/models.py`: includes `conversation_messages`.
- `src/nemo_mcp_guardrails/runtime_factory.py`: Azure, NeMo, MCP, and agent construction. It uses the authenticated app's `guardrail_llm_config_id` for NeMo rails and `main_llm_config_id` for the LangChain agent, with `.env` Azure fallback when either ID is missing.
- `src/nemo_mcp_guardrails/guarded_execution.py`: reusable single-request guardrail workflow.
- `src/nemo_mcp_guardrails/output_guard.py`: deterministic app-scoped quoted
  output phrase extraction and matching.
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
- `tests/test_output_guard.py`: isolated explicit output phrase parser and
  matcher regression test.

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
Linux AMD64 frontend port-80 image build: passed
non-root uid=1001 Next.js port-80 /login probe: passed
Linux AMD64 backend image rebuild after output-guard fix: passed
backend container API/database/frontend-proxy health: passed
container-native GitHub MCP readOnly=false manual probe: passed
explicit output phrase parser regression test: passed
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

Immediate top priority: finish verifying and hand off the corrected ACI image
pair. The corrected backend image is local and verified but not yet pushed.
The frontend management MVP, management JWT/RBAC, named LLM selectors, connector
management, policy management, and Runtime Test are already implemented.

```text
guardrail.azurecr.io/guardrail-fe:<matching-tag> -> public port 80
guardrail.azurecr.io/guardrail-be:<matching-tag> -> private port 8000
```

Build both Linux AMD64 images from the repository root:

```powershell
docker build --platform linux/amd64 -t guardrail-be:latest .
docker build --platform linux/amd64 --build-arg NEXT_PUBLIC_API_BASE_URL=/api/gms -t guardrail-fe:latest .\frontend
```

Verify the containerized local stack:

```powershell
docker compose up -d
Invoke-RestMethod http://127.0.0.1/api/gms/health
Invoke-WebRequest -UseBasicParsing http://127.0.0.1/login
```

Then push one matching image pair and give the deployment owner this ACI
contract:

```text
one Linux multi-container ACI group
public group port: 80 only
frontend process: 0.0.0.0:80
backend process: 0.0.0.0:8000, not publicly exposed
frontend GMS_API_BASE_URL: http://127.0.0.1:8000
external persistent PostgreSQL
runtime-injected secrets
```

Actual ACI resource creation remains with the supervisor's deployment team.
After deployment, validate login, policy CRUD, proxy health, and one guarded
GitHub request without a port suffix in the browser URL. Keep
`GITHUB_MCP_READ_ONLY=1` for scripted tests.

## Boundaries Not Yet Implemented

- Connector credentials and LLM credentials are not managed through a secrets
  manager yet.
- Argument-level and workflow-state policies are not implemented.
- TLS/custom-domain ingress, audit screens, and CI/CD publishing are not
  implemented yet.

## Editing Rules

- Preview exact non-doc code diffs and wait for user approval.
- Docs-only updates can be applied directly.
- Add short docstrings to new Python functions/classes.
- Update relevant docs after every completed change.
- Never commit `.env`, real API keys, PATs, or plaintext connector credentials.
