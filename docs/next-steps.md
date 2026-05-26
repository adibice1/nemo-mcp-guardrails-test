# Next Steps

## Current Milestone

The GitHub MCP prototype now has:

- A working NeMo input-rail gate using `self check input`.
- A compiler-driven tool-call guard in `src/nemo_mcp_guardrails/tool_guard.py`.
- A structured policy-object prototype in `src/nemo_mcp_guardrails/policy_compiler.py`.
- Curated generated policy tests consumed by `scripts/test_nemo_mcp.py`.
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

tool_guard.py
-> checks actual MCP tool names before execution

GitHub MCP read-only mode
-> GITHUB_READ_ONLY=1 prevents write tools from being exposed in normal tests
```

The deterministic Python pre-check remains comparison/report-only unless `ENFORCE_PYTHON_PRECHECK=true`.

## Immediate Next Step: Fix Output Rails In Isolation

Before starting the database/API phase, debug NeMo output rails separately.

Do not enable output rails directly in the full GitHub MCP runner first. Earlier output rail attempts caused false blocking and old OpenAI client errors.

Recommended small milestone:

```text
scripts/debug_nemo_output_check.py
-> load config with RailsConfig.from_path("config")
-> inject the same AzureChatOpenAI model into LLMRails
-> test a normal safe assistant response
-> test a fake token/secret-like assistant response
-> verify no APIRemovedInV1 or old openai.ChatCompletion path
-> verify safe output passes and secret-like output blocks
```

After that works, add optional output checking after the LangChain agent response in `scripts/test_nemo_mcp.py`.

## Database/API Phase After Output Rails

After output rails are stable, start the backend foundation.

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
