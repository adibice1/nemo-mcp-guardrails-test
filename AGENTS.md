# AGENTS.md

## Project Context

This project tests NVIDIA NeMo Guardrails with GitHub MCP and an LLM.

The goal is to build toward a guardrails management system where administrators can configure app-specific policies, such as blocking GitHub write operations, without manually editing backend guardrail code.

Confirmed target terminology:

- `app` means a client application authorized to consume the Guardrails Management System.
- `connector` means an external integration such as GitHub MCP, SharePoint, or Outlook.
- The connector terminology migration is complete: `apps` are GMS client applications, while `connectors`, `connector_actions`, `connector_resources`, and `connector_tool_mappings` model external integrations.
- Read `docs/target-architecture.md` before proposing the next schema migration.
- Read `docs/work-computer-handoff.md` first when continuing this exact
  2026-06-16 home-computer milestone on another machine.
- The target GMS is a full proxy that owns input rails, agent/tool execution, and output rails.
- One app may use multiple connectors; users and apps are many-to-many.
- Global policies are mandatory across every app.
- Main-agent and guardrail-classification LLM configurations may differ.
- Policy rules should compile automatically when rules or assignments change.
- Input-policy `conditions.custom_resource` values are canonicalized before
  storage/equivalence checks. Case, singular/plural resource prefixes and
  wording such as `name`, `named`, `called` and `titled` do not create separate
  reusable enforcement definitions.

## Current Architecture

The test pipeline is:

User prompt
-> deterministic Python pre-check report only
-> DB compiled prompt rules are injected into `config/prompts.yml` templates
-> NeMo Guardrails input rail using the app's guardrail AzureChatOpenAI config
-> LangChain agent
-> `src/nemo_mcp_guardrails/tool_guard.py` wraps GitHub MCP tools and blocks DB-derived restricted tool names before execution
-> GitHub MCP tools, normally in read-only Docker mode unless local `.env` explicitly sets `GITHUB_MCP_READ_ONLY=0`
-> NeMo Guardrails output rail using the app's guardrail AzureChatOpenAI config
-> final model answer

The deterministic Python pre-check is no longer the main enforcement path. It currently reports what it would block for comparison, unless `ENFORCE_PYTHON_PRECHECK=true` is set.

The project now also includes a policy-object compiler prototype in `src/nemo_mcp_guardrails/policy_compiler.py`. It models admin-created input policies such as `github + create + issue + block`, generates NeMo self-check rule text as a preview, generates blocked MCP tool names for `src/nemo_mcp_guardrails/tool_guard.py`, generates curated blocked prompt tests consumed by `tests/test_nemo_mcp.py`, and previews output-policy rule text.

## Current Safety Policy

Allowed GitHub MCP actions:
- Search repositories
- Read repository files
- List branches
- List issues
- Read pull requests
- Read commits/tags/releases

Blocked actions:
- Create or update issues
- Comment on issues
- Create, update, merge, or review pull requests
- Push commits
- Create/delete branches
- Create/update/delete files
- Reveal tokens, API keys, secrets, `.env`, or environment variables

## Important Implementation Notes

