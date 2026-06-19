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

### 2. Add Real Allowed/Blocked HTTP Runtime Integration Coverage

Current `scripts/test_app_auth_http.py` verifies authentication, runtime
reachability, conversation history, truncation, and controlled error branches
with fake runtime pieces.

Next slice:

- Create a temporary authorized app.
- Assign one GitHub input policy to it.
- Call `POST /v1/guardrails/run` with an allowed read prompt.
- Call `POST /v1/guardrails/run` with a blocked write prompt.
- Assert status, rail statuses, called tools, history metadata, and cleanup.
- Keep `GITHUB_MCP_READ_ONLY=1` for scripted tests.

## Near-Term Backend Work

### 3. Automate Policy Compilation And Invalidation

Current state:

- `POST /policies/compile-rules` can write `compiled_policy_rules`.
- Compiled rules can become stale when a policy or assignment changes.

Needed:

- Automatically mark compiled rules stale when policy definitions change.
- Compile or refresh rules after create/update/delete operations.
- Decide whether this happens synchronously in the API or later through a
  worker/background queue.

### 4. Finish Runtime LLM Provider Support

Current state:

- `main_llm_config_id` and `guardrail_llm_config_id` are respected.
- Azure OpenAI-compatible provider rows are executable.
- Non-Azure providers such as Gemini return a clear unsupported-provider error.

Needed:

- Add provider adapter functions for future providers.
- Resolve `credential_reference` through a secrets manager instead of `.env`.
- Keep guardrail-classification LLM and main-agent LLM independently
  configurable.

### 5. Enforce Connector Access And Credentials

Current state:

- `app_connectors` stores which connectors an app can use.
- Runtime still constructs GitHub MCP tools from `.env` settings.

Needed:

- Load connector access for the authenticated app at runtime.
- Refuse connector/tool execution when the app is not linked to that connector.
- Resolve connector credentials through `credential_reference`.

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

### 11. Audit, Analytics, And Caching

Future enhancements:

- Conversation/action audit views.
- Runtime event logging.
- Redis cache for compiled app policy bundles.
- Background workers for compilation and invalidation.

## Current Useful Verification Commands

```powershell
.\.venv\Scripts\python.exe scripts\test_runtime_llm_selection.py
.\.venv\Scripts\python.exe scripts\test_app_auth_http.py
.\.venv\Scripts\python.exe scripts\test_app_auth.py
.\.venv\Scripts\python.exe scripts\test_policy_assignment_api.py
.\.venv\Scripts\python.exe scripts\test_app_policy_scope.py
.\.venv\Scripts\python.exe scripts\test_tool_guard.py
.\.venv\Scripts\python.exe scripts\debug_nemo_output_check.py
.\.venv\Scripts\python.exe scripts\test_nemo_mcp.py
```
