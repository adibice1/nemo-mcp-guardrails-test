# Runtime Flow Map

## Target Full-Proxy Flow

The current flow documented below is the GitHub research prototype. The
confirmed production target adds client-app authentication and makes the GMS a
full proxy:

```text
client app + app ID/API key
-> authenticate authorized app
-> load mandatory global rules
-> load app-specific rule assignments
-> load app connectors and LLM configurations
-> build guardrail rails with the app's guardrail LLM config
-> build agent with the app's main LLM config
-> input rail
-> GMS agent
-> tool guard
-> connector tool
-> agent final response
-> output rail
-> client app and user
```

Target terminology:

```text
app       = client application using GMS
connector = GitHub MCP, SharePoint, Outlook, etc.
```

The connector terminology migration is complete. `apps` represent GMS client
applications and `connectors` represent external integrations.

## Current Management API Flow

```text
POST /apps
-> hash submitted API key
-> store client app without plaintext credentials

POST /apps/{app_id}/policy-assignments
-> validate app and reusable policy
-> create or update one or more app-specific assignments from policy_ids

POST /apps/by-client-id/{client_id}/policy-assignments
-> resolve client_id to app_id
-> use the same app-specific assignment flow

PUT/DELETE /apps/by-client-id/{client_id}/policy-assignments/{assignment_id}
-> resolve client_id to app_id
-> use the same app-specific update/delete flow

PUT/DELETE /apps/by-client-id/{client_id}/policy-assignments
-> resolve client_id to app_id
-> bulk update/delete assignment rows by policy_ids
-> return 404 if any requested policy_id is not assigned to the app

GET /apps/{app_id}/effective-policy-assignments
GET /apps/by-client-id/{client_id}/effective-policy-assignments
-> return mandatory global assignments and app-specific assignments together

POST /global-policy-assignments
-> validate reusable policies
-> create or update one or more mandatory global assignments from policy_ids

PUT/DELETE /global-policy-assignments
-> bulk update/delete global assignment rows by policy_ids
-> return 404 if any requested policy_id is not globally assigned

POST /policies
-> validate readable connector/action/resource/category fields
-> store policy row
-> compile its NeMo rail rule in the same transaction
-> rollback and return 400 if the compiler cannot build a rule

PUT /policies/{policy_id}
-> update policy row
-> increment policy_version
-> mark previous compiled rules stale and disabled
-> compile a fresh active rule when the policy remains enabled
-> leave no active compiled rule when the policy is disabled

POST /policies/compile-rules
-> manual full resync/debug endpoint
-> marks existing compiled rules stale and disabled
-> creates fresh active compiled rules for all enabled policies
```

These assignment APIs manage scope. Policy and compiled-rule loaders now
accept an optional app ID and filter to enabled global assignments plus enabled
assignments for that app. The current no-app integration runner still loads all
enabled policies and prints an explicit testing-only warning.

Assignment POST bodies use the same shape for single and bulk operations:

```json
{
  "policy_ids": [26, 12, 13],
  "enabled": true
}
```

Assignment responses include readable app and policy labels such as
`app_label` and `policy_label` beside the numeric IDs.

Developers can use either the numeric app ID or the app `client_id` in Swagger.
The `client_id` routes are only convenience aliases; assignments are still
stored against the app's internal `app_id`.

The effective-policy view is read-only. It exists so developers can quickly
answer "which policies currently apply to this app?" without manually checking
both global and app assignment tables.

This is a concise map of how the current project moves from database policies to the terminal output shown by `tests/test_nemo_mcp.py`.

The full runner accepts optional testing-only scope through
`tests/test_nemo_mcp.py --app-id ...`. It passes that app ID into compiled
prompt-rule loading, runtime input-policy loading, and blocked-tool
compilation. It does not authenticate the app yet.

`tests/test_app_policy_scope.py` creates two temporary real DB apps, assigns
issue creation only to App A, verifies App A/App B scope differences, and
deletes its temporary rows in `finally`.

`src/nemo_mcp_guardrails/app_auth.py` centralizes API-key hashing and
constant-time verification. `authenticate_app()` returns only an authorized app
whose client ID and API key match. `tests/test_app_auth.py` proves valid and
rejected cases with self-cleaning temporary rows.

## Current Protected Runtime Boundary

