# Project Context: NeMo Guardrails + GitHub MCP

## Confirmed Target Direction

The production target is a full-proxy Guardrails Management System used
primarily with GitHub and SharePoint, while remaining extensible to Outlook and
other connectors.

Important terminology change:

```text
app       = client application consuming the GMS
connector = external integration such as GitHub MCP, SharePoint, or Outlook
```

The terminology migration is complete:

```text
apps                    = client applications consuming the GMS
connectors              = external integrations
connector_actions       = actions supported by connectors
connector_resources     = resources supported by connectors
connector_tool_mappings = concrete connector tool mappings
```

Confirmed target behavior:

- one app can use multiple connectors
- users and apps have a many-to-many relationship
- main-agent and guardrail-classification LLMs can differ
- mandatory global policies apply to every app
- prototype webapp login uses email/password
- GMS acts as a full proxy for input rail, agent/tool execution, and output rail
- policy changes automatically compile or invalidate generated rules
- frontend target is Next.js 13
- frontend scaffold exists in `frontend/`; `/policies` has a read-only FastAPI
  adapter when `NEXT_PUBLIC_API_BASE_URL` is set

The authoritative target design is in `docs/target-architecture.md`.

## Goal

Research NVIDIA NeMo Guardrails and test how guardrails can sit around an LLM that uses GitHub MCP tools.

Long-term project idea: build a web app for administrators to drag and drop app-specific policy blocks, such as "block create GitHub repo" or "block GitHub issue creation", which are then parsed into backend guardrail rules.

## Current Stack

- Python
- LangChain
- Azure OpenAI
- GitHub MCP Server via Docker
- NVIDIA NeMo Guardrails
- `.env` for secrets
- `.env.example` for shareable placeholders

Backend/database direction:

- FastAPI
- SQLAlchemy
- PostgreSQL
- Postgres in Docker for the first local prototype
- pgAdmin in Docker or DBeaver for database inspection
- Later containerisation/OpenShift deployment

## Current Repository Layout

```text
config/                              NeMo Guardrails config
docs/                                handoff and architecture docs
scripts/                             runnable utilities, migrations, and debug scripts
tests/                               self-cleaning verification scripts
src/nemo_mcp_guardrails/             application/library code
src/nemo_mcp_guardrails/database/    future database code location
src/nemo_mcp_guardrails/helper/      helper package
logs/                                local logs
```

## Current Working Result

The system successfully:

- Connects to GitHub MCP.
- Loads GitHub MCP tools.
- Uses Azure OpenAI to call MCP read tools.
- Reads GitHub repositories, branches, and README files.
- Runs NeMo `self check input` before the LangChain agent can call MCP tools.
- Runs NeMo `self check output` after the LangChain agent returns a final answer.
- Blocks unsafe write/credential prompts through NeMo input rails.
- Blocks unsafe secret-like assistant responses through NeMo output rails.
- Keeps deterministic Python pre-checks only as a comparison/safety fallback.
- Wraps MCP tools with `src/nemo_mcp_guardrails/tool_guard.py` so broad tool restrictions and custom-resource argument matches can be blocked before execution.
- Uses `src/nemo_mcp_guardrails/policy_compiler.py` to prototype admin-style policy objects and generated policy artifacts.
- Feeds curated policy-generated tests into `tests/test_nemo_mcp.py`.
- Stores prototype policy rows in local Postgres through FastAPI CRUD endpoints.
- Previews compiler output from enabled database policy rows through `POST /policies/compile-preview`.
- Loads enabled Postgres input policies into runtime code through `src/nemo_mcp_guardrails/database/policy_loader.py`.
- Uses DB-loaded input policies to compile `tool_guard.py` executable guard rules, blocked-tool reporting, and `tests/test_nemo_mcp.py` generated blocked tests.
- Verifies DB policy loading through `tests/test_policy_loader.py`.
- Stores compiled NeMo rule text in `compiled_policy_rules`.
- Automatically refreshes `compiled_policy_rules` when policies are created or
  updated through the policy CRUD API.
- Injects enabled compiled rules into `config/prompts.yml` at runtime through `prompt_rule_compiler.py`.
- Seeds normalized app/action/resource/tool metadata through `scripts/seed_normalized_policy_metadata.py`.
- Backfills `allowed_test_case_expected_tools` from current allowed test rows.
- Creates the additive target-foundation tables `users`, `llm_configs`, and
  `apps`.
