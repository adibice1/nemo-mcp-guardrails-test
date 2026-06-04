# AGENTS.md

## Project Context

This project tests NVIDIA NeMo Guardrails with GitHub MCP and an LLM.

The goal is to build toward a guardrails management system where administrators can configure app-specific policies, such as blocking GitHub write operations, without manually editing backend guardrail code.

## Current Architecture

The test pipeline is:

User prompt
-> deterministic Python pre-check report only
-> DB compiled prompt rules are injected into `config/prompts.yml` templates
-> NeMo Guardrails input rail using injected AzureChatOpenAI
-> LangChain agent
-> `src/nemo_mcp_guardrails/tool_guard.py` wraps GitHub MCP tools and blocks DB-derived restricted tool names before execution
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
- Current input blocking is handled by NeMo `self check input` using `config/prompts.yml` plus enabled DB rules from `compiled_policy_rules`.
- Current output checking is handled by NeMo `self check output` using `config/prompts.yml` plus enabled DB rules from `compiled_policy_rules`.
- `config/config.yml` enables both `self check input` and `self check output`.
- Output self-check prompts intentionally inspect only `{{ bot_response }}` and do not echo `{{ user_input }}`, because unsafe user prompts containing fake token-like text can trigger Azure content filtering before NeMo can classify the assistant output.
- `scripts/test_nemo_mcp.py` manually creates `LLMRails(rails_config, llm=model)` so NeMo uses the same working AzureChatOpenAI model as the LangChain agent.
- Do not switch back to stock `GuardrailsMiddleware(config_path="config")` without testing, because it constructs its own NeMo LLM and previously hit an old OpenAI client path.
- `src/nemo_mcp_guardrails/tool_guard.py` contains the current execution-level MCP tool guard. It is intentionally separate from NeMo input rails and now gets its blocked GitHub tool names from enabled DB input policies through `src/nemo_mcp_guardrails/database/policy_loader.py` and the policy compiler.
- `src/nemo_mcp_guardrails/policy_compiler.py` contains the structured policy-object prototype. It uses `InputPolicyObject` for input/tool policies and `OutputPolicyObject` for output policies. It currently covers GitHub issue, pull request, branch, file, repository, and fork write actions plus credential/secret output checks.
- To add a runtime input policy in the current prototype, add an enabled policy row through the FastAPI CRUD endpoints or DBeaver. Edit `src/nemo_mcp_guardrails/policy_compiler.py` only when adding a new action/resource mapping, synonym, or template that the compiler does not yet understand.
- `config/prompts.yml` is now a stable prompt template. `src/nemo_mcp_guardrails/database/prompt_rule_loader.py` loads enabled rows from `compiled_policy_rules`, and `src/nemo_mcp_guardrails/prompt_rule_compiler.py` injects those rules into the template before `LLMRails` is created.
- `scripts/test_nemo_mcp.py` imports curated generated tests with `compile_policy_test_prompts(load_input_policy_objects())`, so generated blocked tests follow enabled DB input policies.
- `scripts/debug_nemo_self_check.py` is an isolated diagnostic script for NeMo input rails without GitHub MCP.
- `scripts/test_tool_guard.py` is an isolated diagnostic script for the MCP tool guard without Docker, Postgres, GitHub MCP, Azure OpenAI, or real credentials. It forces `NEMO_POLICY_SOURCE=defaults`.
- `scripts/test_policy_loader.py` is an isolated diagnostic script for Postgres policy loading and compilation without Azure OpenAI or GitHub MCP.
- `scripts/debug_nemo_output_check.py` is an isolated diagnostic script for NeMo output rails without GitHub MCP.
- NeMo output rails are now enabled through `config/config.yml` and verified in the full GitHub MCP test runner.
- The database/API phase uses PostgreSQL. Local development starts from `docker-compose.yml`, which runs Postgres and pgAdmin. DBeaver can also connect to the same local Postgres database. The target deployment direction is containerisation and OpenShift.
- FastAPI policy CRUD endpoints live under `/policies`.
- `POST /policies/compile-preview` reads enabled DB policy rows, converts them into `InputPolicyObject` / `OutputPolicyObject`, and returns generated input rules, blocked tools, generated test prompts, and output rules.
- FastAPI allowed-test CRUD endpoints live under `/allowed-test-cases`. These rows are safe prompts that `scripts/test_nemo_mcp.py` should expect to pass; they are not allow/block policies.
- `src/nemo_mcp_guardrails/database/policy_loader.py` provides `load_input_policy_objects()` and `load_output_policy_objects()`. Input policies affect runtime tool guarding. Output policies can be compiled and stored in `compiled_policy_rules`; those stored output rules are now injected into the NeMo output prompt by `prompt_rule_compiler.py`.
- `src/nemo_mcp_guardrails/database/test_case_loader.py` loads enabled DB allowed test cases for `scripts/test_nemo_mcp.py`, falling back to the three default read tests if no enabled DB rows exist.
- Normal full-run GitHub MCP tests should keep `GITHUB_READ_ONLY=1`. Future write-capable testing should be a separate opt-in harness with a throwaway repo and limited token.
- Do not add a custom `config/policies.yml` yet unless explicitly choosing to prototype the future admin/backend policy store. It is not a standard NeMo Guardrails file.

## When Editing This Project

- Do not add real API keys or PATs to committed files.
- Preserve read-only GitHub MCP mode.
- Keep blocked write-action tests separate from allowed read tests.
- Prefer small incremental tests.
- Add short docstrings to new Python functions/classes.
- Before changing non-doc code, preview the exact diff and wait for user approval.

## Recommended Next Step

The current guardrail milestone is green, and the Postgres/FastAPI CRUD, compile-preview, and runtime DB policy loading slices are in place. Continue with commit plus schema design:

```text
commit current DB-backed milestone
-> design policy schema extensions for tool arguments, conditions, workflow state, and priority
-> keep normal GitHub MCP tests read-only
-> refine DB prompt-rule lifecycle and admin UX
```

Future write-tool use cases, such as allowing PR merges only in sequence `A -> B -> C`, require argument and workflow-state checks. A simple tool-name denylist is not enough for that class of policy.

Useful verification commands for the current state:

- `python src/nemo_mcp_guardrails/policy_compiler.py`
- `python scripts/test_tool_guard.py`
- `python scripts/test_policy_loader.py`
- `python scripts/debug_nemo_output_check.py`
- `python scripts/run_api.py`
- `python -m py_compile src/nemo_mcp_guardrails/policy_compiler.py src/nemo_mcp_guardrails/tool_guard.py src/nemo_mcp_guardrails/database/policy_loader.py src/nemo_mcp_guardrails/database/test_case_loader.py src/nemo_mcp_guardrails/database/prompt_rule_loader.py src/nemo_mcp_guardrails/prompt_rule_compiler.py scripts/test_nemo_mcp.py scripts/test_tool_guard.py scripts/test_policy_loader.py scripts/debug_nemo_self_check.py scripts/debug_nemo_output_check.py`
- `python scripts/test_nemo_mcp.py`
