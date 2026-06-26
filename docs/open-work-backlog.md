# Open Work Backlog

This file tracks unfinished implementation work so active plans do not get lost
across machines or Codex sessions.

## Current Status

The GMS backend prototype now has these core runtime pieces:

- App authentication for runtime endpoints with `X-App-ID` and `X-API-Key`.
- App-scoped global plus app-specific policy assignment loading.
- DB-backed compiled prompt rules injected into NeMo prompt templates.
- App-scoped blocked GitHub MCP tool names.
- Authenticated `POST /v1/guardrails/run`.
- Postgres-backed conversation history with request-size trimming.
- Separate app-selected LLM configs for guardrail rails and the main agent.
- Controlled runtime responses for connector tool errors and Azure output
  content-filter failures.
- Centralized single/bulk policy assignment payloads for app and global
  assignments, with readable app and policy labels in API responses.
- Developer-friendly client-ID aliases for app lookup and app-specific policy
  assignment management.
- App connector management APIs now list, create/update, update, and delete
  app connector links by app ID or client ID.
- GitHub connector credentials can now be resolved from
  `app_connectors.credential_reference` when it uses `env:VAR_NAME`.
- Frontend planning docs now exist for the Next.js 13 build:
  `frontend-api-map.md`, `frontend-screen-plan.md`, and
  `frontend-demo-flow.md`.
- The first Next.js 13 frontend scaffold now exists under `frontend/`. It
  currently implements the uploaded Figma screens with mock data:
  `/login`, `/signup`, `/policies`, and `/settings`.
- Policy create/update now automatically refreshes `compiled_policy_rules`;
  old compiled rows are marked stale and disabled.
- HTTP runtime integration coverage now proves an authenticated app can pass an
  allowed read request and block an assigned GitHub write policy through
  `POST /v1/guardrails/run` without Docker or Azure.
- Runtime construction now checks `app_connectors` before GitHub MCP tools are
  built and rejects apps that are not linked to the enabled GitHub connector.

Current presentation/demo scope:

- GitHub MCP is the only connector that needs to be demonstrably supported for
  the upcoming presentation.
- SharePoint, Outlook, and other connectors remain target-architecture
  extensions and should not block the near-term backend/frontend milestone.

## Immediate Priority

### 1. Move Hardcoded Self-Check Behavior Out Of `config/prompts.yml`

Problem:

- `config/prompts.yml` still contains GitHub-specific and credential-specific
  examples.
- Active policy behavior should come from Postgres policy rows and
  `compiled_policy_rules`.
- The output rail can false-positive when the classifier reacts to restricted
  words in the policy text instead of only inspecting `{{ bot_response }}`.

Status:

- Implemented in `config/prompts.yml`: the templates are now generic and
  instruct NeMo to evaluate only the user message or assistant response against
  injected active DB rules.
- Implemented in `policy_compiler.py`: the default credential output rule now
  avoids listing specific sensitive categories in the compiled self-check
  prompt and instead checks for actual sensitive credential or secret
  configuration values.
- Local DB updated: existing credentials output policy and its
  `compiled_policy_rules` row were refreshed to the safer wording.

Follow-up verification:

- Confirm the harmless hello response passes output rails for an app with only
  the global credential output policy.
- Keep DB rules as the source of actual policy behavior.
- If the runtime still blocks unexpectedly, set `NEMO_RUNTIME_DEBUG=true` before
  starting `scripts/run_api.py`. The `/v1/guardrails/run` response will include
  debug-only fields for the raw agent response, output-rail source, and active
  output rule texts.
- If Azure content-filters the output self-check prompt, runtime now falls back
  to a deterministic local secret-pattern scan. Obvious secret-like output still
  blocks; harmless output passes with
  `debug_output_rail_source=azure_content_filter_fallback_passed`.

Future extension:

- Store prompt templates or prompt-template versions in Postgres if admins need
  configurable classifier wrappers later.

### 2. Keep Real Allowed/Blocked HTTP Runtime Integration Coverage Green

Current state:

- `tests/test_app_auth_http.py` verifies authentication, runtime
  reachability, conversation history, truncation, and controlled error branches
  with fake runtime pieces.
- `tests/test_guardrails_run_http.py` creates a temporary authorized app,
  creates and assigns a GitHub issue-creation block policy, then calls
  `POST /v1/guardrails/run` with allowed and blocked prompts.
- The test uses real DB policy assignment, prompt-rule loading, and blocked-tool
  loading, but fake rails/agent so Docker, GitHub MCP, Azure, and write tools
  are not touched.

Needed:

- Keep `GITHUB_MCP_READ_ONLY=1` for scripted tests.
- Add real-Docker/Azure coverage only as an explicit opt-in harness later.

## Near-Term Backend Work

### 3. Broaden Automatic Compilation Coverage

Current state:

- `POST /policies` creates the compiled rule inside the same transaction.
- `PUT /policies/{policy_id}` stales/disables old compiled rows and creates a
  fresh active rule when the policy remains enabled.