- Uses connector terminology consistently across the normalized database,
  policy API, policy compiler, loaders, seed scripts, and tests.
- Creates `app_users` for user/app management roles and `app_connectors` for
  app-specific connector access and credential references.
- Creates `app_policy_assignments` and `global_policy_assignments` without
  duplicating the existing reusable policy definitions in `policies`.
- Exposes client-app CRUD under `/apps`, app-specific policy assignment CRUD
  under `/apps/{app_id}/policy-assignments`, and global assignment CRUD under
  `/global-policy-assignments`.
- Uses `policy_ids` for assignment POST bodies, so the same endpoints handle
  single and bulk assignments. Assignment responses include readable app and
  policy labels for Swagger/frontend use.
- Uses `policy_ids` for assignment bulk update/delete too, returning `404`
  when a requested policy is not assigned in that app/global scope.
- Adds client-ID convenience routes under `/apps/by-client-id/{client_id}` so
  developers do not need to remember numeric app IDs for app lookup or
  policy-assignment management.
- Exposes effective policy assignment views so developers can see global and
  app-specific policies assigned to one app in one response.
- Hashes API keys received by app create/update requests and never returns the
  plaintext key or stored hash in API responses.
- Authenticates runtime HTTP requests through the reusable
  `require_authenticated_app` FastAPI dependency using `X-App-ID` and
  `X-API-Key`.
- Exposes `GET /v1/guardrails/auth-check` as a protected proof endpoint and
  verifies it through the self-cleaning `tests/test_app_auth_http.py`.
- Exposes `POST /v1/guardrails/run` as an authenticated runtime endpoint that
  builds app-scoped policies, prompt rules, blocked tools, NeMo rails, and
  GitHub MCP tools, then executes the submitted message. When
  `conversation_id` is present, it persists the latest user/assistant turn in
  `conversation_messages`; when stored history exists, it is loaded and passed
  to the agent after trimming older turns by `NEMO_MAX_RUNTIME_CONTEXT_CHARS`.
- Runtime LLM selection is app-aware. The authenticated app's
  `guardrail_llm_config_id` is used for NeMo rails, and
  `main_llm_config_id` is used for the LangChain agent. Missing config IDs use
  the `.env` Azure OpenAI deployment. Non-Azure provider rows are allowed as
  future metadata but are not executable yet.
- Uses `src/nemo_mcp_guardrails/guarded_execution.py` for reusable
  single-request input-rail, agent/guarded-tool, and output-rail coordination.
- Provides a Next.js 13 frontend scaffold under `frontend/` for `/login`,
  `/signup` admin-managed notice, `/apps`, `/apps/[clientId]`, `/policies`,
  `/user-management`, and `/settings`.
- Keeps the frontend in mock mode when `NEXT_PUBLIC_API_BASE_URL` is absent,
  and switches `/policies` to read real apps/global assignments/effective app
  assignments from FastAPI when `frontend/.env.local` sets
  `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000`.
- The backend-backed policy page now supports duplicate-aware Create,
  assignment-safe Edit, and assignment-only Delete. Assignment `display_name`
  values keep app-specific labels separate from reusable policy behavior.

## Current Runtime Flow

```text
User prompt
-> Python pre-check report only
-> compiled_policy_rules are injected into config/prompts.yml template
-> NeMo self_check_input using the app guardrail AzureChatOpenAI config
-> if blocked: safe refusal and no MCP tool call
-> if passed: LangChain agent
-> src/nemo_mcp_guardrails/tool_guard.py wraps MCP tools and blocks restricted tool names before execution
-> GitHub MCP tools, normally read-only through `GITHUB_MCP_READ_ONLY=1`
-> NeMo self_check_output using the app guardrail AzureChatOpenAI config
-> final answer
```

## Current Policy Compiler Prototype

`src/nemo_mcp_guardrails/policy_compiler.py` contains the structured policy-object prototype.

Example input policy:

```json
{
  "app": "github",
  "action": "create",
  "resource": "issue",
  "effect": "block"
}
```

The compiler uses `InputPolicyObject` for input/tool policies and `OutputPolicyObject` for output policies.

For input policies, it uses adapter-style GitHub metadata:

- action synonyms
- resource synonyms
- action/resource to MCP tool mappings
- reusable prompt templates for generated tests

Current default policy objects cover:

