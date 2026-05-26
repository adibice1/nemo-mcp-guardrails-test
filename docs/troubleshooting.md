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

## NeMo Output Rail False Blocking

Output rails are disabled for now.

If allowed read requests return:

```text
I cannot provide this response due to content policy.
```

or logs mention the old OpenAI path, treat output rails as not yet fixed. The next planned task is to debug output rails separately in an isolated script before wiring them into the full GitHub MCP runner.

Recommended next script:

```text
scripts/debug_nemo_output_check.py
```

It should inject the same `AzureChatOpenAI` model into `LLMRails`, then verify:

- safe normal assistant output passes
- fake token/secret-like assistant output blocks
- NeMo does not use the old `openai.ChatCompletion` path

## Policy Compiler / Tool Guard Sanity Checks

If the next machine needs to verify the current policy-object prototype, run:

```powershell
python src/nemo_mcp_guardrails/policy_compiler.py
python scripts/debug_tool_guard.py
python -m py_compile src/nemo_mcp_guardrails/policy_compiler.py src/nemo_mcp_guardrails/tool_guard.py scripts/test_nemo_mcp.py scripts/debug_tool_guard.py scripts/debug_nemo_self_check.py
python scripts/test_nemo_mcp.py
```

Expected:

- `src/nemo_mcp_guardrails/policy_compiler.py` prints all default GitHub write-policy objects and a combined generated tool denylist.
- `scripts/debug_tool_guard.py` reports every compiler-generated blocked tool was blocked before execution.
- `scripts/test_nemo_mcp.py` blocks all curated generated write-policy prompts through NeMo input rails.

If `scripts/test_nemo_mcp.py` passes allowed read prompts but generated policy prompts are not present, check that it imports `compile_policy_test_prompts()` from `src/nemo_mcp_guardrails/policy_compiler.py`.

## Database Tooling Direction

The organisation prefers MySQL or Oracle. For the first local backend prototype, use MySQL in Docker unless Oracle is explicitly required.

DBeaver is the recommended local database management tool for inspecting policy rows, running manual queries, and debugging FastAPI CRUD behavior.