- `.env` stores real secrets and must never be committed.
- `.env.example` stores placeholder values and should be committed.
- `config/config.yml` should be committed but must not contain real API keys.
- Azure OpenAI credentials are loaded from `.env`.
- GitHub MCP runs in Docker with `GITHUB_READ_ONLY` derived from `.env` `GITHUB_MCP_READ_ONLY`; the committed default is `1` for read-only mode.
- Current input blocking is handled by NeMo `self check input` using `config/prompts.yml` plus enabled DB rules from `compiled_policy_rules`.
- Current output checking is handled by NeMo `self check output` using `config/prompts.yml` plus enabled DB rules from `compiled_policy_rules`.
- `config/config.yml` enables both `self check input` and `self check output`.
- Output self-check prompts intentionally inspect only `{{ bot_response }}` and do not echo `{{ user_input }}`, because unsafe user prompts containing fake token-like text can trigger Azure content filtering before NeMo can classify the assistant output.
- `tests/test_nemo_mcp.py` manually creates `LLMRails(rails_config, llm=model)` so NeMo uses the same working AzureChatOpenAI model as the LangChain agent.
- Do not switch back to stock `GuardrailsMiddleware(config_path="config")` without testing, because it constructs its own NeMo LLM and previously hit an old OpenAI client path.
- `src/nemo_mcp_guardrails/tool_guard.py` contains the execution-level MCP tool guard. `tool_guard_rules_for_app(app_id=...)` compiles immutable per-app broad or `conditions.custom_resource`-specific rules from enabled global plus app-assigned input policies. `blocked_tool_names_for_app(app_id=...)` remains the reporting summary, while `guard_mcp_tool(..., guard_rules=...)` checks normalized exact MCP argument values before execution.
- `src/nemo_mcp_guardrails/policy_compiler.py` contains the structured policy-object prototype. It uses `InputPolicyObject` for input/tool policies and `OutputPolicyObject` for output policies. It currently covers GitHub issue, pull request, branch, file, repository, and fork write actions plus credential/secret output checks.
- GitHub compiler metadata is split into `GITHUB_WRITE_TOOL_MAPPINGS`, `GITHUB_READ_TOOL_MAPPINGS`, and `GITHUB_METADATA_TOOL_MAPPINGS`. Runtime blocking uses write mappings only; normalized metadata seeding uses the combined metadata mapping.
- To add a runtime input policy in the current prototype, add an enabled policy row through the FastAPI CRUD endpoints or DBeaver. Edit `src/nemo_mcp_guardrails/policy_compiler.py` only when adding a new action/resource mapping, synonym, or template that the compiler does not yet understand.
- `config/prompts.yml` is now a stable prompt template. `src/nemo_mcp_guardrails/database/prompt_rule_loader.py` loads enabled rows from `compiled_policy_rules`, and `src/nemo_mcp_guardrails/prompt_rule_compiler.py` injects those rules into the template before `LLMRails` is created.
- `tests/test_nemo_mcp.py` imports curated generated tests with `compile_policy_test_prompts(load_input_policy_objects())`, so generated blocked tests follow enabled DB input policies.
- `scripts/debug_nemo_self_check.py` is an isolated diagnostic script for NeMo input rails without GitHub MCP. It uses `build_rails_config_with_prompt_rules("config")` so it tests the same DB-injected prompt configuration as the full runner.
- `tests/test_tool_guard.py` is an isolated diagnostic script for the MCP tool guard without Docker, Postgres, GitHub MCP, Azure OpenAI, or real credentials. It forces `NEMO_POLICY_SOURCE=defaults`, proves the same tool can be blocked for App A and allowed for App B using different scoped sets, and proves a custom issue-title restriction blocks only the matching MCP call.
- `tests/test_policy_loader.py` is an isolated diagnostic script for Postgres policy loading and compilation without Azure OpenAI or GitHub MCP.
- `tests/test_app_policy_scope.py` is a self-cleaning Postgres integration diagnostic. It creates two temporary apps, assigns GitHub issue creation only to App A, verifies app-scoped NeMo rules and blocked tools, and deletes both apps and their assignments in `finally`.
- `scripts/debug_nemo_output_check.py` is an isolated diagnostic script for NeMo output rails without GitHub MCP. It uses `build_rails_config_with_prompt_rules("config")` so it tests the same DB-injected prompt configuration as the full runner.
- NeMo output rails are now enabled through `config/config.yml` and verified in the full GitHub MCP test runner.
- The database/API phase uses PostgreSQL. Local development starts from `docker-compose.yml`, which runs Postgres and pgAdmin. DBeaver can also connect to the same local Postgres database. The target deployment direction is containerisation and OpenShift.
- The home computer runs the project Docker Postgres service on host port `5433` because a Windows PostgreSQL service already uses host port `5432`. Home-computer `.env`, `DATABASE_URL`, and DBeaver settings must use `5433`; Postgres still listens on port `5432` inside the container.
- FastAPI policy CRUD endpoints live under `/policies`.
- `POST /policies/compile-preview` reads enabled DB policy rows, converts them into `InputPolicyObject` / `OutputPolicyObject`, and returns generated input rules, blocked tools, generated test prompts, and output rules.
- `POST /policies` and `PUT /policies/{policy_id}` automatically refresh `compiled_policy_rules`; old compiled rows are marked stale and disabled, and a fresh active row is created when the policy remains enabled.
- `POST /policies/compile-rules` remains available as a manual full resync/debug endpoint.
- FastAPI allowed-test CRUD endpoints live under `/allowed-test-cases`. These rows are safe prompts that `tests/test_nemo_mcp.py` should expect to pass; they are not allow/block policies.
- `src/nemo_mcp_guardrails/database/policy_loader.py` provides app-aware `load_input_policy_objects(app_id=...)` and `load_output_policy_objects(app_id=...)`. With an app ID, loaders return enabled global assignments plus enabled assignments for that app. Without an app ID, they preserve the current all-enabled testing behavior.
- `src/nemo_mcp_guardrails/database/prompt_rule_loader.py` and `build_rails_config_with_prompt_rules(..., app_id=...)` apply the same optional assignment scope to compiled NeMo rules.
- `src/nemo_mcp_guardrails/database/test_case_loader.py` loads enabled DB allowed test cases for `tests/test_nemo_mcp.py`, falling back to the three default read tests if no enabled DB rows exist.
- `scripts/seed_normalized_policy_metadata.py` seeds normalized connector metadata and backfills `allowed_test_case_expected_tools`. Expected counts after seeding are: connectors 2, connector_actions 11, connector_resources 10, connector_tool_mappings 33, allowed_test_case_expected_tools 3.
- Normalized connector metadata tables exist now: `connectors`, `connector_actions`, `connector_resources`, `connector_tool_mappings`, and `allowed_test_case_expected_tools`. Runtime policy loading prefers normalized relationships with flat `policies.connector/action/resource` fallback fields.
- `app_users` and `app_connectors` now model user/app management roles and app-specific connector access. GitHub connector credentials can be resolved from `credential_reference` when it uses `env:VAR_NAME`; blank references fall back to `GITHUB_PERSONAL_ACCESS_TOKEN`.
- Runtime construction checks `app_connectors` before building GitHub MCP tools; unlinked or disabled-link apps are rejected before Docker/Azure/MCP startup.
- `app_policy_assignments` and `global_policy_assignments` reference the existing reusable definitions in `policies`. The connector-independent credential output policy is globally assigned; GitHub write policies remain unassigned.
- FastAPI client-app CRUD lives under `/apps`; nested app-policy-assignment CRUD lives under `/apps/{app_id}/policy-assignments`; global assignment CRUD lives under `/global-policy-assignments`.
- App/global assignment POST bodies use `policy_ids`, so the same endpoints handle single and bulk assignment. Assignment responses include readable app and policy labels beside numeric IDs for Swagger/frontend use.
- `GET /policy-options` returns enabled connector/action/resource combinations
  from normalized `connector_tool_mappings`; the frontend uses it for cascading
  policy-builder dropdowns and does not offer unmapped combinations.
