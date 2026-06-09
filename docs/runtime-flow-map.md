# Runtime Flow Map

This is a concise map of how the current project moves from database policies to the terminal output shown by `scripts/test_nemo_mcp.py`.

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
-> apps
-> app_actions
-> app_resources
-> tool_mappings
```

It also backfills:

```text
allowed_test_cases.expected_tools
-> allowed_test_case_expected_tools
-> tool_mappings
```

Expected current counts:

```text
apps 2
app_actions 11
app_resources 10
tool_mappings 33
allowed_test_case_expected_tools 3
```

The normalized policy-reference migration is now applied:

```text
policies.app_id/action_id/resource_id
-> policy_loader.py eagerly loads normalized relationships
-> normalized names are preferred at runtime
-> flat app/action/resource strings remain fallback compatibility fields
```

`compiled_policy_rules` also stores `policy_version` and `stale`. Runtime
prompt-rule loading ignores stale rows.

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

Loads enabled rule rows from the `compiled_policy_rules` table. These rows are generated artifacts created by `POST /policies/compile-rules`.

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

Creates the test-runner prompt dictionaries consumed by `scripts/test_nemo_mcp.py`.

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

```text
-> test_case_loader.py:69
   _to_loaded_allowed_test_case()
```

Converts each DB row into a `LoadedAllowedTestCase`, preserving the DB ID for terminal display.

If Postgres is down or there are no enabled allowed test cases, the loader falls back to default allowed read-only GitHub tests. If the DB has only one enabled allowed test case, only that one DB test case is used.

## Full Test Runner Flow

```text
scripts/test_nemo_mcp.py:312
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
scripts/test_nemo_mcp.py:239
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

At import time, loads DB-backed input policies and compiles them into blocked MCP tool names.

```text
-> policy_loader.py:121
   load_input_policy_objects()
-> policy_compiler.py:319
   compile_blocked_tools()
```

The result is the runtime blocked tool set, for example:

```text
issue_write
create_pull_request
merge_pull_request
create_or_update_file
```

```text
tool_guard.py:20
guard_mcp_tool()
```

Wraps each MCP tool. If the tool name is blocked, it raises an error before the real GitHub MCP tool can run.

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
policies.py:158
compile_and_store_policy_rules()
```

Reads enabled DB policies, compiles them, deletes old stored compiled rules, and inserts fresh rows into `compiled_policy_rules`.

```text
policies.py:145
list_compiled_policy_rules()
```

Reads the currently stored compiled rules.

## What Comes From Where

| Thing | Current Source | Notes |
| --- | --- | --- |
| Runtime input policies | Postgres `policies` table | Loaded by `policy_loader.py`. |
| Runtime blocked tool names | DB policies compiled by `policy_compiler.py` | Used by `tool_guard.py`. |
| Generated blocked test prompts | DB policies compiled by `policy_compiler.py` | Used by `test_nemo_mcp.py`. |
| Allowed test prompts | Postgres `allowed_test_cases` table | Falls back to defaults if DB unavailable/empty. |
| Allowed expected-tool join rows | Postgres `allowed_test_case_expected_tools` table | Seeded/backfilled, but not yet used by `test_case_loader.py`. |
| Output policy objects | Postgres `policies` table | Loadable/compilable now. |
| Normalized app/action/resource metadata | Postgres `apps`, `app_actions`, `app_resources`, `tool_mappings` | Seeded by `scripts/seed_normalized_policy_metadata.py`. |
| Actual NeMo input prompt template | `config/prompts.yml` + DB rules | `prompt_rule_compiler.py` injects `compiled_policy_rules` into the template. |
| Actual NeMo output prompt template | `config/prompts.yml` + DB rules | `prompt_rule_compiler.py` injects `compiled_policy_rules` into the template. |
| Stored compiled rule text | Postgres `compiled_policy_rules` table | Created by `POST /policies/compile-rules`, consumed by `prompt_rule_loader.py`. |

## Current End State In Terminal

When `scripts/test_nemo_mcp.py` runs successfully, the terminal should show:

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
