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

## Current Runtime Flow

```text
User prompt
-> Python pre-check report only
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

For now, new policies are added by editing `src/nemo_mcp_guardrails/policy_compiler.py`.

For a new GitHub input/tool policy:

1. Add or reuse an action/resource tool mapping in `GITHUB_TOOL_MAPPINGS`.
2. Add action synonyms in `GITHUB_ACTION_SYNONYMS` if the action is new.
3. Add resource synonyms in `GITHUB_RESOURCE_SYNONYMS` if the resource is new.
4. Add an `InputPolicyObject` to `DEFAULT_INPUT_POLICY_OBJECTS`.
5. Make sure `config/prompts.yml` still describes the restriction clearly enough for `self_check_input`.
6. Run the compiler, tool guard, and full MCP tests.

Example:

```python
InputPolicyObject(
    app="github",
    action="create",
    resource="issue",
    effect="block",
)
```

For a new output policy, add an `OutputPolicyObject` to `DEFAULT_OUTPUT_POLICY_OBJECTS` and make sure `config/prompts.yml` still describes the output restriction clearly enough for `self_check_output`.

Current important design note:

- `config/prompts.yml` is still manually maintained, which is normal for a NeMo Guardrails project and matches the standard NeMo examples.
- `policy_compiler.py` currently previews rule text and drives tool denylist/test generation, but it does not automatically rewrite `config/prompts.yml`.
- In the future admin/backend version, policy objects stored in Postgres should be used to assemble more dynamic prompt text from templates, so administrators do not need to manually edit guardrail prompt files.

## Current Safety Layers

```text
config/prompts.yml
-> NeMo self_check_input blocks unsafe user intent before the agent runs

config/prompts.yml
-> NeMo self_check_output blocks unsafe assistant output after the agent runs

src/nemo_mcp_guardrails/tool_guard.py
-> blocks DB-derived restricted MCP tool names before execution

GitHub MCP Docker env
-> GITHUB_READ_ONLY=1 prevents write tools from being offered during normal tests
```

Normal full-run GitHub MCP tests should remain read-only. Future write-capable testing should use a separate opt-in harness with a throwaway repository, limited token, and explicit safety flags.

## Important Implementation Detail

NeMo input rails work when the project creates rails like this:

```python
rails_config = RailsConfig.from_path("config")
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

Output policies are loadable for debug/compiler visibility, but actual NeMo output enforcement still comes from `config/prompts.yml` until dynamic prompt assembly is implemented.

## Current Next Step

Commit the current DB-backed milestone, then design the next policy schema for future write-capable systems:

```text
policy types: input / output / tool / argument / workflow
conditions: repo, branch, PR number, file path, allowed sequence, current state
effect: allow / block
priority: explicit conflict resolution
```

Example future policy need: allow merges only in sequence `A -> B -> C`, and block `B -> A -> C` or any other order. That requires tool-argument and workflow-state checks, not only prompt rails or a tool-name denylist.