- Duplicate-aware policy resolution is available under `/apps/by-client-id/{client_id}/policy-assignments/resolve` and `/global-policy-assignments/resolve`. It returns `created`, `reused`, or `already_assigned`; direct equivalent policy create/update requests return `409`.
- Assignment-safe edit resolution is available under `PUT /apps/by-client-id/{client_id}/policy-assignments/{assignment_id}/resolve` and `PUT /global-policy-assignments/{assignment_id}/resolve`. Assignments have optional `display_name` values so apps can label shared definitions independently.
- `scripts/migrate_policy_assignment_display_names.py` adds/backfills assignment names. `scripts/deduplicate_policies.py` previews legacy duplicate consolidation and applies it only with `--apply`.
- `tests/test_policy_resolution_api.py` proves App A/App B policy reuse, shared-policy-safe edits, duplicate rejection, assignment-only deletion, and global-equivalent behavior. `tests/test_policy_deduplication.py` proves legacy merges preserve assignments and names.
- `tests/test_policy_metadata_api.py` proves `/policy-options` returns only
  connectors with enabled mappings and filters resources by action.
- The frontend policy builder currently lists GitHub and SharePoint only. Global policy rows display a globe; app-specific rows display GitHub or Microsoft/SharePoint connector marks, with a folder fallback for unknown connectors. SharePoint is not runtime-enabled yet.
- The frontend now has `/apps` and `/apps/[clientId]`. The list uses real app, connector-count, and effective-policy data; the detail page provides Overview, GitHub Connectors, numeric LLM configuration, effective Policies, and an authenticated Runtime Test. SharePoint remains a disabled coming-soon choice.
- Main and app-detail policy rows open a shared `policy-summary-modal.tsx` backed by `GET /policies/{policy_id}`. Edit/Delete buttons stop row propagation.
- App/global assignment bulk update/delete also uses `policy_ids`; the API returns `404` if a requested policy is not assigned in that app/global scope.
- Developer-friendly client-ID aliases exist under `/apps/by-client-id/{client_id}` and `/apps/by-client-id/{client_id}/policy-assignments`; they resolve to the same internal app rows and full assignment CRUD logic.
- App connector CRUD exists under `/apps/{app_id}/connectors` and `/apps/by-client-id/{client_id}/connectors`; connector references can use a numeric connector ID or connector name such as `github`.
- Effective policy assignment summaries exist under `/apps/{app_id}/effective-policy-assignments` and `/apps/by-client-id/{client_id}/effective-policy-assignments`; they return global plus app-specific assignments with policy IDs, assignment IDs, labels, and enabled flags.
- App create/update accepts an API key, stores only its SHA-256 hash, and never returns the plaintext key or hash. `src/nemo_mcp_guardrails/app_auth.py` centralizes hashing and constant-time verification; `authenticate_app()` accepts only matching, authorized client ID/API-key pairs.
- `tests/test_app_auth.py` is a self-cleaning Postgres authentication diagnostic covering valid, wrong-key, unknown-client, and unauthorized-app cases.
- `src/nemo_mcp_guardrails/api/auth.py` provides the reusable FastAPI `require_authenticated_app` dependency. It reads `X-App-ID` and `X-API-Key`, authenticates before runtime work begins, and returns the same generic `401` response for every invalid case.
- `GET /v1/guardrails/auth-check` is the first protected runtime proof endpoint. It verifies credentials and returns only the authenticated app identity; it does not load policies, NeMo, Docker, or MCP tools.
- `POST /v1/guardrails/run` is now the authenticated guarded runtime endpoint. It validates app credentials, loads stored `conversation_messages` for the app conversation, bootstraps from client-supplied `conversation_history` when needed, trims older turns by `NEMO_MAX_RUNTIME_CONTEXT_CHARS`, builds app-scoped NeMo rails and guarded GitHub MCP tools, calls `execute_guarded_message()`, stores the latest user/assistant turn when `conversation_id` is present, and returns a JSON execution response with history metadata.
- `src/nemo_mcp_guardrails/runtime_factory.py` respects separate `main_llm_config_id` and `guardrail_llm_config_id` values on the authenticated app. The guardrail config is injected into NeMo rails, and the main config is used by the LangChain agent. Missing config IDs fall back to `.env` Azure OpenAI settings. Only Azure OpenAI-compatible provider rows are executable for now; other providers return a clear unsupported-provider error.
- `src/nemo_mcp_guardrails/guarded_execution.py` now owns the reusable single-request sequence: input rail, early block, agent/guarded tools with optional trimmed history, controlled `tool_error` responses for connector `ToolException` failures, output rail, controlled blocked responses for Azure output `content_filter` failures, and structured result. `tests/test_nemo_mcp.py` still chooses test prompts and prints the familiar workflow sections.
- `tests/test_app_auth_http.py` is a self-cleaning HTTP authentication diagnostic covering missing headers, wrong keys, unknown clients, unauthorized apps, and valid credentials.
- `tests/test_guardrails_run_http.py` is a self-cleaning HTTP runtime diagnostic proving authenticated `/run` loads real app-scoped policy assignments, compiled prompt rules, and blocked tools while using fake rails/agent to avoid Docker and Azure.
- `tests/test_runtime_connector_access.py` proves linked apps can use the enabled GitHub connector and unlinked or disabled-link apps are rejected before MCP construction.
- `tests/test_app_connector_api.py` proves app connector CRUD, connector lookup by name or ID, upsert behavior, and missing-link errors.
- `tests/test_runtime_connector_credentials.py` proves default PAT fallback, app-specific `env:VAR_NAME` credential references, missing env vars, and unsupported reference schemes.
- The management/admin CRUD endpoints are not authenticated yet. Do not describe the current HTTP dependency as protecting `/apps`, `/policies`, or assignment CRUD.
- Normal full-run GitHub MCP tests should keep `GITHUB_MCP_READ_ONLY=1`. Manual local write testing can set `GITHUB_MCP_READ_ONLY=0` in `.env` and restart the API. Future write-capable scripted testing should be a separate opt-in harness with a throwaway repo and limited token.
- Do not add a custom `config/policies.yml` yet unless explicitly choosing to prototype the future admin/backend policy store. It is not a standard NeMo Guardrails file.

