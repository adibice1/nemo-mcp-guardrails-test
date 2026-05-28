# Next Steps

## Current Milestone

The GitHub MCP prototype now has:

- A working NeMo input-rail gate using `self check input`.
- A compiler-driven tool-call guard in `src/nemo_mcp_guardrails/tool_guard.py`.
- A structured policy-object prototype in `src/nemo_mcp_guardrails/policy_compiler.py`.
- Curated generated policy tests consumed by `scripts/test_nemo_mcp.py`.
- A config-driven NeMo output rail using `self check output`.
- An isolated output-rail diagnostic script in `scripts/debug_nemo_output_check.py`.
- Compact test output by default, with verbose LangChain traces controlled by `VERBOSE_TRACE=true`.

Current successful flow:

```text
User prompt
-> deterministic Python pre-check reports what it would block
-> NeMo self_check_input using injected AzureChatOpenAI
-> if blocked: safe refusal, no MCP tool call
-> if passed: LangChain agent runs
-> src/nemo_mcp_guardrails/tool_guard.py checks MCP tool names before execution
-> GitHub MCP read-only tools may be called
-> NeMo self_check_output checks the final assistant response
-> final answer
```

The key implementation choice is that `scripts/test_nemo_mcp.py` does not use stock `GuardrailsMiddleware`. Instead, it manually creates:

```python
rails_config = RailsConfig.from_path("config")
rails = LLMRails(rails_config, llm=model)
```

This avoids NeMo constructing an old OpenAI client internally.

## Completed: Repository Structure Cleanup

Project code has been moved out of the repository root.

Current layout:

```text
config/                              NeMo Guardrails config
docs/                                handoff and architecture docs
scripts/                             runnable debug/test scripts
src/nemo_mcp_guardrails/             application/library code
src/nemo_mcp_guardrails/database/    future database code location
src/nemo_mcp_guardrails/helper/      helper package
logs/                                local logs
```

Run scripts from the repository root, for example:

```powershell
python scripts/test_nemo_mcp.py
python scripts/debug_tool_guard.py
python src/nemo_mcp_guardrails/policy_compiler.py
```

## Completed: Compiler-Driven Tool Guard

The static GitHub write-tool denylist has been moved into policy objects.

`src/nemo_mcp_guardrails/policy_compiler.py` now maps policy objects to blocked MCP tools for:

- Creating/updating/commenting on issues
- Creating/updating/merging/reviewing pull requests
- Creating branches
- Creating/updating/deleting/pushing files
- Creating repositories
- Forking repositories

`src/nemo_mcp_guardrails/tool_guard.py` now uses:

```python
BLOCKED_GITHUB_MCP_TOOLS = STATIC_BLOCKED_GITHUB_MCP_TOOLS | compile_blocked_tools()
```

`STATIC_BLOCKED_GITHUB_MCP_TOOLS` is currently an empty reserved hook for emergency/manual blocks.

`scripts/debug_tool_guard.py` verifies every compiler-generated blocked tool is intercepted before execution.

## Adding A Policy Today

Until the database/API phase exists, add policies in `src/nemo_mcp_guardrails/policy_compiler.py`.

For GitHub input/tool policies:

```text
GITHUB_TOOL_MAPPINGS
-> GITHUB_ACTION_SYNONYMS, if needed
-> GITHUB_RESOURCE_SYNONYMS, if needed
-> DEFAULT_INPUT_POLICY_OBJECTS
-> config/prompts.yml, if the self-check prompt needs clearer wording
-> run verification commands
```

For output policies:

```text
DEFAULT_OUTPUT_POLICY_OBJECTS
-> config/prompts.yml, if the self-check output prompt needs clearer wording
-> scripts/debug_nemo_output_check.py
-> run verification commands
```

Side note: hardcoded prompt text in `config/prompts.yml` is correct for the current NeMo prototype and matches the standard NeMo Guardrails style. The compiler does not yet rewrite prompt files. The future admin/backend phase should move toward dynamic prompt text assembled from stored policy objects and templates.

## Completed: Curated Policy Tests

`compile_policy_test_prompts()` now returns one generated test per policy object by default.

The full MCP test runner currently includes:

- 3 allowed GitHub read tests
- 14 generated GitHub write-policy tests
- 2 credential/token tests

Latest observed full run:

- Allowed read tests passed and called only read tools.
- All 14 generated policy tests were blocked by NeMo input rails.
- Credential/token tests were blocked by NeMo input rails.
- The previous ambiguous `review pull request` generated test was changed to `approve pull request`, which now blocks correctly.

## Current Safety Layers

```text
NeMo input rail
-> checks prompt-level user intent through config/prompts.yml

NeMo output rail
-> checks final assistant responses through config/prompts.yml

tool_guard.py
-> checks actual MCP tool names before execution

GitHub MCP read-only mode
-> GITHUB_READ_ONLY=1 prevents write tools from being exposed in normal tests
```

The deterministic Python pre-check remains comparison/report-only unless `ENFORCE_PYTHON_PRECHECK=true`.

## Completed: Output Rails

Output rails are now enabled in `config/config.yml`:

```yaml
output:
  flows:
    - self check output
```

`scripts/test_nemo_mcp.py` reads that config and runs a NeMo output checkpoint after the LangChain agent produces a final answer. For input-blocked requests, it runs the output checkpoint against the safe refusal text.

The output self-check prompt in `config/prompts.yml` intentionally checks only `{{ bot_response }}`. It does not include `{{ user_input }}`, because unsafe user prompts containing fake token-like strings can trigger Azure content filtering before NeMo can classify the assistant response.

Verification:

```text
scripts/debug_nemo_output_check.py
-> safe normal assistant output passes
-> fake token/secret-like assistant output blocks
-> no old OpenAI client path is used
```

The full `scripts/test_nemo_mcp.py` run now prints `Output rail enabled via config/config.yml.` and includes `NEMO OUTPUT RAIL RESULT` before each final response.

## Immediate Next Step: Database/API Phase

Start the backend foundation.

Supervisor guidance:

- Use MySQL or Oracle because those align with the organisation.
- Prefer MySQL first for local Docker prototyping unless Oracle is explicitly required immediately.
- Use DBeaver for database inspection and manual debugging.
- Plan for containerisation and later OpenShift deployment.

Recommended database/API path:

```text
MySQL Docker container
-> DBeaver connection
-> FastAPI app skeleton
-> SQLAlchemy policy model
-> policy CRUD endpoints
-> compiler loads active DB policies
```

Initial API endpoints:

```text
GET    /health
POST   /policies
GET    /policies
GET    /policies/{policy_id}
PATCH  /policies/{policy_id}
DELETE /policies/{policy_id}
POST   /policies/compile-preview
```

Keep the DB schema portable enough that Oracle support remains realistic later.

## Files To Read First On Another Machine

Start with:

- `AGENTS.md`
- `docs/project-context.md`
- `docs/testing-notes.md`
- `docs/troubleshooting.md`
- `docs/next-steps.md`
- `scripts/test_nemo_mcp.py`
- `src/nemo_mcp_guardrails/policy_compiler.py`
- `src/nemo_mcp_guardrails/tool_guard.py`
- `scripts/debug_tool_guard.py`
- `scripts/debug_nemo_self_check.py`
- `config/prompts.yml`
- `config/config.yml`