```text
GET /v1/guardrails/auth-check
-> require_authenticated_app()
-> read X-App-ID and X-API-Key
-> authenticate_app()
-> reject invalid requests with generic 401
-> return authenticated app identity
```

The proof endpoint deliberately stops after authentication. It does not load
policies, create NeMo rails, start Docker, or expose MCP tools.
`tests/test_app_auth_http.py` verifies missing headers, wrong keys, unknown
clients, unauthorized apps, and valid credentials, then removes its temporary
rows.

`POST /v1/guardrails/run` now reuses the dependency, builds app-scoped prompt
rules, runtime policies, tool blocking, and separate runtime LLMs, then
executes the submitted message through the guarded runtime. The NeMo rails use
the app's `guardrail_llm_config_id`; the LangChain agent uses the app's
`main_llm_config_id`. Missing config IDs fall back to the `.env` Azure OpenAI
deployment. Non-Azure providers are recorded for the target architecture but
return a clear unsupported-provider error in the current prototype. When
`conversation_id` is provided, the endpoint loads stored prior turns for that
app conversation. If no stored turns exist, it bootstraps from client-supplied
`conversation_history`. Older turns are trimmed by
`NEMO_MAX_RUNTIME_CONTEXT_CHARS` so the latest message plus recent history fits
before Azure OpenAI is called.

`tests/test_guardrails_run_http.py` is the focused HTTP integration proof for
this endpoint. It uses fake rails/agent to avoid Docker and Azure, while still
using real temporary DB app rows, policy rows, app assignments,
`compiled_policy_rules`, prompt-rule loading, and blocked-tool loading.
`tests/test_runtime_connector_access.py` verifies linked apps are allowed and
unlinked or disabled-link apps are rejected before GitHub MCP tools are built.

```text
POST /v1/guardrails/run
-> authenticate app
-> verify app has an enabled app_connectors link to the GitHub connector
-> load stored conversation_messages for app_id + conversation_id
-> use client-supplied conversation_history only when no stored history exists
-> keep newest prior turns that fit beside the latest message
-> select guardrail LLM config for NeMo rails
-> select main LLM config for the LangChain agent
-> input rail checks latest message
-> agent receives trimmed history + latest message
-> connector tool failures return status=tool_error instead of HTTP 500
-> output rail checks assistant response
-> Azure output content-filter failures return a controlled blocked response
-> store latest user/assistant turn when conversation_id exists
-> return response plus history metadata
```

Reusable guarded execution has now been extracted:

```text
guarded_execution.py
-> execute_guarded_message()
-> input rail
-> early block or agent with guarded tools and trimmed history
-> controlled tool_error for connector ToolException failures
-> output rail
-> controlled blocked response for Azure output content_filter failures
-> GuardedExecutionResult

test_nemo_mcp.py
-> selects test prompts
-> calls execute_guarded_message()
-> prints the familiar workflow sections
```

The HTTP runtime endpoint now calls the same reusable function.

## Big Picture

```text
Postgres policy rows
-> policy_loader.py converts rows into policy objects
-> policy_compiler.py compiles policy objects into guardrail artifacts
-> compiled_policy_rules are loaded and injected into prompts.yml templates
-> test_nemo_mcp.py builds allowed + blocked test prompts
-> NeMo input rail decides pass/block
-> LangChain agent calls GitHub MCP tools for passed prompts
-> tool_guard.py blocks restricted MCP tools before execution
-> NeMo output rail checks final response
-> terminal prints precheck report, rail results, tools called, final response
```

The database is now the active source for runtime policies. `policy_compiler.py` is still important because it explains what each policy means.

## Normalized Metadata Seeding

```text
scripts/seed_normalized_policy_metadata.py
```

Seeds system/reference metadata from `policy_compiler.py`:

```text
GITHUB_METADATA_TOOL_MAPPINGS
-> connectors
-> connector_actions
-> connector_resources
-> connector_tool_mappings
```

It also backfills:

```text
allowed_test_cases.expected_tools
-> allowed_test_case_expected_tools
-> connector_tool_mappings
```

Expected current counts:

```text
connectors 2
connector_actions 11
connector_resources 10
connector_tool_mappings 33
allowed_test_case_expected_tools 3
```

The normalized policy-reference migration is now applied:

