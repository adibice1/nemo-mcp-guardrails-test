# Troubleshooting Notes

## Terminology During Migration

The terminology migration is complete. `apps` represents client applications
consuming the GMS. `connectors` represents GitHub MCP, SharePoint, Outlook, and
other integrations. Check `docs/target-architecture.md` before changing schema
code.

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
prompt_rule_config = build_rails_config_with_prompt_rules("config")
rails_config = prompt_rule_config.rails_config
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

The isolated input/output diagnostic scripts now report expected unsafe
Azure-filtered cases separately from completed NeMo classifications. An Azure
filter block means the request entered the NeMo rail, but Azure rejected the
rail's internal LLM call before NeMo could return its own decision.

What worked:

- Avoid example-heavy prompts containing explicit token-like phrases.
- Use a simple restricted-operation classifier.
- Keep output as `yes` or `no`.

Current parser-compatible convention:

- `yes` means block
- `no` means allow

## NeMo Input Rail Blocks Safe GitHub Reads

If read-only prompts like "list branches" are blocked, inspect the raw self-check response with `scripts/debug_nemo_self_check.py`.

The diagnostic uses `build_rails_config_with_prompt_rules("config")` so it
loads the same DB-injected prompt configuration as the full runner. The latest
home-computer run allowed the safe read-only input and blocked write and
credential inputs through NeMo.

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
- fake token/secret-like assistant output blocks through NeMo or Azure
- NeMo does not use the old `openai.ChatCompletion` path

If Azure returns `content_filter` during output checks, inspect `config/prompts.yml`. The `self_check_output` prompt should only include `{{ bot_response }}`. Do not echo `{{ user_input }}` in the output prompt unless you are deliberately retesting Azure filtering behavior.

Current home-computer result:

```text
safe GitHub summary: passed by NeMo
fake GitHub token: blocked by NeMo output rail
fake environment variable: blocked by NeMo output rail
```

## Policy Compiler / Tool Guard Sanity Checks

If the next machine needs to verify the current policy-object prototype, run:

```powershell
python src/nemo_mcp_guardrails/policy_compiler.py
python scripts/seed_normalized_policy_metadata.py
python tests/test_tool_guard.py
python tests/test_policy_loader.py
python scripts/debug_nemo_output_check.py
python -m py_compile src/nemo_mcp_guardrails/app_auth.py src/nemo_mcp_guardrails/guarded_execution.py src/nemo_mcp_guardrails/runtime_factory.py src/nemo_mcp_guardrails/api/app_schemas.py src/nemo_mcp_guardrails/api/apps.py src/nemo_mcp_guardrails/api/assignment_serializers.py src/nemo_mcp_guardrails/api/auth.py src/nemo_mcp_guardrails/api/runtime.py src/nemo_mcp_guardrails/api/runtime_schemas.py src/nemo_mcp_guardrails/policy_compiler.py src/nemo_mcp_guardrails/policy_rule_service.py src/nemo_mcp_guardrails/tool_guard.py src/nemo_mcp_guardrails/database/models.py src/nemo_mcp_guardrails/database/conversation_store.py src/nemo_mcp_guardrails/database/policy_loader.py src/nemo_mcp_guardrails/database/test_case_loader.py src/nemo_mcp_guardrails/database/prompt_rule_loader.py src/nemo_mcp_guardrails/prompt_rule_compiler.py scripts/seed_normalized_policy_metadata.py tests/test_nemo_mcp.py tests/test_tool_guard.py tests/test_policy_loader.py tests/test_app_policy_scope.py tests/test_app_auth.py tests/test_app_auth_http.py tests/test_policy_auto_compile.py tests/test_guardrails_run_http.py tests/test_runtime_connector_access.py tests/test_app_connector_api.py tests/test_runtime_connector_credentials.py tests/test_runtime_llm_selection.py scripts/debug_nemo_self_check.py scripts/debug_nemo_output_check.py
python tests/test_nemo_mcp.py
```

Expected:

