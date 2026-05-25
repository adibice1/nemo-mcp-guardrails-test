# Project Context: NeMo Guardrails + GitHub MCP

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

## Current Working Result

The system successfully:

- Connects to GitHub MCP
- Loads MCP tools
- Uses Azure OpenAI to call MCP read tools
- Reads GitHub repositories, branches, and README files
- Runs NeMo `self check input` before the LangChain agent can call MCP tools
- Blocks unsafe write/credential prompts through NeMo input rails
- Keeps deterministic Python pre-checks only as a comparison/safety fallback
- Wraps MCP tools with `tool_guard.py` so restricted tool names can be blocked before execution
- Uses `policy_compiler.py` to prototype admin-style policy objects and generated policy artifacts
- Feeds policy-generated issue-creation test prompts into `test_nemo_mcp.py`

## Current Runtime Flow

```text
User prompt
-> Python pre-check report only
-> NeMo self_check_input using AzureChatOpenAI injected into LLMRails
-> if blocked: safe refusal and no MCP tool call
-> if passed: LangChain agent
-> tool_guard.py wraps MCP tools and blocks restricted tool names before execution
-> GitHub MCP read-only tools
-> final answer
```

## Current Policy Compiler Prototype

`policy_compiler.py` now contains the first structured policy-object prototype.

Current default policy:

```json
{
  "app": "github",
  "action": "create",
  "resource": "issue",
  "effect": "block"
}
```

The compiler uses adapter-style GitHub metadata:

- action synonyms: `create`, `open`, `file`, `submit`, `raise`, `log`
- resource synonyms: `issue`, `bug report`
- tool mapping: `create + issue -> issue_write`
- reusable prompt templates for generated tests

It currently generates:

- NeMo self-check rule text preview
- tool denylist preview containing `issue_write`
- multiple blocked test prompts consumed by `test_nemo_mcp.py`

The generated tests currently include prompt variants such as:

- `Create an issue ...`
- `Open a new bug report ...`
- `File an issue ...`
- `Submit a new bug report ...`
- `Raise an issue ...`
- `Log a new bug report ...`

These generated tests have been verified to be blocked by NeMo input rails in the full GitHub MCP test flow.

## Important Implementation Detail

NeMo input rails work when the project creates rails like this:

```python
rails_config = RailsConfig.from_path("config")
rails = LLMRails(rails_config, llm=model)
```

This matters because stock `GuardrailsMiddleware(config_path="config")` constructs its own internal NeMo LLM. In this environment, that path previously tried to use an old OpenAI/LangChain client and failed with `openai.ChatCompletion` / `APIRemovedInV1`.

## Prompt Design Status

`config/prompts.yml` currently defines `self_check_input` as a yes/no classifier:

- `no` means the request is allowed
- `yes` means the request asks for a restricted operation and should be blocked

This matches NeMo's default parser, where `yes` maps to unsafe/block and `no` maps to safe/allow.

## Known Issues

### NeMo Output Rails

Output rails are disabled for now.

Earlier NeMo output rail attempts caused false blocking because NeMo tried to invoke an old/default OpenAI path. Output rails should be debugged separately after input rails and tool-call rails are stable.

### Tool-Call Guarding

Tool-call guarding now has a first prototype in `tool_guard.py`.

The guard wraps every loaded MCP tool before it is passed to the LangChain agent. If the proposed tool name is in the restricted GitHub write-tool denylist, the wrapper returns a safe refusal instead of calling the underlying MCP tool.

This is intentionally separate from NeMo input rails:

- NeMo input rails check user intent before the agent runs.
- `tool_guard.py` checks actual MCP tool names before execution.
- `GITHUB_READ_ONLY=1` still prevents GitHub MCP write tools from being exposed during normal tests.

This matters because an ambiguous user prompt could still cause an LLM to choose a write-capable tool if such tools are ever available.

The project is not using a custom `policies.yml` file yet because that is not a standard NeMo Guardrails config file. For now, keep NeMo policy text in `config/prompts.yml` and keep the Python execution-level guard in `tool_guard.py`. A future admin/backend policy compiler can generate both prompt-level policy text and tool-call policy rules from a structured policy store, eventually backed by PostgreSQL.

## Current Next Step

The next recommended implementation step is to connect the compiler-generated tool denylist to `tool_guard.py`, so `issue_write` comes from the compiled policy object instead of being manually listed in the guard module.

Keep this incremental:

1. Add a compiler helper that returns blocked tool names from `DEFAULT_POLICY_OBJECTS`.
2. Import that helper in `tool_guard.py`.
3. Preserve the static denylist for other restricted tools while moving `issue_write` to compiler output.
4. Re-run `debug_tool_guard.py`, `policy_compiler.py`, and `test_nemo_mcp.py`.
