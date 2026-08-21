# Open Work Backlog

This file tracks unfinished implementation work so active plans do not get lost
across machines or Codex sessions.

## Current Status

The GMS backend prototype now has these core runtime pieces:

- App authentication for runtime endpoints with `X-App-ID` and `X-API-Key`.
- Management login and `/management-auth/me` now use scrypt password hashes and
  signed JWT bearer tokens. Public signup is disabled; system admins create
  users from `/management-users` and issue one-time temporary passwords.
- Existing users receive `name` and unique `username` values backfilled from
  email. Settings loads the authenticated profile, saves those fields through
  `PUT /management-auth/me`, and Logout returns to the real Login page.
- App-scoped global plus app-specific policy assignment loading.
- DB-backed compiled prompt rules injected into NeMo prompt templates.
- App-scoped blocked GitHub MCP tool names.
- Authenticated `POST /v1/guardrails/run`.
- Postgres-backed conversation history with request-size trimming.
- Separate app-selected LLM configs for guardrail rails and the main agent.
- `GET /llm-configs` exposes readable configuration metadata without credential
  references, and the app LLM tab uses named selectors instead of numeric IDs.
- `POST /llm-configs` creates Azure-compatible configuration metadata with an
  optional `env:VARIABLE_NAME` credential reference. The runtime resolves that
  reference per selected main/guardrail model and otherwise uses the shared
  `AZURE_OPENAI_API_KEY` fallback.
- Controlled runtime responses for connector tool errors and Azure output
  content-filter failures.
- App-scoped deterministic checks for explicit quoted output prohibitions such
  as `Cannot say 'hello'`; broad rules such as `No profanities` remain NeMo
  semantic classifications.
- Runtime responses expose `output_rail_source` and Azure-reported filtered
  categories. The frontend distinguishes `blocked (Azure: category)` from
  `blocked (GMS)`; generic Azure events fall back to `blocked (Azure)`.
- Azure filtering during NeMo input self-checks is converted from an unhandled
  `500` into a controlled runtime block. Responses expose `input_rail_source`
  and `input_rail_categories`, and Runtime Test renders labels such as
  `Input: blocked (Azure: hate)` while leaving output as `not run`.
- LangChain can convert an Azure-filtered agent completion into a category-less
  `ValueError`. The runtime recognizes that exact provider message and returns
  `Output: blocked (Azure)` instead of HTTP `500`.
- MCP policy matches now raise `ToolGuardViolation` before the connector call.
  `/run` reports `tool_guard_status` and `tool_guard_source`, skips output rails
  after a guard violation, and Runtime Test shows `Tool guard: blocked (GMS)`.
  The coverage count is labelled `Guarded tool types` rather than implying the
  current request invoked every covered tool.
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
  implements the uploaded Figma screens and current management pages:
  `/login`, `/signup` admin-managed notice, `/apps`, `/apps/[clientId]`,
  `/policies`, `/user-management`, and `/settings`.
- Production-style frontend and backend Docker images now build successfully.
  Local Compose runs them with Postgres and pgAdmin, and the frontend
  same-origin `/api/gms` proxy reaches FastAPI over the private Compose network.
  The backend image bundles the native GitHub MCP executable, so neither local
  Compose nor the Azure Container Instances target needs a Docker socket.
- The normal-developer Apps workflow is implemented: `/apps` lists and opens
  assigned client applications; `/apps/[clientId]` provides Overview,
  Connectors, LLM, Policies, and Runtime Test tabs backed by FastAPI. App
  creation is system-admin-only.
- The admin-only User Management workflow is implemented: `/user-management`
  lists users, creates accounts with one-time temporary passwords, resets
  passwords, blocks/enables users, changes system role, and links users to apps
  as app developers.
- App API keys are now backend-generated. Create and regenerate responses show
  the plaintext key once, GMS stores only the hash, and regeneration invalidates
  the previous key.
- Settings now provides a class-based app-wide dark theme. It previews
  immediately, saves the selected theme in browser `localStorage`, and restores
  it before rendering on later visits.
- The `/policies` page now has a typed read/write API adapter. When
  `frontend/.env.local` sets
  `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000`, it loads real apps, global
  policy assignments, and app effective policy assignments from FastAPI. When
  the env var is absent, it stays in mock mode for static/Vercel design demos.
- The create-policy modal now writes through FastAPI when backend mode is
  enabled: it creates the reusable policy, assigns it globally or to the
  selected app, reloads DB-backed assignments, and closes only after success.
- The same Create/Edit modal now supports input and output policies. Policy
  naming is available immediately; input mode uses the cascading structured
  fields, while output mode replaces them with a required free-text output
  rule. Custom output categories compile through a general NeMo output
  classifier while the credential category keeps its specialized wording.
- Policy storage now keeps names in `policies.description` and output behavior
  in `conditions.output_rule`. Loaders retain a legacy-description fallback.
  `scripts/migrate_output_policy_rules.py` backfills existing output rows and
  refreshes their compiled rules. Runtime Test displays input and output policy
  counters separately.
- Output rules now compile as restriction statements rather than independent
  yes/no instructions. `self_check_output` performs one OR-style decision: a
  violation of any active output policy blocks the response.
- `output_guard.py` extracts quoted phrases from explicit `cannot`, `must not`,
  `do not`, and `never` rules. Matching is case-insensitive and reports debug
  source `deterministic_output_phrase`.
- Policy creation now resolves structural equivalence before inserting. The
  backend returns `created`, `reused`, or `already_assigned`; equivalent names
  do not create duplicate policy definitions, and app requests do not add a
  redundant assignment when the same policy is already active globally.
