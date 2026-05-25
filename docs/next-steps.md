# Next Steps

## Current Milestone

The GitHub MCP prototype now has a working NeMo input-rail gate, a tool-call guard prototype, compact test output, and a first structured policy-object compiler.

Current successful flow:

```text
User prompt
-> deterministic Python pre-check reports what it would block
-> NeMo self_check_input using injected AzureChatOpenAI
-> if blocked: safe refusal, no MCP tool call
-> if passed: LangChain agent runs
-> tool_guard.py checks MCP tool names before execution
-> GitHub MCP read-only tools may be called
-> final answer
```

The key implementation choice is that `test_nemo_mcp.py` does not use stock `GuardrailsMiddleware`. Instead, it manually creates:

```python
rails_config = RailsConfig.from_path("config")
rails = LLMRails(rails_config, llm=model)
```

This avoids NeMo constructing an old OpenAI client internally.

## Completed: Reduced Test Output Noise

`test_nemo_mcp.py` now defaults to compact output instead of printing full LangChain message traces and full GitHub MCP tool payloads.

Verbose mode is controlled with:

```text
VERBOSE_TRACE=true
```

Default compact output shows:

- Test name
- Python pre-check would-block/allow result
- NeMo input rail status
- Tool names called
- Final response

Verbose output keeps the full message trace.

## Completed: Tool-Call Guard Prototype

Input rails are useful but not sufficient for the final product. The project now has a first tool-call guard prototype in `tool_guard.py`.

Current behavior:

```text
Before executing any MCP tool call, inspect the proposed tool name and arguments.
If the tool is restricted, block it before execution.
```

Why:

- A user prompt may be ambiguous.
- The LLM may choose a write tool even if the input was not obviously unsafe.
- Future MCP toolsets may include write tools if read-only mode is disabled for testing.

The initial GitHub tool-call denylist includes:

- `issue_write`
- `add_issue_comment`
- `create_pull_request`
- `update_pull_request`
- `merge_pull_request`
- `pull_request_review_write`
- `create_branch`
- `create_or_update_file`
- `delete_file`
- `push_files`
- `create_repository`
- `fork_repository` if policy forbids repo creation/forking

`debug_tool_guard.py` verifies the guard without Docker, GitHub MCP, Azure OpenAI, or real credentials.

## Completed: Policy Object Compiler Prototype

The project has started moving from hand-written policy prompts and Python denylist rules toward structured policy objects.

Example structured policy:

```json
{
  "app": "github",
  "action": "create",
  "resource": "issue",
  "effect": "block"
}
```

Implemented in `policy_compiler.py`.

Current compiler output:

- NeMo self-check policy text preview
- Tool-call denylist preview containing `issue_write`
- Generated blocked test cases consumed by `test_nemo_mcp.py`

The compiler uses GitHub adapter-style metadata:

- action synonyms: `create`, `open`, `file`, `submit`, `raise`, `log`
- resource synonyms: `issue`, `bug report`
- tool mapping: `create + issue -> issue_write`
- reusable test prompt templates

The generated issue-creation tests are verified in the full `test_nemo_mcp.py` run.

Do not add a custom `config/policies.yml` yet unless the project explicitly decides to prototype the future admin/backend policy store. `policies.yml` is not a standard NeMo Guardrails file. For now, keep NeMo input policy in `config/prompts.yml` and execution-level guard logic in `tool_guard.py`.

## Immediate Next Step: Connect Compiler Output To Tool Guard

`tool_guard.py` still has a static denylist that includes `issue_write`.

Next implementation goal:

```text
policy_compiler.py
-> compiled blocked tool names
-> tool_guard.py
```

Recommended small change:

1. Add a helper in `policy_compiler.py`, for example `compile_blocked_tools()`, that returns blocked tool names from `DEFAULT_POLICY_OBJECTS`.
2. In `tool_guard.py`, keep a static denylist for policy not yet represented as objects, but remove `issue_write` from that static set.
3. Combine the static denylist with compiler-generated blocked tools.
4. Verify `debug_tool_guard.py` still blocks `issue_write`.
5. Verify `test_nemo_mcp.py` still passes.

This proves the policy object can drive both generated tests and execution-level tool blocking.

Do not connect compiler output directly into `config/prompts.yml` yet. Keep generated NeMo prompt text as preview output until the compiler structure is more stable.

## Output Rails Later

Do not prioritize NeMo output rails yet.

Output rails previously hit old OpenAI client/configuration problems and caused false blocking. Revisit them after:

1. Input rails remain stable.
2. Tool-call guarding works.
3. The test output is easier to read.

## Recommended Work Order

1. Connect compiler-generated blocked tool names into `tool_guard.py`.
2. Keep static guard entries for policy areas not yet represented by policy objects.
3. Add one more GitHub policy object only after the first generated-tool path is verified.
4. Later, generate a NeMo self-check prompt section or preview file from policy objects.
5. Keep the generated/manual boundary explicit while this is still a research prototype.
6. Only then revisit output rails.

## Files To Read First On Another Machine

Start with:

- `AGENTS.md`
- `docs/project-context.md`
- `docs/testing-notes.md`
- `docs/troubleshooting.md`
- `docs/next-steps.md`
- `test_nemo_mcp.py`
- `policy_compiler.py`
- `tool_guard.py`
- `debug_tool_guard.py`
- `debug_nemo_self_check.py`
- `config/prompts.yml`
- `config/config.yml`
