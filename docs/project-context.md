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

Backend/database direction:

- FastAPI
- SQLAlchemy
- PostgreSQL
- Postgres in Docker for the first local prototype
- pgAdmin in Docker or DBeaver for database inspection
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
- Runs NeMo `self check output` after the LangChain agent returns a final answer.
- Blocks unsafe write/credential prompts through NeMo input rails.
- Blocks unsafe secret-like assistant responses through NeMo output rails.
- Keeps deterministic Python pre-checks only as a comparison/safety fallback.
- Wraps MCP tools with `src/nemo_mcp_guardrails/tool_guard.py` so restricted tool names can be blocked before execution.
- Uses `src/nemo_mcp_guardrails/policy_compiler.py` to prototype admin-style policy objects and generated policy artifacts.
- Feeds curated policy-generated tests into `scripts/test_nemo_mcp.py`.
- Stores prototype policy rows in local Postgres through FastAPI CRUD endpoints.
- Previews compiler output from enabled database policy rows through `POST /policies/compile-preview`.
- Loads enabled Postgres input policies into runtime code through `src/nemo_mcp_guardrails/database/policy_loader.py`.
- Uses DB-loaded input policies to compile `tool_guard.py` blocked tools and `scripts/test_nemo_mcp.py` generated blocked tests.
- Verifies DB policy loading through `scripts/test_policy_loader.py`.
- Stores compiled NeMo rule text in `compiled_policy_rules`.
- Injects enabled compiled rules into `config/prompts.yml` at runtime through `prompt_rule_compiler.py`.
- Seeds normalized app/action/resource/tool metadata through `scripts/seed_normalized_policy_metadata.py`.
- Backfills `allowed_test_case_expected_tools` from current allowed test rows.

## Current Runtime Flow

```text
User prompt
-> Python pre-check report only
-> compiled_policy_rules are injected into config/prompts.yml template
-> NeMo self_check_input using AzureChatOpenAI injected into LLMRails
-> if blocked: safe refusal and no MCP tool call
-> if passed: LangChain agent
-> src/nemo_mcp_guardrails/tool_guard.py wraps MCP tools and blocks restricted tool names before execution
-> GitHub MCP read-only tools
-> NeMo self_check_output using AzureChatOpenAI injected into LLMRails
-> final answer
```

## Current Policy Compiler Prototype

`src/nemo_mcp_guardrails/policy_compiler.py` contains the structured policy-object prototype.

Example input policy:

```json
{
  "app": "github",
  "action": "create",
  "resource": "issue",
  "effect": "block"
}
```

The compiler uses `InputPolicyObject` for input/tool policies and `OutputPolicyObject` for output policies.

For input policies, it uses adapter-style GitHub metadata:

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
- output self-check rule previews for credential/secret output policies

`compile_policy_test_prompts()` returns one test per policy object by default, so the full test runner stays manageable.

## Adding Policies In The Current Prototype

For runtime policy testing, add enabled policy rows through FastAPI Swagger,
DBeaver, or direct SQL. Edit `src/nemo_mcp_guardrails/policy_compiler.py` only
when adding a new GitHub action/resource/tool mapping or new compiler metadata.

For a new GitHub input/tool policy:

1. Add or reuse an action/resource tool mapping in `GITHUB_WRITE_TOOL_MAPPINGS`.
2. Add action synonyms in `GITHUB_ACTION_SYNONYMS` if the action is new.
3. Add resource synonyms in `GITHUB_RESOURCE_SYNONYMS` if the resource is new.
4. Add an `InputPolicyObject` to `DEFAULT_INPUT_POLICY_OBJECTS`.
5. Add or enable the policy row in Postgres.
6. Run `POST /policies/compile-rules`.
7. Run the compiler, tool guard, and full MCP tests.

Example:

```python
InputPolicyObject(
    app="github",
    action="create",
    resource="issue",
    effect="block",
)
```

For a new output policy, add an enabled output policy row in Postgres, run
`POST /policies/compile-rules`, and verify that the output rule count appears
in `scripts/test_nemo_mcp.py`.