```text
policies.connector_id/action_id/resource_id
-> policy_loader.py eagerly loads normalized relationships
-> normalized names are preferred at runtime
-> flat app/action/resource strings remain fallback compatibility fields
```

`compiled_policy_rules` also stores `policy_version` and `stale`. Runtime
prompt-rule loading ignores stale rows.

Policy CRUD accepts readable names such as:

```text
github + create + issue
```

The API resolves and stores the corresponding `app_id`, `action_id`, and
`resource_id`, while keeping the readable names synchronized for current
responses and compatibility.

For input policies, the API then checks for an enabled matching
`connector_tool_mappings` row:

```text
readable names
-> normalized IDs
-> enabled app/action/resource tool mapping exists
-> save policy
```

This rejects individually valid names combined into unsupported operations,
such as `github + merge + issue`.

## Policy Loading

```text
src/nemo_mcp_guardrails/database/policy_loader.py:98
load_input_policy_entries()
```

Loads enabled `input` policy rows from Postgres. Each DB row is converted into a `LoadedInputPolicy`, which keeps both the compiled policy object and the DB source ID.

```text
-> policy_loader.py:58
   _to_input_policy_object()
```

Converts a DB `PolicyRecord` into an `InputPolicyObject`.

```text
-> policy_compiler.py:5
   InputPolicyObject
```

This is the compiler-friendly shape of an input policy, for example:

```text
app=github, action=create, resource=issue, effect=block
```

```text
policy_loader.py:121
load_input_policy_objects()
```

Returns only the raw `InputPolicyObject`s. This is used by `tool_guard.py` when it only needs the blocked tool names and does not need DB IDs.

```text
policy_loader.py:127
load_output_policy_objects()
```

Loads enabled `output` policy rows from Postgres and converts them into `OutputPolicyObject`s. These can be compiled into output rail rule text, stored in `compiled_policy_rules`, and injected into the runtime NeMo output prompt.

## Prompt Rule Loading

```text
src/nemo_mcp_guardrails/database/prompt_rule_loader.py:21
load_prompt_policy_rules()
```

Loads enabled rule rows from the `compiled_policy_rules` table. These rows are
generated artifacts refreshed automatically by policy create/update and can
also be regenerated through `POST /policies/compile-rules`.

```text
-> src/nemo_mcp_guardrails/prompt_rule_compiler.py:23
   format_prompt_rule_block()
```

Formats loaded input/output rules as prompt-ready bullet lists.

```text
-> src/nemo_mcp_guardrails/prompt_rule_compiler.py:52
   build_rails_config_with_prompt_rules()
```

Reads `config/config.yml`, `config/prompts.yml`, and `config/rails.co`, injects the loaded DB rule blocks into `{{ input_policy_rules }}` and `{{ output_policy_rules }}`, then builds the runtime `RailsConfig` in memory.

## Policy Compilation

```text
src/nemo_mcp_guardrails/policy_compiler.py:275
compile_policy()
```

Compiles one `InputPolicyObject` into:

```text
CompiledInputPolicy(
  input_rail_rule,
  blocked_tools,
  test_cases
)
```

Example output for `github + create + issue + block`:

```text
input_rail_rule = Answer "yes" when the user asks to create...
blocked_tools = ("issue_write",)
test_cases = ("Blocked: create issue", ...)
```

```text
policy_compiler.py:236
compile_input_rail_rule()
```

Creates the human-readable NeMo self-check rule sentence.

```text
policy_compiler.py:250
compile_test_cases()
```

Creates generated blocked test prompts from compiler synonyms/templates.

```text
policy_compiler.py:298
compile_policy_test_prompts()
```

Creates the test-runner prompt dictionaries consumed by `tests/test_nemo_mcp.py`.

```text
policy_compiler.py:319
compile_blocked_tools()
```

Compiles all input policies into the set of blocked MCP tool names.

```text
policy_compiler.py:333
compile_output_rail_rules()
```

Compiles output policy objects into output self-check rule text.

## Allowed Test Case Loading

```text
src/nemo_mcp_guardrails/database/test_case_loader.py:83
load_allowed_test_cases()
```

Loads enabled rows from the `allowed_test_cases` table.

Expected tools are loaded through:

```text
allowed_test_cases
-> allowed_test_case_expected_tools
-> connector_tool_mappings.tool_name
```