## When Editing This Project

- Do not add real API keys or PATs to committed files.
- Preserve the safe committed default for GitHub MCP mode; do not hardcode write mode into committed code.
- Keep blocked write-action tests separate from allowed read tests.
- Prefer small incremental tests.
- Add short docstrings to new Python functions/classes.
- Before changing non-doc code, preview the exact diff and wait for user approval.
- Update the relevant project docs whenever a code, configuration, database, testing, or local-setup change is completed.

## Recommended Next Step

Read `docs/open-work-backlog.md` before choosing the next implementation
slice. It is the single backlog for unfinished plans.

The assignment-aware, app-authentication, protected HTTP boundary,
authenticated runtime endpoint, reusable guarded-execution slice,
conversation-history persistence/truncation, app-selected main/guardrail LLM
selection, policy CRUD auto-compilation, app connector CRUD, env-based
connector credential resolution, frontend policy Create/Edit/Delete integration,
and duplicate consolidation are green. The next main implementation slice is
the app-management frontend for the GitHub MCP demo.
Use `docs/frontend-api-map.md`, `docs/frontend-screen-plan.md`, and
`docs/frontend-demo-flow.md` before changing UI code:

```text
users + apps + llm_configs now exist
connector terminology migration is complete
app_users + app_connectors now exist
runtime_factory.py enforces enabled app_connectors access before GitHub MCP construction
app_policy_assignments + global_policy_assignments now exist
app and assignment CRUD APIs now exist
policy_loader.py + prompt_rule_loader.py accept optional app IDs
no-app test runners explicitly warn that they load every enabled policy
tool_guard.py can compile and apply optional per-app blocked-tool sets
test_app_policy_scope.py proves real temporary DB assignments and cleanup
test_nemo_mcp.py accepts testing-only --app-id scope
app_auth.py verifies authorized client ID/API-key pairs
test_app_auth.py covers valid and rejected cases with cleanup
api/auth.py rejects invalid X-App-ID/X-API-Key requests before runtime work
GET /v1/guardrails/auth-check proves the protected boundary
test_app_auth_http.py covers valid and rejected HTTP cases with cleanup
test_guardrails_run_http.py covers allowed and blocked /run behavior with real DB scope
test_runtime_connector_access.py covers runtime connector access enforcement
test_app_connector_api.py covers app connector CRUD by app ID and client ID
test_runtime_connector_credentials.py covers env:VAR_NAME PAT resolution
POST /v1/guardrails/run executes app-scoped guarded requests
runtime_schemas.py defines the future-compatible message request and execution response
guarded_execution.py coordinates input rail, agent/tools, and output rail
test_nemo_mcp.py displays GuardedExecutionResult without owning coordination
runtime_factory.py selects app main/guardrail LLM configs, then builds Azure-backed NeMo rails, env-configured GitHub MCP tools, and the LangChain agent
policy CRUD auto-refreshes compiled_policy_rules
frontend-api-map.md maps backend endpoints to UI screens
frontend-screen-plan.md defines the first Next.js 13 screens/components
frontend-demo-flow.md defines the presentation GitHub MCP demo path
frontend/ contains Next.js 13 pages: /login, /signup, /apps, /apps/[clientId], /policies, /settings
/policies supports backend-backed duplicate-aware Create, assignment-safe Edit, and assignment-only Delete
Apps list/detail and GitHub connector/runtime management are backend-backed
-> add a readable LLM-config catalogue and named selectors next
-> defer production secrets-manager and admin auth unless specifically requested
-> keep policy CRUD auto-compilation covered by test_policy_auto_compile.py
-> keep normal GitHub MCP tests read-only
```

