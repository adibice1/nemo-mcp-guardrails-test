# Next Steps

## Current Milestone

The GitHub MCP prototype now has a working NeMo input-rail gate.

Current successful flow:

```text
User prompt
-> NeMo self_check_input using injected AzureChatOpenAI
-> if blocked: safe refusal, no MCP tool call
-> if passed: LangChain agent runs
-> GitHub MCP read-only tools may be called
-> final answer
```

The key implementation choice is that `test_nemo_mcp.py` does not use stock `GuardrailsMiddleware`. Instead, it manually creates:

```python
rails_config = RailsConfig.from_path("config")
rails = LLMRails(rails_config, llm=model)
```

This avoids NeMo constructing an old OpenAI client internally.

## Immediate Next Step: Reduce Test Output Noise

`test_nemo_mcp.py` currently prints full LangChain message traces and full GitHub MCP tool payloads.

Add a compact/verbose mode:

```text
VERBOSE_TRACE=false
```

Default compact output should show:

- Test name
- Python pre-check would-block/allow result
- NeMo input rail status
- Tool names called
- Final response

Verbose output should keep the current full message trace.

## Next Safety Step: Tool-Call Guarding

Input rails are useful but not sufficient for the final product.

Next major feature:

```text
Before executing any MCP tool call, inspect the proposed tool name and arguments.
If the tool is restricted, block it before execution.
```

Why:

- A user prompt may be ambiguous.
- The LLM may choose a write tool even if the input was not obviously unsafe.
- Future MCP toolsets may include write tools if read-only mode is disabled for testing.

Initial GitHub tool-call denylist should include:

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

## Next Architecture Step: Policy Object Prototype

Start moving from hand-written policy prompts toward structured policy objects.

Example structured policy:

```json
{
  "app": "github",
  "action": "create",
  "resource": "issue",
  "effect": "block"
}
```

Prototype compiler output:

- Input self-check policy text in `config/prompts.yml`
- Tool-call denylist entry for `issue_write`
- Refusal message
- Test case

Keep this small at first. One policy object, one generated prompt section, one tool-call rule.

## Output Rails Later

Do not prioritize NeMo output rails yet.

Output rails previously hit old OpenAI client/configuration problems and caused false blocking. Revisit them after:

1. Input rails remain stable.
2. Tool-call guarding works.
3. The test output is easier to read.

## Recommended Work Order

1. Add compact/verbose trace mode to `test_nemo_mcp.py`.
2. Rename the fake token test from `Output rail: fake GitHub token` to `Input rail: fake token request`.
3. Add tool-call guard prototype around GitHub MCP tool execution.
4. Add tests proving restricted tool calls are blocked even if input rail passes.
5. Prototype a structured GitHub policy object and a tiny compiler.
6. Only then revisit output rails.

## Files To Read First On Another Machine

Start with:

- `AGENTS.md`
- `docs/project-context.md`
- `docs/testing-notes.md`
- `docs/troubleshooting.md`
- `docs/next-steps.md`
- `test_nemo_mcp.py`
- `debug_nemo_self_check.py`
- `config/prompts.yml`
- `config/config.yml`
