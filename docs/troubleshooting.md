# Troubleshooting Notes

## Password Copy And Change - 2026-10-09

Copy Password now catches unavailable/denied Clipboard API access, tries a
selection-based fallback, and shows a manual-copy message if neither succeeds.
Refresh the User Management page after updating the frontend. A failed copy
does not dismiss the one-time password popup.

Signed-in admins and developers can use Settings -> Change password. Enter the
current password, a 15-256-character replacement and matching confirmation.
Success returns to Login; use the new password. Password changes and admin
resets invalidate earlier sessions, and tokens from before this backend update
need a fresh login. Forced first-login setup/temporary expiry are still pending.
The feature requires the updated backend's `/management-auth/me/password` route;
a deployed older backend will not gain it from a local frontend change alone.

For online-database access from home, read
[home-online-database.md](home-online-database.md). It separates local Docker
data from the deployed DB, explains the Compose DATABASE_URL override, and
provides both a deployed-API route and direct PostgreSQL/DBeaver instructions.

## Work Computer: Policy Assistant Failed To Fetch - 2026-10-09

The work-computer frontend uses `http://localhost:3000/policies` and calls
`http://127.0.0.1:8000`. During this diagnosis, the API was stopped and the
only running project frontend was on port 3001. The API and frontend were
restarted on 8000 and 3000 using the existing launchers. No source,
environment-file, credential, or database-configuration change was needed.
The configured work database at `127.0.0.1:5432/nemo_mcp_guardrails` was reachable;
do not copy the home computer's port-5433 settings to this machine.

Verify `/health`, `/health/db`, and the frontend page before checking Azure.
The current default CORS origins permit localhost/127.0.0.1 on frontend port
3000. Another frontend port requires an explicit matching origin. Avoid
running two Next.js development servers against the same `.next` directory.

Live Azure drafting succeeded with the existing backend settings. The text
`any issues with the name 'hello'` returned a clarification asking whether
issue creation should be blocked. To request that action explicitly, use
`Block creation of GitHub issues titled 'hello'.` Drafting does not save a
policy or execute GitHub tools.

HTTP health/page checks and the policy-assistant CORS preflight returned 200;
unauthenticated generation returned the expected 401 with the matching CORS
origin. The isolated policy-assistant diagnostic passed. Live generation was
checked directly through the authoring helper; an authenticated browser
generation was not verified because the browser connection tool was unavailable.
Refresh the page and sign in again if the management session has expired.

## AI Output Policy Drafting - 2026-10-09

Select Output in Choose Rail Type before generating a response restriction.
The assistant should show `Output -> Custom resource` and fill Output Rule,
not the input connector/action/resource fields. Input and output draft JSON
must have the matching `policy_type` tag. Restart the API after updating the
backend, and refresh the frontend if an older input-only client is cached.

Live generation requires a management login and the backend's existing
`AZURE_OPENAI_*` settings; it does not require an app API key or the hosted DB.
Output generation does not read GitHub metadata. `/policy-preview` deliberately
stays offline and provides the hello example in Sample mode.

An invalid model response produces a visible error rather than an invented
sample policy. For a word ban, use quoted wording such as
`Do not include the word "hello" in assistant responses.` The existing matcher
ignores casing and does not match hello inside `shelloworld`. Other output
restrictions still require separate runtime evaluation. Generation and applying
a draft do not save a policy; review the form and explicitly choose Create.

## Home Computer: No Local Management Account - 2026-10-09

Management users live in the database selected by the backend's `DATABASE_URL`.
An account in the hosted database is not automatically available in the home
computer's separate PostgreSQL instance. Public signup is intentionally
disabled; creating a local development administrator requires an authorized
database bootstrap or an existing administrator's User Management action.

Before provisioning, confirm the backend points to the intended local database
and the `users` table has the current profile/authentication columns. A local
bootstrap can insert `UserRecord` with email, name, unique username,
`system_role="admin"`, and `enabled=True`, using the existing
`management_auth.hash_password()` helper for `password_hash`. Use a transaction
and reject existing emails/usernames rather than overwriting another account.
Never store a plaintext password in the database or documentation. No SQL
injection, login bypass, or change to authentication code is needed.

The backend also requires a randomly generated `GMS_JWT_SECRET` of at least
32 characters in its environment. Keep it in the ignored local `.env`, never
in committed code or docs. A newly created account alone cannot log in if
the backend cannot sign its management JWT. Restart the backend when needed
after changing local configuration.

On 2026-10-09, one enabled local test administrator was provisioned against
`localhost:5433/nemo_mcp_guardrails` with the application's scrypt helper.
A missing local JWT secret was generated in the ignored `.env`. HTTP login
and authenticated `/management-auth/me` returned 200 and confirmed the admin
role. Existing accounts were not modified and the hosted database was not used.

Use `http://127.0.0.1:3000/login` for the normal local management UI. Its API
URL points to `http://127.0.0.1:8000`, and the default CORS configuration
allows origin `http://127.0.0.1:3000`. The separate port-3100
`/policy-preview` page requires no login; normal login on port 3100 is not
allowed by the current backend CORS configuration. Avoid running multiple
Next.js development servers against the same `.next` directory.

Credentials were delivered separately to the user and are not stored here.

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

When manually testing a containerized backend with
`GITHUB_MCP_READ_ONLY=0`, changing `.env` is not enough for an existing
container. Recreate the backend container because `docker restart` does not
reload `--env-file` values. Use `docker exec <backend-container> printenv
GITHUB_MCP_READ_ONLY` to verify the effective setting before testing a write
tool.

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
