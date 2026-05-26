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

Planned backend/database direction:

- FastAPI
- SQLAlchemy
- MySQL or Oracle, based on organisation preference
- MySQL in Docker for the first local prototype unless Oracle is required immediately
- DBeaver for database inspection
- Later containerisation/OpenShift deployment

## Current Repository Layout

```text
config/                              NeMo Guardrails config
docs/                                handoff and architecture docs
scripts/                             runnable debug/test scripts
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
- Blocks unsafe write/credential prompts through NeMo input rails.
- Keeps deterministic Python pre-checks only as a comparison/safety fallback.
- Wraps MCP tools with `src/nemo_mcp_guardrails/tool_guard.py` so restricted tool names can be blocked before execution.
- Uses `src/nemo_mcp_guardrails/policy_compiler.py` to prototype admin-style policy objects and generated policy artifacts.
- Feeds curated policy-generated tests into `scripts/test_nemo_mcp.py`.

## Current Runtime Flow

```text
User prompt
-> Python pre-check report only
-> NeMo self_check_input using AzureChatOpenAI injected into LLMRails
-> if blocked: safe refusal and no MCP tool call
-> if passed: LangChain agent
-> src/nemo_mcp_guardrails/tool_guard.py wraps MCP tools and blocks restricted tool names before execution
-> GitHub MCP read-only tools
-> final answer
```

## Current Policy Compiler Prototype

`src/nemo_mcp_guardrails/policy_compiler.py` contains the structured policy-object prototype.

Example policy:

```json
{
  "app": "github",
  "action": "create",
  "resource": "issue",
  "effect": "block"
}
```

The compiler uses adapter-style GitHub metadata:

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
- curated blocked test prompts consumed by `scripts/test_nemo_mcp.py`

`compile_policy_test_prompts()` returns one test per policy object by default, so the full test runner stays manageable.

## Current Safety Layers

```text
config/prompts.yml
-> NeMo self_check_input blocks unsafe user intent before the agent runs

src/nemo_mcp_guardrails/tool_guard.py
-> blocks restricted MCP tool names before execution

GitHub MCP Docker env
-> GITHUB_READ_ONLY=1 prevents write tools from being offered during normal tests
```

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

## Output Rails Status

Output rails are disabled for now.

Earlier NeMo output rail attempts caused false blocking because NeMo tried to invoke an old/default OpenAI path. The next recommended implementation step is to debug output rails in an isolated script before enabling them in `scripts/test_nemo_mcp.py`.

Recommended next output-rail script:

```text
scripts/debug_nemo_output_check.py
```

It should:

- Inject the same `AzureChatOpenAI` model into `LLMRails`.
- Test a normal safe assistant response.
- Test a fake token/secret-like assistant response.
- Verify safe output passes.
- Verify secret-like output blocks.
- Verify no old OpenAI client path is used.

## Current Next Step

Fix NeMo output rails in isolation.

After that, move into the MySQL/FastAPI foundation:

```text
MySQL Docker container
-> DBeaver connection
-> FastAPI app skeleton
-> SQLAlchemy policy model
-> policy CRUD endpoints
-> compiler loads active DB policies
```