- Create/update/comment on GitHub issues
- Create/update/merge/approve GitHub pull requests
- Create GitHub branches
- Create/update/delete/push GitHub files
- Create GitHub repositories
- Fork GitHub repositories

The compiler currently generates:

- NeMo self-check rule text preview
- compiler-generated blocked MCP tool names
- curated blocked test prompts consumed by `tests/test_nemo_mcp.py`
- output self-check rule previews for credential/secret output policies

`compile_policy_test_prompts()` returns one test per policy object by default, so the full test runner stays manageable.

## Adding Policies In The Current Prototype

For runtime policy testing, add enabled policy rows through FastAPI Swagger,
DBeaver, or direct SQL. Edit `src/nemo_mcp_guardrails/policy_compiler.py` only
when adding a new GitHub action/resource/tool mapping or new compiler metadata.

For a new GitHub input/tool policy:

1. Add or reuse an action/resource tool mapping in `GITHUB_WRITE_TOOL_MAPPINGS`.
2. Add action synonyms in `GITHUB_ACTION_SYNONYMS` if the action is new.
3. Add resource synonyms in `GITHUB_RESOURCE_SYNONYMS` if the resource is new.
4. Add an `InputPolicyObject` to `DEFAULT_INPUT_POLICY_OBJECTS`.
5. Add or enable the policy row in Postgres.
6. Policy CRUD automatically refreshes `compiled_policy_rules`.
7. Run the compiler, tool guard, and full MCP tests.

Example:

```python
InputPolicyObject(
    app="github",
    action="create",
    resource="issue",
    effect="block",
)
```

For a new output policy, add an enabled output policy row in Postgres through
the API. Policy CRUD automatically refreshes `compiled_policy_rules`; then
verify that the output rule count appears in `tests/test_nemo_mcp.py`.

Current important design note:

- `config/prompts.yml` is now a stable template with `{{ input_policy_rules }}` and `{{ output_policy_rules }}` placeholders.
- `prompt_rule_loader.py` loads enabled rows from `compiled_policy_rules`.
- `prompt_rule_compiler.py` injects those rows into the prompt template before `LLMRails` is created.
- The static prompt text remains as context/fallback around the dynamic DB rules.

## Current Safety Layers

```text
config/prompts.yml
-> stable template for NeMo self_check_input

config/prompts.yml
-> stable template for NeMo self_check_output

compiled_policy_rules
-> dynamic input/output rules injected into prompts.yml templates

src/nemo_mcp_guardrails/tool_guard.py
-> blocks DB-derived restricted MCP tool names before execution

GitHub MCP Docker env
-> GITHUB_MCP_READ_ONLY=1 maps to GitHub MCP `GITHUB_READ_ONLY=1`
-> prevents write tools from being offered during normal tests
```

Normal full-run GitHub MCP tests should remain read-only. Manual local write
testing can set `GITHUB_MCP_READ_ONLY=0` in `.env`, then restart
`scripts/run_api.py`. Future write-capable scripted testing should use a
separate opt-in harness with a throwaway repository, limited token, and
explicit safety flags.

## Important Implementation Detail

NeMo input rails work when the project creates rails like this:

```python
prompt_rule_config = build_rails_config_with_prompt_rules("config")
rails_config = prompt_rule_config.rails_config
rails = LLMRails(rails_config, llm=model)
```

This matters because stock `GuardrailsMiddleware(config_path="config")` constructs its own internal NeMo LLM. In this environment, that path previously tried to use an old OpenAI/LangChain client and failed with `openai.ChatCompletion` / `APIRemovedInV1`.

## Prompt Design Status

`config/prompts.yml` currently defines `self_check_input` and `self_check_output` as yes/no classifiers:

- `no` means the request is allowed
- `yes` means the request asks for a restricted operation and should be blocked

This matches NeMo's default parser, where `yes` maps to unsafe/block and `no` maps to safe/allow.

## Output Rails Status

Output rails are enabled through `config/config.yml`:

```yaml
output:
  flows:
    - self check output
```

`tests/test_nemo_mcp.py` reads `rails_config.rails.output.flows` and runs `rails.check_async(..., rail_types=[RailType.OUTPUT])` after each final response.

The output self-check prompt only includes the assistant response:

```text
Assistant response:
{{ bot_response }}
```

It intentionally does not echo the user input, because unsafe user prompts containing fake token-like strings can trigger Azure content filtering before NeMo can classify the assistant response.