- Frontend Delete now removes only the selected app/global assignment. The
  reusable policy definition remains available for other apps.
- Direct reusable policy-definition deletion is admin-only and now refuses to
  delete policies that are still assigned globally or to any app. Assigned
  deletes return `409` with assignment references.
- Frontend Edit is assignment-safe. It resolves the edited behavior, switches
  only that app/global assignment to an existing or newly created reusable
  policy, and leaves other apps on their previous policy.
- Policy rows on the main Policies page and app-detail Policies tab now open a
  shared backend-backed summary modal without interfering with Edit/Delete.
- Optional `conditions.custom_resource` values now flow into compiled input
  rules and immutable MCP guard rules. Runtime recursively checks normalized
  exact tool-argument values, so a targeted issue title, branch, path, or
  identifier can be blocked without denying every call to that tool.
- Custom-resource phrases are canonicalized for reuse across case,
  singular/plural resource wording, and `name`/`named`/`called`/`titled`
  variants. Legacy consolidation applies the same canonical identity.
- `GET /policy-options` exposes enabled normalized tool mappings. The policy
  form cascades connector -> action -> valid resources and omits connectors
  without mappings, including the current SharePoint placeholder.
- Policy mutation warnings render above open dialogs, policy naming/global
  controls appear first, and the Apps list omits redundant client-ID and
  authorization columns.
- App/global assignments now store optional `display_name` values, so each app
  can name a shared policy independently. The frontend prefers this name.
- `scripts/deduplicate_policies.py` consolidates legacy equivalent policy rows;
  `scripts/migrate_policy_assignment_display_names.py` adds/backfills the
  assignment display-name columns.
- FastAPI allows configured frontend origins through `NEMO_CORS_ORIGINS`; the
  committed local default covers `http://127.0.0.1:3000` and
  `http://localhost:3000`.
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
- The frontend currently exposes only GitHub and SharePoint in its connector
  selector. GitHub is executable; SharePoint remains a UI/metadata placeholder
  until backend mappings and runtime support are implemented.
- Policy-table icons distinguish scope and connector: global assignments use a
  globe, app-specific GitHub/SharePoint assignments use connector marks, and
  unknown legacy connectors use a folder fallback.
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
- The app LLM tab can create Azure configuration metadata and select it by
  readable name; raw keys never pass through the browser or API.
- Selected LLM configurations can resolve distinct `env:VARIABLE_NAME` API
  keys at runtime.
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

- Completed. Management CRUD requires JWT authentication.
- App reads/writes are filtered through active app-developer `app_users` links;
  legacy `owner` links are still accepted for compatibility, viewer links no
  longer grant app access, and system admins bypass app membership.
- App creation is system-admin-only and new apps atomically link the admin
  creator as an app developer.
- Global assignments, direct policy mutation/compilation, and allowed-test
  mutation are restricted to system admins.
- The frontend automatically sends its saved JWT and hides or disables
  admin-only global-policy and guardrail-LLM controls for developers.

Follow-up:

- Add richer admin audit/logging screens after supervisor confirmation.

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

Current implementation:

- `docs/frontend-api-map.md` maps backend endpoints to frontend screens.
- `docs/frontend-screen-plan.md` proposes the first app structure and
  component breakdown.
- `docs/frontend-demo-flow.md` defines the GitHub MCP presentation flow.
- `docs/figma-design-intake.md` records the uploaded Figma screens and
  interaction notes.
- `frontend/` contains the Figma-matched implementation, a read/write
  API-backed `/policies` adapter, and functional app list/detail routes.
- `/user-management` provides admin-only user creation, password reset,
  enable/block, role changes, and app-developer links.
- The app LLM tab uses a readable LLM-config catalogue and named selectors.

Next implementation slice:

- Add optional admin force-delete behavior only if supervisors want policy
  definition deletion to also remove assignment references.
- Add LLM configuration update/delete and ownership controls after the
  organization confirms its provider-administration workflow.
- Keep richer audit/logging screens as post-presentation work pending
  supervisor confirmation.

### 11. Audit, Analytics, And Caching

Future enhancements:

- Conversation/action audit views.
- Runtime event logging.
- Redis cache for compiled app policy bundles.
- Background workers for compilation and invalidation.

### 12. Registry And CI/CD

Current local milestone:

- Backend and frontend images build successfully.
- Compose health checks pass for frontend, backend and Postgres.
- Backend database health and frontend-to-backend proxy health are verified.
- Backend image bundles the pinned native GitHub MCP executable and does not
  require a Docker socket or root runtime user.
- Direct source runs retain the Docker-based GitHub MCP launcher by default.
- Backend and frontend image contracts use private backend port `8000` and
  public frontend port `80`. The non-root Node process receives only
  `NET_BIND_SERVICE` so it can bind the HTTP port.
- The Linux AMD64 frontend port-80 image build and non-root `/login` runtime
  probe passed on 2026-08-21.
- The target hosting service is Azure Container Instances, not OpenShift.

Next deployment work:

- Build and locally test `guardrail-be` and `guardrail-fe` directly.
- Push a matching image pair to `guardrail.azurecr.io`.
- Let the deployment team create a two-container ACI group with frontend
  public port `80`, private backend port `8000`, frontend
  `GMS_API_BASE_URL=http://127.0.0.1:8000`, and external PostgreSQL.
- Validate the deployed proxy, management login, policy CRUD, and guarded
  GitHub runtime.
- Add GitHub Actions pull-request CI for tests and Docker builds.
- Add main-branch image publishing with GitHub OIDC and Azure `AcrPush`.
- Publish immutable Git commit SHA tags alongside any `latest` tag.

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
