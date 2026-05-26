# AGENTS.md

## Project Context

This project tests NVIDIA NeMo Guardrails with GitHub MCP and an LLM.

The goal is to build toward a guardrails management system where administrators can configure app-specific policies, such as blocking GitHub write operations, without manually editing backend guardrail code.

## Current Architecture

The test pipeline is:

User prompt
-> deterministic Python pre-check report only
-> NeMo Guardrails input rail using injected AzureChatOpenAI
-> LangChain agent
-> `src/nemo_mcp_guardrails/tool_guard.py` wraps GitHub MCP tools and blocks restricted tool names before execution
-> GitHub MCP tools in read-only Docker mode
-> final model answer

The deterministic Python pre-check is no longer the main enforcement path. It currently reports what it would block for comparison, unless `ENFORCE_PYTHON_PRECHECK=true` is set.

The project now also includes a first policy-object compiler prototype in `src/nemo_mcp_guardrails/policy_compiler.py`. It models an admin-created policy such as `github + create + issue + block`, generates NeMo self-check rule text as a preview, generates a tool denylist preview containing `issue_write`, and generates blocked prompt tests consumed by `scripts/test_nemo_mcp.py`.

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
- GitHub MCP runs in Docker with `GITHUB_READ_ONLY=1`.
- Current input blocking is handled by NeMo `self check input` in `config/prompts.yml`.
- `scripts/test_nemo_mcp.py` manually creates `LLMRails(rails_config, llm=model)` so NeMo uses the same working AzureChatOpenAI model as the LangChain agent.
- Do not switch back to stock `GuardrailsMiddleware(config_path="config")` without testing, because it constructs its own NeMo LLM and previously hit an old OpenAI client path.
- `src/nemo_mcp_guardrails/tool_guard.py` contains the current execution-level MCP tool guard. It is intentionally separate from NeMo input rails.
- `src/nemo_mcp_guardrails/policy_compiler.py` contains the first structured policy-object prototype and currently generates issue-creation tests from adapter-style metadata.
- `scripts/test_nemo_mcp.py` imports generated tests with `compile_policy_test_prompts()`.
- `scripts/debug_nemo_self_check.py` is an isolated diagnostic script for NeMo input rails without GitHub MCP.
- `scripts/debug_tool_guard.py` is an isolated diagnostic script for the MCP tool guard without Docker, GitHub MCP, Azure OpenAI, or real credentials.
- NeMo output rails are still disabled. Output rail testing should be debugged separately after input rails/tool-call rails are stable.
- Do not add a custom `config/policies.yml` yet unless explicitly choosing to prototype the future admin/backend policy store. It is not a standard NeMo Guardrails file.

## When Editing This Project

- Do not add real API keys or PATs to committed files.
- Preserve read-only GitHub MCP mode.
- Keep blocked write-action tests separate from allowed read tests.
- Prefer small incremental tests.
- Add short docstrings to new Python functions/classes.
- Before changing non-doc code, preview the exact diff and wait for user approval.

## Recommended Next Step

Connect compiler-generated blocked tool names into `src/nemo_mcp_guardrails/tool_guard.py`.

The goal is:

```text
src/nemo_mcp_guardrails/policy_compiler.py
-> compiled blocked tool names
-> src/nemo_mcp_guardrails/tool_guard.py
```

Keep static denylist entries for restricted actions that are not yet represented as policy objects, but move `issue_write` to compiler-generated output. Then verify:

- `python src/nemo_mcp_guardrails/policy_compiler.py`
- `python scripts/debug_tool_guard.py`
- `python -m py_compile src/nemo_mcp_guardrails/policy_compiler.py src/nemo_mcp_guardrails/tool_guard.py scripts/test_nemo_mcp.py scripts/debug_tool_guard.py scripts/debug_nemo_self_check.py`
- `python scripts/test_nemo_mcp.py`
