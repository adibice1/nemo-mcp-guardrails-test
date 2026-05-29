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
-> NeMo Guardrails output rail using injected AzureChatOpenAI
-> final model answer

The deterministic Python pre-check is no longer the main enforcement path. It currently reports what it would block for comparison, unless `ENFORCE_PYTHON_PRECHECK=true` is set.

The project now also includes a policy-object compiler prototype in `src/nemo_mcp_guardrails/policy_compiler.py`. It models admin-created input policies such as `github + create + issue + block`, generates NeMo self-check rule text as a preview, generates blocked MCP tool names for `src/nemo_mcp_guardrails/tool_guard.py`, generates curated blocked prompt tests consumed by `scripts/test_nemo_mcp.py`, and previews output-policy rule text.

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
- Current output checking is handled by NeMo `self check output` in `config/prompts.yml`.
- `config/config.yml` enables both `self check input` and `self check output`.
- Output self-check prompts intentionally inspect only `{{ bot_response }}` and do not echo `{{ user_input }}`, because unsafe user prompts containing fake token-like text can trigger Azure content filtering before NeMo can classify the assistant output.
- `scripts/test_nemo_mcp.py` manually creates `LLMRails(rails_config, llm=model)` so NeMo uses the same working AzureChatOpenAI model as the LangChain agent.
- Do not switch back to stock `GuardrailsMiddleware(config_path="config")` without testing, because it constructs its own NeMo LLM and previously hit an old OpenAI client path.
- `src/nemo_mcp_guardrails/tool_guard.py` contains the current execution-level MCP tool guard. It is intentionally separate from NeMo input rails and now gets its blocked GitHub tool names from the policy compiler.
- `src/nemo_mcp_guardrails/policy_compiler.py` contains the structured policy-object prototype. It uses `InputPolicyObject` for input/tool policies and `OutputPolicyObject` for output policies. It currently covers GitHub issue, pull request, branch, file, repository, and fork write actions plus credential/secret output checks.
- To add a new policy in the current prototype, edit `src/nemo_mcp_guardrails/policy_compiler.py` mappings/synonyms/default policy objects and update `config/prompts.yml` manually if the NeMo self-check wording needs to change. Hardcoded prompt text is correct for now; later database/API work should move toward dynamic prompt text assembled from stored policy objects and templates.
- `scripts/test_nemo_mcp.py` imports curated generated tests with `compile_policy_test_prompts()`, one test per policy object by default.
- `scripts/debug_nemo_self_check.py` is an isolated diagnostic script for NeMo input rails without GitHub MCP.
- `scripts/debug_tool_guard.py` is an isolated diagnostic script for the MCP tool guard without Docker, GitHub MCP, Azure OpenAI, or real credentials.
- `scripts/debug_nemo_output_check.py` is an isolated diagnostic script for NeMo output rails without GitHub MCP.
- NeMo output rails are now enabled through `config/config.yml` and verified in the full GitHub MCP test runner.
- The later database/API phase should use PostgreSQL. Local development now starts from `docker-compose.yml`, which runs Postgres and pgAdmin. DBeaver can also connect to the same local Postgres database. The target deployment direction is containerisation and OpenShift.
- Do not add a custom `config/policies.yml` yet unless explicitly choosing to prototype the future admin/backend policy store. It is not a standard NeMo Guardrails file.

## When Editing This Project

- Do not add real API keys or PATs to committed files.
- Preserve read-only GitHub MCP mode.
- Keep blocked write-action tests separate from allowed read tests.
- Prefer small incremental tests.
- Add short docstrings to new Python functions/classes.
- Before changing non-doc code, preview the exact diff and wait for user approval.

## Recommended Next Step

The current guardrail milestone is green, and the first Postgres/FastAPI CRUD slice is in place. Continue with compiler integration:

```text
POST /policies/compile-preview
-> convert DB policy rows into InputPolicyObject / OutputPolicyObject
-> compiler loads active policies from the database
-> generated policy previews return through the API
```

Useful verification commands for the current state:

- `python src/nemo_mcp_guardrails/policy_compiler.py`
- `python scripts/debug_tool_guard.py`
- `python scripts/debug_nemo_output_check.py`
- `python scripts/run_api.py`
- `python -m py_compile src/nemo_mcp_guardrails/policy_compiler.py src/nemo_mcp_guardrails/tool_guard.py scripts/test_nemo_mcp.py scripts/debug_tool_guard.py scripts/debug_nemo_self_check.py scripts/debug_nemo_output_check.py`
- `python scripts/test_nemo_mcp.py`
