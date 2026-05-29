# Troubleshooting Notes

## GitHub Push Protection

If GitHub blocks push with `GH013` and says an Azure OpenAI key was found, remove the secret from commits.

Recommended:
1. Rotate the exposed Azure key.
2. Run `git reset --soft origin/main`.
3. Remove real keys from committed files.
4. Store real keys only in `.env`.
5. Commit `.env.example` instead.

## Azure OpenAI Key Handling

Use `.env`:

```env
AZURE_OPENAI_API_KEY=...
OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_VERSION=...
AZURE_OPENAI_DEPLOYMENT=...
GITHUB_PERSONAL_ACCESS_TOKEN=...
```

`OPENAI_API_KEY` is included because some NeMo/LangChain internals still expect it.

## GitHub MCP Connection Closed

If MCP says `Connection closed`, check:

- Docker is running
- `GITHUB_PERSONAL_ACCESS_TOKEN` exists in `.env`
- The PAT starts with `github_pat_` or `ghp_`
- The PAT is valid
- The Docker image `ghcr.io/github/github-mcp-server` can run

## NeMo Old OpenAI Client Error

If NeMo rails fail with:

```text
openai.ChatCompletion is no longer supported
APIRemovedInV1
```

or:

```text
AttributeError: 'NoneType' object has no attribute 'create'
```

then NeMo is likely constructing its own internal LLM through an old OpenAI/LangChain path.

Current workaround:

```python
model = AzureChatOpenAI(...)
rails_config = RailsConfig.from_path("config")
rails = LLMRails(rails_config, llm=model)
```

Avoid relying on stock `GuardrailsMiddleware(config_path="config")` until this path is retested, because it creates `LLMRails(config)` internally without the injected Azure model.

## Azure Content Filter on Self-Check Prompt

If Azure returns:

```text
BadRequestError
code: content_filter
jailbreak: detected=True
```

then the self-check prompt may look too much like a jailbreak or policy-bypass prompt to Azure.

What worked:

- Avoid example-heavy prompts containing explicit token-like phrases.
- Use a simple restricted-operation classifier.
- Keep output as `yes` or `no`.

Current parser-compatible convention:

- `yes` means block
- `no` means allow

## NeMo Input Rail Blocks Safe GitHub Reads

If read-only prompts like "list branches" are blocked, inspect the raw self-check response with `scripts/debug_nemo_self_check.py`.

Expected for read-only prompt:

```text
RAW SELF-CHECK RESPONSE:
no

PARSED SELF-CHECK RESULT:
[True]
```

Expected for write/credential prompt:

```text
RAW SELF-CHECK RESPONSE:
yes

PARSED SELF-CHECK RESULT:
[False]
```

If a safe prompt returns `yes`, revise `config/prompts.yml`.

## NeMo Output Rail Issues

Output rails are enabled in `config/config.yml`:

```yaml
output:
  flows:
    - self check output
```

If allowed read requests return:

```text
I cannot provide this response due to content policy.
```

or logs mention the old OpenAI path, debug output rails separately before changing the full GitHub MCP runner.

Use:

```text
scripts/debug_nemo_output_check.py
```

It injects the same `AzureChatOpenAI` model into `LLMRails`, then verifies:

- safe normal assistant output passes
- fake token/secret-like assistant output blocks
- NeMo does not use the old `openai.ChatCompletion` path

If Azure returns `content_filter` during output checks, inspect `config/prompts.yml`. The `self_check_output` prompt should only include `{{ bot_response }}`. Do not echo `{{ user_input }}` in the output prompt unless you are deliberately retesting Azure filtering behavior.

## Policy Compiler / Tool Guard Sanity Checks

If the next machine needs to verify the current policy-object prototype, run:

```powershell
python src/nemo_mcp_guardrails/policy_compiler.py
python scripts/debug_tool_guard.py
python scripts/debug_nemo_output_check.py
python -m py_compile src/nemo_mcp_guardrails/policy_compiler.py src/nemo_mcp_guardrails/tool_guard.py scripts/test_nemo_mcp.py scripts/debug_tool_guard.py scripts/debug_nemo_self_check.py scripts/debug_nemo_output_check.py
python scripts/test_nemo_mcp.py
```

Expected:

- `src/nemo_mcp_guardrails/policy_compiler.py` prints all default GitHub write input policy objects, a combined generated tool denylist, and generated output rail rules.
- `scripts/debug_tool_guard.py` reports every DB-derived compiler-generated blocked tool was blocked before execution.
- `scripts/debug_nemo_output_check.py` reports output rail checks passed.
- `scripts/test_nemo_mcp.py` prints `Runtime input policies loaded`, blocks generated DB-policy prompts through NeMo input rails, and prints `NEMO OUTPUT RAIL RESULT` before final responses.

If `scripts/test_nemo_mcp.py` passes allowed read prompts but generated policy prompts are not present, check:

- `src/nemo_mcp_guardrails/database/policy_loader.py` can connect to Postgres.
- Enabled input policy rows exist in the `policies` table.
- Rows include `policy_type=input`, `enabled=true`, `app`, `action`, `resource`, and `effect`.
- `scripts/test_nemo_mcp.py` calls `compile_policy_test_prompts(load_input_policy_objects())`.

If the database is unavailable or has no valid enabled input rows, `policy_loader.py` falls back to `DEFAULT_INPUT_POLICY_OBJECTS`.

## Database Tooling Direction

The current database direction is PostgreSQL. For the first local backend prototype, use the Postgres service in `docker-compose.yml`.

pgAdmin is available as a Docker service, and DBeaver can also connect to the same local Postgres database for inspecting policy rows, running manual queries, and debugging FastAPI CRUD behavior.

## Runtime DB Policy Loading

Current runtime input/tool policy flow:

```text
Postgres policies table
-> load_input_policy_objects()
-> compile_blocked_tools()
-> tool_guard.py
```

To inspect what runtime code sees:

```powershell
$env:PYTHONPATH="src"; @'
from nemo_mcp_guardrails.database.policy_loader import load_input_policy_objects
from nemo_mcp_guardrails.policy_compiler import compile_blocked_tools

policies = load_input_policy_objects()
for policy in policies:
    print(policy)

print(sorted(compile_blocked_tools(policies)))
'@ | .\.venv\Scripts\python.exe -
```

Normal full-run GitHub MCP tests should keep `GITHUB_READ_ONLY=1`. Do not switch the default test runner to write mode. Future write-capable tests should be separate, opt-in, and use a throwaway repo plus a limited token.