- `src/nemo_mcp_guardrails/policy_compiler.py` prints all default GitHub write input policy objects, a combined generated tool denylist, and generated output rail rules.
- `tests/test_tool_guard.py` reports every DB-derived compiler-generated blocked tool was blocked before execution.
- `tests/test_policy_loader.py` reports enabled Postgres input/output policies and their compiled artifacts.
- `scripts/seed_normalized_policy_metadata.py` reports `connectors: global, github`, `github connector actions: 11`, `github connector resources: 10`, `github connector tool mappings: 33`, and `allowed test expected-tool links: 3`.
- `scripts/debug_nemo_output_check.py` reports output rail checks passed.
- `tests/test_nemo_mcp.py` prints `NeMo prompt policy rules loaded`, `Runtime input policies loaded`, blocks generated DB-policy prompts through NeMo input rails, and prints `NEMO OUTPUT RAIL RESULT` before final responses.

If `tests/test_nemo_mcp.py` passes allowed read prompts but generated policy prompts are not present, check:

- `src/nemo_mcp_guardrails/database/policy_loader.py` can connect to Postgres.
- Enabled input policy rows exist in the `policies` table.
- Rows include `policy_type=input`, `enabled=true`, `connector`, `action`, `resource`, and `effect`.
- `tests/test_nemo_mcp.py` calls `compile_policy_test_prompts(load_input_policy_objects())`.

If the database is unavailable or has no valid enabled input rows, `policy_loader.py` falls back to `DEFAULT_INPUT_POLICY_OBJECTS`.

## Database Tooling Direction

The current database direction is PostgreSQL. For the first local backend prototype, use the Postgres service in `docker-compose.yml`.

pgAdmin is available as a Docker service, and DBeaver can also connect to the same local Postgres database for inspecting policy rows, running manual queries, and debugging FastAPI CRUD behavior.

## IMPORTANT HANDOVER: Home Laptop DBeaver Fatal Password Error

Read this section first when the home laptop reports:

```text
FATAL: password authentication failed
```

The most likely cause is **not DBeaver, VS Code, or an incorrect `.env`
copy/paste**. PostgreSQL stores its initialized password inside the persistent
Docker volume. Updating `.env` afterward does not update that stored password.

DBeaver does not require a VS Code extension and does not automatically read
the project's `.env` file. It connects directly to the Postgres server exposed
by Docker.

The confirmed home-computer cause was a port conflict: a Windows PostgreSQL
service already owns host port `5432`. The project Docker Postgres service
therefore uses host port `5433`.

Use these DBeaver connection settings on the home computer:

```text
Host: localhost
Port: 5433
Database: nemo_mcp_guardrails
Username: nemo_mcp_guardrails
Password: value of POSTGRES_PASSWORD
Authentication: Database Native
```

Use these home-computer `.env` values:

```env
POSTGRES_PORT=5433
DATABASE_URL=postgresql+psycopg://nemo_mcp_guardrails:nemo_mcp_guardrails_dev_password@localhost:5433/nemo_mcp_guardrails
```

Do not change the container's internal Postgres port. Docker maps home host
port `5433` to container port `5432`.

Important Docker/Postgres behavior:

```text
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
```

are only used when the Postgres data volume is first initialized. This project
uses the persistent Docker volume:

```yaml
postgres_data:/var/lib/postgresql/data
```

Changing `.env` later does not automatically change the password stored inside
an existing Postgres volume. Therefore, DBeaver can reject the password even
when the copied `.env` values look correct and the container reports healthy.

Recommended home-computer recovery when no local DB data needs preserving:

```powershell
docker compose down -v
docker compose up -d
docker compose ps
```

Then reconnect DBeaver using the current `.env` values. This is usually the
fastest fix on a newly configured home laptop.

Confirm the Compose service list and runtime port without printing resolved
environment values:

```powershell
docker compose config --services
docker compose ps
```

Expected port mapping:

```text
0.0.0.0:5433->5432/tcp
```

If the home laptop database has no important local data, recreate its volumes:

```powershell
docker compose down -v
docker compose up -d
```