Current important design note:

- `config/prompts.yml` is now a stable template with `{{ input_policy_rules }}` and `{{ output_policy_rules }}` placeholders.
- `prompt_rule_loader.py` loads enabled rows from `compiled_policy_rules`.
- `prompt_rule_compiler.py` injects those rows into the prompt template before `LLMRails` is created.
- The static prompt text remains as context/fallback around the dynamic DB rules.

## Current Safety Layers

```text
config/prompts.yml
-> stable template for NeMo self_check_input

config/prompts.yml
-> stable template for NeMo self_check_output

compiled_policy_rules
-> dynamic input/output rules injected into prompts.yml templates

src/nemo_mcp_guardrails/tool_guard.py
-> blocks DB-derived restricted MCP tool names before execution

GitHub MCP Docker env
-> GITHUB_READ_ONLY=1 prevents write tools from being offered during normal tests
```

Normal full-run GitHub MCP tests should remain read-only. Future write-capable testing should use a separate opt-in harness with a throwaway repository, limited token, and explicit safety flags.

## Important Implementation Detail

NeMo input rails work when the project creates rails like this:

```python
prompt_rule_config = build_rails_config_with_prompt_rules("config")
rails_config = prompt_rule_config.rails_config
rails = LLMRails(rails_config, llm=model)
```

This matters because stock `GuardrailsMiddleware(config_path="config")` constructs its own internal NeMo LLM. In this environment, that path previously tried to use an old OpenAI/LangChain client and failed with `openai.ChatCompletion` / `APIRemovedInV1`.

## Prompt Design Status

`config/prompts.yml` currently defines `self_check_input` and `self_check_output` as yes/no classifiers:

- `no` means the request is allowed
- `yes` means the request asks for a restricted operation and should be blocked

This matches NeMo's default parser, where `yes` maps to unsafe/block and `no` maps to safe/allow.

## Output Rails Status

Output rails are enabled through `config/config.yml`:

```yaml
output:
  flows:
    - self check output
```

`scripts/test_nemo_mcp.py` reads `rails_config.rails.output.flows` and runs `rails.check_async(..., rail_types=[RailType.OUTPUT])` after each final response.

The output self-check prompt only includes the assistant response:

```text
Assistant response:
{{ bot_response }}
```

It intentionally does not echo the user input, because unsafe user prompts containing fake token-like strings can trigger Azure content filtering before NeMo can classify the assistant response.

`scripts/debug_nemo_output_check.py` verifies safe assistant output passes and fake token/environment-variable output blocks.

## Current DB-Backed Runtime State

The first Postgres/FastAPI CRUD slice, compile-preview endpoint, and runtime database policy loader are in place.

```text
Postgres policies
-> policy_loader.py
-> InputPolicyObject / OutputPolicyObject
-> compiler
-> tool_guard.py blocked tool names
-> generated tests in scripts/test_nemo_mcp.py
```

Latest verified enabled input policy sample:

```text
github create issue block -> issue_write
github create pull_request block -> create_pull_request
github merge pull_request block -> merge_pull_request
github update file block -> create_or_update_file
```

Output policies are compiled into `compiled_policy_rules`; enabled output rules
are now injected into the runtime NeMo output prompt by `prompt_rule_compiler.py`.

## Current Normalized Metadata State

The normalized metadata slice has started. The new tables are:

```text
apps
app_actions
app_resources
tool_mappings
allowed_test_case_expected_tools
```

Seed with:

```powershell
python scripts/seed_normalized_policy_metadata.py
```

Latest expected counts:

```text
apps 2
app_actions 11
app_resources 5
tool_mappings 17
allowed_test_case_expected_tools 3
```

## Current Next Step

Add normalized FK/version/condition columns to `policies`, backfill current flat
policy rows to point at `apps`, `app_actions`, and `app_resources`, then update
`policy_loader.py` to prefer normalized joins while keeping flat text columns as
fallback.

Do not remove the flat `policies.app/action/resource` columns yet.