If an allowed test has no normalized expected-tool links, the loader falls
back to its legacy comma-separated `expected_tools` value.

Allowed-test create/update requests accept readable tool-name lists:

```json
{
  "expected_tools": ["search_repositories", "get_file_contents"]
}
```

The API resolves enabled `connector_tool_mappings`, replaces the join rows, and keeps the
legacy text value synchronized temporarily.

```text
-> test_case_loader.py:69
   _to_loaded_allowed_test_case()
```

Converts each DB row into a `LoadedAllowedTestCase`, preserving the DB ID and
normalized expected tool names for terminal display.

If Postgres is down or there are no enabled allowed test cases, the loader falls back to default allowed read-only GitHub tests. If the DB has only one enabled allowed test case, only that one DB test case is used.

## Full Test Runner Flow

```text
tests/test_nemo_mcp.py:312
main()
```

Starts the full integration test runner.

```text
-> test_nemo_mcp.py:414
   build_rails_config_with_prompt_rules()
```

Builds the NeMo config using static prompt templates plus enabled rows from `compiled_policy_rules`.

```text
-> test_nemo_mcp.py:432
   load_input_policy_entries()
```

Loads enabled runtime input policies from the DB.

```text
-> test_nemo_mcp.py:151
   print_runtime_policy_summary()
```

Prints the DB policy IDs and their compiled blocked tool names in the terminal.

```text
-> test_nemo_mcp.py:435
   load_allowed_test_cases()
```

Loads enabled allowed test cases from the DB.

```text
-> test_nemo_mcp.py:207
   print_allowed_test_case_summary()
```

Prints allowed test case DB IDs, names, and expected tools.

```text
-> test_nemo_mcp.py:438
   test_prompts = [...]
```

Builds the final test execution list:

```text
allowed DB test cases
+ generated blocked tests from DB policies
+ hardcoded credential/security regression tests
```

```text
-> test_nemo_mcp.py:222
   compile_allowed_test_prompts()
```

Turns loaded allowed test cases into test-runner prompt dictionaries.

```text
-> test_nemo_mcp.py:178
   compile_runtime_policy_test_prompts()
```

Takes DB-loaded input policies, calls `compile_policy_test_prompts()`, and appends labels like:

```text
[DB policy #12]
```

This is what proves the blocked tests came from DB-backed policies instead of only static Python defaults.

```text
-> test_nemo_mcp.py:451
   for test in test_prompts:
```

Runs each test prompt and prints the sections seen in the terminal.

## Per-Test Execution Flow

For each prompt, the terminal output is produced in this order:

```text
test name
-> user prompt
-> old Python precheck report
-> NeMo input rail result
-> MCP tools called, if allowed
-> NeMo output rail result
-> final response
```

```text
tests/test_nemo_mcp.py:239
precheck_user_prompt()
```

Reports what the old deterministic Python precheck would have blocked. This is not the main enforcement path unless `ENFORCE_PYTHON_PRECHECK=true`.

```text
test_nemo_mcp.py:75
apply_output_rail()
```

Runs NeMo output rails over the final assistant response.

```text
test_nemo_mcp.py:113
extract_tool_names()
```

Extracts MCP tool names from the LangChain result so the terminal can show which tools were called.

```text
test_nemo_mcp.py:138
print_tool_summary()
```

Prints the `MCP TOOLS CALLED` section.

## Tool Guard Flow

```text
src/nemo_mcp_guardrails/tool_guard.py:10
BLOCKED_GITHUB_MCP_TOOLS = ...
```

The backward-compatible constant loads the no-app all-enabled blocked-tool set.
`tool_guard_rules_for_app(app_id=...)` compiles per-app immutable rules that
retain optional `conditions.custom_resource` values.

```text
-> policy_loader.py:121
   load_input_policy_objects()
-> policy_compiler.py
   compile_policy()
-> tool_guard.py
   ToolGuardRule(tool_names, custom_resource)
```

`blocked_tool_names_for_app(app_id=...)` flattens those rules for API reporting.
At execution, broad rules block every matching tool call; conditional rules
recursively compare normalized exact MCP argument values before blocking.

```text
issue_write
create_pull_request
merge_pull_request
create_or_update_file
```

```text
tool_guard.py
guard_mcp_tool()
```