`scripts/debug_nemo_output_check.py` verifies safe assistant output passes and fake token/environment-variable output blocks.

## Current DB-Backed Runtime State

The first Postgres/FastAPI CRUD slice, compile-preview endpoint, and runtime database policy loader are in place.

```text
Postgres policies
-> policy_loader.py
-> InputPolicyObject / OutputPolicyObject
-> compiler
-> tool_guard.py blocked tool names
-> generated tests in tests/test_nemo_mcp.py
```

Latest verified enabled input policy sample:

```text
github create issue block -> issue_write
github create pull_request block -> create_pull_request
github merge pull_request block -> merge_pull_request
github update file block -> create_or_update_file
```

Output policies are compiled into `compiled_policy_rules`; enabled output rules
are now injected into the runtime NeMo output prompt by `prompt_rule_compiler.py`.
`POST /policies/compile-rules` remains available as a manual full-resync/debug
endpoint, but normal policy create/update flows no longer require it.

## Current Normalized Metadata State

The normalized metadata slice has started. The new tables are:

```text
connectors
connector_actions
connector_resources
connector_tool_mappings
allowed_test_case_expected_tools
```

Seed with:

```powershell
python scripts/seed_normalized_policy_metadata.py
```

Latest expected counts:

```text
connectors 2
connector_actions 11
connector_resources 10
connector_tool_mappings 33
allowed_test_case_expected_tools 3
```

## Client-App Foundation State

The first target-architecture schema slice is additive and complete:

```text
users
llm_configs
apps
```

Run the idempotent foundation migration with:

```powershell
python scripts/migrate_client_app_foundation.py
```

The `apps` table starts empty by design. App CRUD, centralized API-key hashing,
reusable app authentication, and the first protected HTTP runtime endpoint now
exist. User login, admin-route authorization, and LLM-secret handling do not
exist yet.

## Current Runtime App Scope

App connector management APIs now exist, so apps can be linked to GitHub
without manual database edits:

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

`connector_ref` can be a numeric connector ID or connector name such as
`github`.

```text
POST /v1/guardrails/run
-> require_authenticated_app
-> authenticated app ID
-> check app_connectors for enabled GitHub connector access
-> reject runtime construction if app is not linked to GitHub
-> app_policy_assignments + global_policy_assignments
-> active global policies + active app policies
-> app-scoped NeMo prompt rules
-> app-scoped tool guard
-> execute input rail + guarded agent/tools + output rail
```

The `users`, `apps`, `app_users`, `connectors`, and `app_connectors`
foundation now exists. The credential output policy is globally assigned;
GitHub write policies are currently unassigned.

Management CRUD now requires JWT authentication. Developers see only apps
linked through active app-developer `app_users` links. App creation is
system-admin-only; linked app developers can mutate their assigned apps, and
system admins can access every app. Global policy mutation and guardrail-LLM
selection are system-admin-only. The existing pre-RBAC demo users/apps are
linked by the idempotent `scripts/backfill_existing_app_users.py` script.

Assignment management APIs exist. `policy_loader.py`, `prompt_rule_loader.py`,
and `build_rails_config_with_prompt_rules()` now accept an optional app ID.
With an app ID, they load enabled global assignments plus enabled assignments
for that app. Without an app ID, they intentionally preserve the current
all-enabled testing behavior and print a warning in the main diagnostics.

`tool_guard.py` can compile a blocked-tool set for an optional app ID and apply
that set to wrapped tools. `tests/test_app_policy_scope.py` proves real
temporary DB assignments scope both NeMo rules and blocked tools, then cleans
up. `tests/test_nemo_mcp.py --app-id ...` passes a testing-only app scope
through the full read-only runner.

`app_auth.py` verifies app credentials at the service layer.
`api/auth.py` exposes that verifier through `require_authenticated_app`, and
`GET /v1/guardrails/auth-check` proves invalid requests are rejected before
runtime work. `POST /v1/guardrails/run` now reuses the authenticated scope and
executes the submitted message through `execute_guarded_message()`.
`tests/test_guardrails_run_http.py` proves allowed and blocked HTTP runtime
cases with real temporary DB policy scope and fake rails/agent.
`tests/test_runtime_connector_access.py` proves enabled GitHub connector
links are required before MCP tools are built.
`tests/test_app_connector_api.py` proves app connector CRUD and client-ID
aliases.

Do not remove the flat `policies.connector/action/resource` columns yet.