Warning: `docker compose down -v` deletes that laptop's local Postgres and
pgAdmin data. It does not affect another laptop's database.

For a non-destructive password reset:

```powershell
docker compose exec postgres psql -U nemo_mcp_guardrails -d nemo_mcp_guardrails
```

Then inside `psql`:

```sql
\password nemo_mcp_guardrails
```

Set it to the same value as `POSTGRES_PASSWORD`, then exit:

```sql
\q
```

After recreating/resetting the home database, rerun:

```powershell
python scripts/migrate_client_app_foundation.py
python scripts/migrate_connector_terminology.py
python scripts/migrate_app_relationships.py
python scripts/migrate_policy_assignments.py
python scripts/seed_normalized_policy_metadata.py
```

The database and its rows are local to each laptop unless a shared remote
Postgres server is configured.

## Runtime DB Policy Loading

Current runtime input/tool policy flow:

```text
Postgres policies table
-> load_input_policy_objects(app_id=optional_app_id)
-> compile_blocked_tools()
-> tool_guard.py
```

No-app calls preserve the current all-enabled test behavior. App-scoped calls
load enabled global assignments plus enabled assignments for that app.

Inspect both scopes with:

```powershell
python tests/test_policy_loader.py
python tests/test_policy_loader.py --app-id 999999
python tests/test_app_policy_scope.py
python tests/test_app_auth.py
python tests/test_app_auth_http.py
```

`tool_guard.py` preserves a no-app all-enabled compatibility constant, but it
can also compile and apply per-app blocked-tool sets. `POST /v1/guardrails/run`
now passes the authenticated app into blocked-tool compilation while preparing
its context. The next slice applies that set to real connector tools during
guarded execution.

The full runner also accepts testing-only app scope:

```powershell
python tests/test_nemo_mcp.py --app-id 999999
```

This does not enforce app authentication. Although service-level credential
verification now exists, the runner accepts nonexistent IDs for scope-testing
purposes because it does not call the verifier.

Credential verification itself can be checked with:

```powershell
python tests/test_app_auth.py
```

The service verifier rejects wrong keys, unknown client IDs, and unauthorized
apps with the same result. HTTP enforcement can be checked with:

```powershell
python tests/test_app_auth_http.py
```

`GET /v1/guardrails/auth-check` returns the same generic `401` for missing
headers and all invalid credential cases. If Swagger marks the two headers as
optional, that is intentional: the dependency accepts missing values so it can
return the uniform `401` instead of FastAPI returning a distinct `422`.

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

## Normalized Metadata Tables

If `allowed_test_case_expected_tools` is empty, run:

```powershell
python scripts/seed_normalized_policy_metadata.py
```

Expected counts:

```text
connectors 2
connector_actions 11
connector_resources 10
connector_tool_mappings 33
allowed_test_case_expected_tools 3
```

The join table is the preferred runtime source for expected tool names.
`test_case_loader.py` falls back to the old
`allowed_test_cases.expected_tools` text column only when no normalized links
exist for that allowed test.

## ACI Frontend Port 80

The deployed frontend image listens directly on port `80`. ACI should expose
only group port `80`; backend port `8000` stays internal. Do not configure ACI
as if it could map public `80` to frontend `3000`, because ACI does not support
Docker-style port translation.

Expected ACI flow:

```text
http://<aci-fqdn> -> frontend :80
/api/gms/* -> Next.js proxy -> http://127.0.0.1:8000
```

If the ACI URL requires `:3000`, the old frontend image or old container-group
port configuration is still deployed. Confirm the image tag, frontend `PORT`,
and the group public-port list.

If port `80` returns a connection failure, inspect frontend logs for a bind
error. The image keeps the `nextjs` user non-root and grants the Node executable
only `NET_BIND_SERVICE` so it can bind the privileged HTTP port.

For local Compose only, a busy host port `80` can be bypassed with
`FRONTEND_PORT=3000` in `.env`. That produces local mapping `3000:80` without
changing the image or ACI contract.