Wraps each MCP tool with the supplied immutable blocked-tool set. If the tool
name is blocked, it returns a refusal before the real MCP tool can run.

```text
tool_guard.py:23
guarded_coroutine()
```

This is the actual async wrapper that blocks restricted tools or forwards allowed tools to GitHub MCP.

## FastAPI Compile Flow

These endpoints are used to inspect and store compiled artifacts through Swagger.

```text
src/nemo_mcp_guardrails/api/policies.py:99
compile_policy_preview()
```

Reads enabled DB policies and returns a temporary preview:

```text
input_rules
blocked_tools
test_prompts
output_rules
```

This does not store anything.

```text
src/nemo_mcp_guardrails/policy_rule_service.py
```

Owns reusable policy-rule compilation:

```text
policy row
-> to_input_policy_object() or to_output_policy_object()
-> compile_policy_rule_record()
-> refresh_compiled_policy_rule()
-> compiled_policy_rules
```

`POST /policies` and `PUT /policies/{policy_id}` call this service inside the
same database transaction as the policy write. Old compiled rows are marked
`stale=true` and `enabled=false`; a fresh row is inserted only when the policy
is enabled.

```text
policies.py
compile_and_store_policy_rules()
```

The manual resync endpoint still exists. It marks existing stored compiled
rules stale/disabled and inserts fresh rows for every enabled policy.

```text
policies.py:145
list_compiled_policy_rules()
```

Reads the currently stored compiled rules.

## What Comes From Where

| Thing | Current Source | Notes |
| --- | --- | --- |
| Runtime input policies | Postgres `policies` table | `policy_loader.py` accepts optional app scope. |
| App policy scope | Postgres `app_policy_assignments` | App-scoped loader filtering implemented. |
| Global policy scope | Postgres `global_policy_assignments` | Included in every app-scoped loader query. |
| Runtime HTTP app identity | `X-App-ID` + `X-API-Key` verified against Postgres `apps` | `require_authenticated_app` protects `/v1/guardrails/auth-check` and `/v1/guardrails/run`. |
| Runtime execution endpoint | `POST /v1/guardrails/run` | Authenticates, builds app-scoped runtime parts, calls `execute_guarded_message()`, and returns JSON execution results. |
| Reusable guarded message coordination | `guarded_execution.py` | Returns full rail results, final response, agent result, and called tools. |
| Runtime blocked tool names | DB policies compiled by `policy_compiler.py` | `blocked_tool_names_for_app(app_id=...)` receives the authenticated app ID in the run context. |
| Generated blocked test prompts | DB policies compiled by `policy_compiler.py` | Used by `test_nemo_mcp.py`. |
| Allowed test prompts | Postgres `allowed_test_cases` table | Falls back to defaults if DB unavailable/empty. |
| Allowed expected-tool join rows | Postgres `allowed_test_case_expected_tools` table | Preferred by `test_case_loader.py`; legacy text remains a fallback. |
| Output policy objects | Postgres `policies` table | Loadable/compilable now. |
| Normalized connector/action/resource metadata | Postgres `connectors`, `connector_actions`, `connector_resources`, `connector_tool_mappings` | Seeded by `scripts/seed_normalized_policy_metadata.py`. |
| Actual NeMo input prompt template | `config/prompts.yml` + DB rules | `prompt_rule_compiler.py` injects `compiled_policy_rules` into the template. |
| Actual NeMo output prompt template | `config/prompts.yml` + DB rules | `prompt_rule_compiler.py` injects `compiled_policy_rules` into the template. |
| Stored compiled rule text | Postgres `compiled_policy_rules` table | Auto-refreshed by policy CRUD and manually resyncable through `POST /policies/compile-rules`; consumed by `prompt_rule_loader.py`. |

## Current End State In Terminal

When `tests/test_nemo_mcp.py` runs successfully, the terminal should show:

```text
NeMo prompt policy rules loaded
-> input/output rule counts from compiled_policy_rules

Runtime input policies loaded
-> DB policy IDs and blocked tools

Allowed test cases loaded
-> DB allowed test IDs and expected tools

Each test case
-> old Python precheck report
-> NeMo input rail result
-> MCP tools called, for allowed prompts
-> NeMo output rail result
-> final response
```

That is the current proof that policies and allowed tests are coming from the database, then being compiled into runnable guardrail/test artifacts.