- Disabling a policy leaves no active non-stale compiled rule.
- Invalid compiler input returns `400` without partially persisting the policy.
- `POST /policies/compile-rules` remains available as a manual full resync.

Needed:

- Decide whether assignment changes should trigger cached app-policy bundle
  invalidation once Redis or another cache is introduced.
- Keep `tests/test_policy_auto_compile.py` in the verification set whenever
  policy CRUD changes.

### 4. Finish Runtime LLM Provider Support

Current state:

- `main_llm_config_id` and `guardrail_llm_config_id` are respected.
- Azure OpenAI-compatible provider rows are executable.
- Non-Azure providers such as Gemini return a clear unsupported-provider error.

Needed:

- Add provider adapter functions for future providers.
- Resolve `credential_reference` through a secrets manager instead of `.env`
  for production deployments.
- Keep guardrail-classification LLM and main-agent LLM independently
  configurable.

### 5. Add Connector Management APIs And Credential Resolution

Current state:

- `app_connectors` stores which connectors an app can use.
- Runtime checks enabled GitHub connector access before constructing GitHub MCP
  tools.
- App connector links can be managed through `/apps/{app_id}/connectors` and
  `/apps/by-client-id/{client_id}/connectors`.
- `tests/test_app_connector_api.py` verifies app connector CRUD, connector
  lookup by name or ID, upsert behavior, and missing-link errors.
- Runtime resolves GitHub MCP credentials from `credential_reference` when it
  uses `env:VAR_NAME`, and falls back to `GITHUB_PERSONAL_ACCESS_TOKEN` when
  no connector-specific reference is set.
- `tests/test_runtime_connector_credentials.py` verifies default PAT fallback,
  app-specific `env:VAR_NAME` references, missing env vars, and unsupported
  reference schemes.

Needed:

- Add a real secrets-manager resolver for references such as `vault:...`.

### 6. Protect Management/Admin APIs

Current state:

- Runtime endpoints are authenticated.
- Management CRUD endpoints under `/apps`, `/policies`, assignments, and
  allowed tests are not authenticated yet.

Needed:

- Add user login/session or token authentication.
- Add role checks for developer app owners versus admins.
- Restrict global policy management to admins.

## Later Backend Work

### 7. Remove Legacy Policy String Columns

Current state:

- Normalized connector/action/resource IDs exist.
- Legacy flat policy columns remain as compatibility fallback.

Needed:

- Ensure every create/update/load path uses normalized IDs.
- Remove `policies.connector`, `policies.action`, and `policies.resource` only
  after stable verification.

### 8. Add Argument-Level And Workflow-State Policies

Needed for policies such as:

```text
allow merge A -> B -> C only
block merge B -> A -> C
```

Tool-name denylisting is not enough. These policies need:

- Tool argument checks.
- Workflow state storage.
- Ordered transition validation.

### 9. Add Optional Write-Capable MCP Test Harness

Normal tests must remain read-only.

Future write tests should be:

- Explicitly opt-in.
- Pointed at a throwaway repository.
- Run with a limited token.
- Kept separate from the standard test suite.

### 10. Frontend Management App

Target frontend:

- Next.js 13.
- Developer login.
- App list and app detail screens.
- Policy assignment management.
- Global policy management for admins.
- Later: visual policy builder.

Current prep:

- `docs/frontend-api-map.md` maps backend endpoints to frontend screens.
- `docs/frontend-screen-plan.md` proposes the first app structure and
  component breakdown.
- `docs/frontend-demo-flow.md` defines the GitHub MCP presentation flow.
- `docs/figma-design-intake.md` records the uploaded Figma screens and
  interaction notes.
- `frontend/` contains the first static/mock implementation of the Figma
  pages.

Next implementation slice:

- Wire `/policies` to the FastAPI policy/app assignment endpoints.
- Replace mock app/policy data with typed API calls from
  `docs/frontend-api-map.md`.
- Add loading/error/empty states before expanding to runtime tester screens.

### 11. Audit, Analytics, And Caching

Future enhancements:

- Conversation/action audit views.
- Runtime event logging.
- Redis cache for compiled app policy bundles.
- Background workers for compilation and invalidation.

## Current Useful Verification Commands

```powershell
.\.venv\Scripts\python.exe tests\\test_runtime_llm_selection.py
.\.venv\Scripts\python.exe tests\\test_app_auth_http.py
.\.venv\Scripts\python.exe tests\\test_app_auth.py
.\.venv\Scripts\python.exe tests\\test_policy_assignment_api.py
.\.venv\Scripts\python.exe tests\\test_policy_auto_compile.py
.\.venv\Scripts\python.exe tests\\test_guardrails_run_http.py
.\.venv\Scripts\python.exe tests\\test_runtime_connector_access.py
.\.venv\Scripts\python.exe tests\\test_app_connector_api.py
.\.venv\Scripts\python.exe tests\\test_app_policy_scope.py
.\.venv\Scripts\python.exe tests\\test_tool_guard.py
.\.venv\Scripts\python.exe scripts\debug_nemo_output_check.py
.\.venv\Scripts\python.exe tests\\test_nemo_mcp.py
```
