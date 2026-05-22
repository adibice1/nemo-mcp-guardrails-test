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
-> GitHub MCP tools in read-only Docker mode
-> final model answer

The deterministic Python pre-check is no longer the main enforcement path. It currently reports what it would block for comparison, unless `ENFORCE_PYTHON_PRECHECK=true` is set.

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
- `test_nemo_mcp.py` manually creates `LLMRails(rails_config, llm=model)` so NeMo uses the same working AzureChatOpenAI model as the LangChain agent.
- Do not switch back to stock `GuardrailsMiddleware(config_path="config")` without testing, because it constructs its own NeMo LLM and previously hit an old OpenAI client path.
- `debug_nemo_self_check.py` is an isolated diagnostic script for NeMo input rails without GitHub MCP.
- NeMo output rails are still disabled. Output rail testing should be debugged separately after input rails/tool-call rails are stable.

## When Editing This Project

- Do not add real API keys or PATs to committed files.
- Preserve read-only GitHub MCP mode.
- Keep blocked write-action tests separate from allowed read tests.
- Prefer small incremental tests.