Future write-tool use cases, such as allowing PR merges only in sequence `A -> B -> C`, require argument and workflow-state checks. A simple tool-name denylist is not enough for that class of policy.

Useful verification commands for the current state:

- `python scripts/migrate_client_app_foundation.py`
- `python scripts/migrate_connector_terminology.py`
- `python scripts/migrate_app_relationships.py`
- `python scripts/migrate_policy_assignments.py`
- `python src/nemo_mcp_guardrails/policy_compiler.py`
- `python scripts/seed_normalized_policy_metadata.py`
- `python tests/test_tool_guard.py`
- `python tests/test_policy_loader.py`
- `python tests/test_app_policy_scope.py`
- `python tests/test_app_auth.py`
- `python tests/test_app_auth_http.py`
- `python tests/test_policy_assignment_api.py`
- `python tests/test_policy_auto_compile.py`
- `python tests/test_policy_metadata_api.py`
- `python tests/test_guardrails_run_http.py`
- `python tests/test_runtime_connector_access.py`
- `python tests/test_app_connector_api.py`
- `python tests/test_runtime_connector_credentials.py`
- `python tests/test_runtime_llm_selection.py`
- `python scripts/debug_nemo_output_check.py`
- `python scripts/run_api.py`
- `python -m py_compile src/nemo_mcp_guardrails/app_auth.py src/nemo_mcp_guardrails/guarded_execution.py src/nemo_mcp_guardrails/runtime_factory.py src/nemo_mcp_guardrails/api/app_schemas.py src/nemo_mcp_guardrails/api/apps.py src/nemo_mcp_guardrails/api/assignment_serializers.py src/nemo_mcp_guardrails/api/auth.py src/nemo_mcp_guardrails/api/runtime.py src/nemo_mcp_guardrails/api/runtime_schemas.py src/nemo_mcp_guardrails/policy_compiler.py src/nemo_mcp_guardrails/policy_rule_service.py src/nemo_mcp_guardrails/tool_guard.py src/nemo_mcp_guardrails/database/models.py src/nemo_mcp_guardrails/database/conversation_store.py src/nemo_mcp_guardrails/database/policy_loader.py src/nemo_mcp_guardrails/database/test_case_loader.py src/nemo_mcp_guardrails/database/prompt_rule_loader.py src/nemo_mcp_guardrails/prompt_rule_compiler.py scripts/seed_normalized_policy_metadata.py tests/test_nemo_mcp.py tests/test_tool_guard.py tests/test_policy_loader.py tests/test_app_policy_scope.py tests/test_app_auth.py tests/test_app_auth_http.py tests/test_policy_auto_compile.py tests/test_guardrails_run_http.py tests/test_runtime_connector_access.py tests/test_app_connector_api.py tests/test_runtime_connector_credentials.py tests/test_runtime_llm_selection.py scripts/debug_nemo_self_check.py scripts/debug_nemo_output_check.py`
- `python tests/test_nemo_mcp.py`
