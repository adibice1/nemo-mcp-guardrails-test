# LLM Provider Guide

Updated for the provider-neutral integration on 2026-10-20 against API schemas, model/grant
validation, runtime factory, policy assistant and frontend routes. This guide
separates supported configuration changes from provider development. It does
not certify that an arbitrary deployment works without a live acceptance test.

For commands and exact UI entries, follow the
[Claude and Ollama walkthroughs](model-switch-walkthroughs.md).

For every provider/engine named in NVIDIA's supported-model page, use the
[complete supported-provider setup guide](supported-llm-setup-guide.md).

## What Can Be Switched Today

| Intended change | Current support | Required action |
| --- | --- | --- |
| Another Azure OpenAI deployment for the main agent | Implemented | Provision approved endpoint/key metadata, grant the app main access, then update its main selection |
| Another Azure OpenAI deployment for NeMo input/output rails | Implemented | Independently provision/grant guardrail access and have a system admin update the guardrail selection |
| Environment-default Azure deployment | Implemented | Explicit default grant for each selected purpose; backend environment changes require restart |
| Local/hosted models exposing standard Chat Completions | Compatible adapter implemented | Approve a base URL and explicit credential reference, grant the profile and test role capabilities |
| Native vendor APIs (for example Claude, Gemini, Bedrock) | Via a separately deployed compatible gateway | Configure a supported upstream adapter/model at the gateway; GMS selects an approved compatible profile |
| Policy-authoring AI in Create Policy | Azure defaults or an independent compatible profile | Backend GMS_POLICY_AI_* settings; independently of app model selections |

The provider field selects the API protocol. azure/azure_openai use the existing
AzureChatOpenAI adapter. openai_compatible uses ChatOpenAI with an approved base
URL and explicit credential reference, directly or through a model gateway.
A native vendor URL alone does not translate its protocol. Model-specific tool,
classification and JSON behavior must be tested; support is not universal across
every model or feature. See [gateway setup](model-gateway-integration.md).

## The Three Model Roles

| Role | Selected by | Who can change it |
| --- | --- | --- |
| Main agent: chooses tools and generates the response | apps.main_llm_config_id | System admin or linked app developer, from that app's approved main choices |
| Guardrail classifier: NeMo input and output checks | apps.guardrail_llm_config_id | System admin, from that app's approved guardrail choices |
| Policy authoring: drafts policies through /policy-assistant/suggest | Backend GMS_POLICY_AI_* compatible profile, or AZURE_OPENAI_* defaults | Backend operator |

The runtime sequence is input rail -> main agent -> guarded tools -> output
rail. Input and output rails share the selected guardrail model; separate
input/output model selectors are not implemented. The same configuration may
serve both runtime roles, but it needs a separate enabled grant for each role.

Changing an app's main/guardrail configuration does not switch the policy AI.
Changing backend Azure defaults can affect an Azure-configured policy AI and runtime selections
that use those defaults. The authoring endpoint uses management authentication,
not app API keys or app/purpose model grants.

## Before Switching An Azure Runtime Model

1. Use the intended backend and database with the current schema, including
   app_llm_grants. Check the [current handoff](work-computer-handoff.md) before
   any migration; rehearsal and production rollout states are different.
2. Have a normal management JWT for API calls. A setup-only password JWT cannot
   perform these management operations. Configuration/grant provisioning needs
   a system administrator. Linked developers may select only their app's main
   model; they cannot approve grants or change the guardrail selection.
3. Identify the existing app's numeric id and client_id through GET /apps.
   Preserve its current model IDs/grants for rollback. For a new app, an admin
   first creates it without named model selections; this creates no model grants.
4. For a real /v1/guardrails/run test, the app must be authorized, have enabled
   GitHub connector access and valid backend connector credentials, and have
   enforceable global/app policies and current compiled rules. Full runtime is
   database-backed even if the proposed model is local.
5. Confirm that the candidate Azure deployment supports its assigned role.
   The main model needs LangChain tool calling; the classifier must follow NeMo's
   yes/no prompts reliably. Runtime construction currently sets temperature=0.
   A deployment incompatible with these parameters needs a code adaptation;
   passing provider validation does not prove model compatibility.

The app detail page now mounts a Models tab. Administrators create profiles,
approve/revoke app/purpose access and select main/guardrail models. Linked
developers may select approved main models only. Profile creation grants no
access. The API instructions below remain useful for automation and handover.

## Backend Environment And Approval Rules

If either runtime role selects Azure or its environment default, the existing
Azure path still requires all four settings (including named Azure configurations):

- AZURE_OPENAI_API_KEY
- AZURE_OPENAI_ENDPOINT
- AZURE_OPENAI_API_VERSION
- AZURE_OPENAI_DEPLOYMENT

When both runtime roles use compatible profiles, none of those Azure settings
is required. Each compatible profile instead requires its own approved base URL
and explicit credential reference.

A named Azure model can override endpoint, deployment and credential reference, but
there is no per-configuration API-version field. AZURE_OPENAI_API_VERSION is
shared by all runtime Azure clients. Keep these valid defaults configured.
The GitHub runtime additionally resolves its enabled connector's PAT.

Additional endpoints and credential names need independent backend approval.
Example backend configuration, using placeholders only:

```env
GMS_ALLOWED_LLM_ENDPOINTS=https://second-resource.openai.azure.com
GMS_ALLOWED_LLM_CREDENTIAL_ENV_VARS=APP_A_AZURE_KEY
APP_A_AZURE_KEY=replace-privately-with-the-real-key
```

Merge these names/origins with any existing lists; do not replace unrelated
approved entries. Inject real values privately into the backend environment.
Use the ignored root .env for direct local execution or the deployment's secret
environment mechanism for containers. Do not put keys in frontend configuration.
Restart the backend after environment, endpoint approval or credential changes;
for containers, recreate/redeploy with the new environment, not just restart an
existing container whose environment is unchanged.

Azure endpoint approval requires an exact HTTPS origin with no credentials, path
other than /, query or fragment. Scheme/host/default port are normalized;
non-default ports remain significant. No wildcard/suffix matching is supported.
AZURE_OPENAI_ENDPOINT is automatically approved. Runtime Azure clients refuse
redirects. Compatible base URLs use the separate exact
GMS_ALLOWED_COMPATIBLE_LLM_ENDPOINTS list, including the protocol path; see the
gateway setup for local HTTP restrictions.

Credentials must be references such as env:APP_A_AZURE_KEY. The exact variable
name must be approved in GMS_ALLOWED_LLM_CREDENTIAL_ENV_VARS;
AZURE_OPENAI_API_KEY is automatically approved. Raw LLM keys and vault: references
are not supported configuration values. Provisioning validates references
without resolving their secret values. Malformed approval lists fail closed.

| Named Azure configuration value | Runtime behavior |
| --- | --- |
| model_name | Azure deployment name, not necessarily the underlying model-family name |
| endpoint omitted/null | Backend AZURE_OPENAI_ENDPOINT |
| credential_reference omitted/null/blank | Backend AZURE_OPENAI_API_KEY |
| api version | Backend AZURE_OPENAI_API_VERSION; cannot be overridden in a row |

Granting a named configuration explicitly approves its bundled fallbacks too.
It does not grant the separate null/default selection. Backend default changes
therefore need operator review of affected configurations and grants.

## Switch An Existing App To Another Azure Deployment

Use a system-admin management JWT for this provisioning example. All management
requests below use Authorization: Bearer <management-token>. Select the correct
API base: http://127.0.0.1:8000 for a direct local backend, or the deployed
frontend origin plus /api/gms for its same-origin proxy. Backend port 8000 is
private in the ACI design. Local Swagger is http://127.0.0.1:8000/docs.
These are instructions for deliberately authorized changes, not dry-run requests.

### 1. Create Or Reuse A Named Configuration

After the backend approvals/restart above, call POST /llm-configs:

```json
{
  "name": "App A alternate Azure deployment",
  "provider": "azure_openai",
  "model_name": "your-actual-azure-deployment-name",
  "endpoint": "https://second-resource.openai.azure.com",
  "credential_reference": "env:APP_A_AZURE_KEY",
  "enabled": true
}
```

Keep the returned configuration id as CONFIG_ID. For an existing configuration,
a system admin can find its id with GET /llm-configs. Responses omit credential
references/values. Configuration list/create are implemented; update/delete APIs
are not. Provision a new configuration if the stored bundle must change.

### 2. Grant Each Intended Purpose

For the existing numeric APP_ID, call
PUT /apps/{app_id}/llm-grants/main/{config_ref}, replacing app_id with APP_ID and
config_ref with CONFIG_ID. The body must explicitly be:

```json
{"enabled": true}
```

To use this configuration for guardrails as well, separately call
PUT /apps/{app_id}/llm-grants/guardrail/{config_ref} with the same body.
One main grant never authorizes guardrail use, or vice versa. Creating a
configuration or selecting a model does not create grants automatically.

Inspect grants with GET /apps/{app_id}/llm-grants. Read usable choices with
GET /apps/{app_id}/llm-options?purpose=main or purpose=guardrail. These options
require app access; the global catalogue requires a system admin. Grant/option
routes also exist under /apps/by-client-id/{client_id}.

### 3. Select The Model On The App

Call PUT /apps/{app_id}. For example, if the returned CONFIG_ID is 42:

```json
{"main_llm_config_id": 42}
```

A system admin may independently select the guardrail configuration:

```json
{"guardrail_llm_config_id": 42}
```

Use the actual returned id, not the example 42. A system admin can submit both
fields in one update if both grants exist. Send only fields you intend to change.
Linked developers must omit guardrail_llm_config_id and authorized, even if the
values would be unchanged. Every explicitly submitted model field is validated,
including unchanged IDs and null; omitted selections remain untouched. The
client-ID alias does not provide a general app-metadata PUT route.

Both currently selected purposes need valid grants before /run can execute.
Changing only main does not repair a missing/revoked guardrail grant.

### 4. Verify And Roll Back If Needed

Read GET /apps/{app_id}, the grants and the purpose-specific options to confirm
the stored selections. /v1/guardrails/auth-check verifies app identity only;
it does not verify model access, availability or quality.

For /v1/guardrails/run, use the existing app client_id in X-App-ID and its
existing app API key in X-API-Key. These differ from the management JWT and the
Azure model key. Example read-only request body:

```json
{
  "message": "Use GitHub MCP to list branches in octocat/Hello-World.",
  "conversation_id": "model-switch-check-unique-1"
}
```

Use a fresh conversation ID per independent acceptance case and keep
GITHUB_MCP_READ_ONLY=1. Confirm actual read-tool invocation and results, input /
output decisions and controlled failures. Add matching/nonmatching cases for
the app's real policies. A plausible answer without a tool call is not proof
of agent tool compatibility. Do not test writes as part of this model check.
The runtime response is not a provider-reported model-identity certificate;
verify the Azure deployment mapping/provider telemetry when required.

App selections/grants are checked before cache reuse; database changes do not
need a restart merely to wait out the TTL. Environment/secret-value changes do
require restart. Already-admitted requests can finish on their prior snapshot.

For rollback, restore the previous model IDs through PUT /apps/{app_id}, provided
their grants are still valid. A previous null selection needs its explicit
default grant. Do not rotate app keys or rewrite policies to switch models.
Revoke unwanted grants separately: admin PUT with enabled=false or DELETE
/apps/{app_id}/llm-grants/{purpose}/{config_ref}. DELETE retains a disabled row;
it does not change the app's selected model. Requests using a revoked selection
then fail until an admin approves or replaces it. Bootstrap manifests never
re-enable an existing disabled grant.

## Select Or Change Environment Defaults

To select the backend Azure default, first grant main/default or
guardrail/default using the same grant PUT route and enabled=true body. Then
set the corresponding app selection explicitly to null. For example:

```json
{"main_llm_config_id": null}
```

New apps and null fields do not receive implicit default grants. To change the
underlying default deployment, update the appropriate backend AZURE_OPENAI_*
settings privately and restart/redeploy. Review all apps/configurations using
fallbacks and the policy-authoring model, rather than treating this as an
app-only change.

## Switch Through A Compatible API Or Model Gateway

Follow the complete [gateway configuration and profile workflow](model-gateway-integration.md).
It includes direct compatible endpoints, native-provider translation, local
addresses, the independent policy-authoring role and gateway access controls.
The GMS adapter uses the already-pinned langchain-openai dependency; installing
every native provider package in GMS is unnecessary for this gateway approach.

A compatible profile uses the existing management API:

~~~json
{
  "name": "Reviewed main model v1",
  "provider": "openai_compatible",
  "model_name": "main-v1",
  "endpoint": "https://llm-gateway.example.com/v1",
  "credential_reference": "env:GMS_MODEL_GATEWAY_KEY",
  "enabled": true
}
~~~

Approve the exact base URL and credential environment name on the backend first.
Then grant this profile to the required app/purpose and select it using the same
grant/update sequence as the Azure example. Blank endpoints/credentials are
rejected for compatible profiles. Model names may be versioned gateway aliases;
keep their upstream mappings fixed to preserve the meaning of app grants.

A main-agent model must support a tool-call/tool-result round trip. A guardrail
model must return a complete yes/no decision for both rails; the compatible
adapter rejects explanatory, empty, refused or truncated classifications. A
policy-authoring model must satisfy the existing JSON/draft validation. A
reachable endpoint or successful chat probe establishes none of these by itself.

A native API without a compatible surface still needs a gateway/provider adapter.
Changing only a URL cannot supply different authentication/model identifiers or
make an unsupported model implement tool calling. Profiles make those changes
configuration work, subject to role acceptance tests.

## Verification And Troubleshooting

Run safe offline model-related checks from the repository root:

```powershell
.\.venv\Scripts\python.exe -B scripts/run_security_checks.py --test test_model_gateway --test test_runtime_llm_selection --test test_app_llm_grants_http --test test_runtime_llm_grants --test test_llm_endpoint_security --test test_output_classifier_fail_closed
```

The runner strips inherited credentials, disables dotenv, uses disposable
fixtures and blocks external sockets. These checks cover construction, grants,
permissions, cache revocation, endpoint/credential controls and failure handling;
they do not contact a real model or prove model quality. For the full offline
catalogue use the same runner without --test.

Live database/MCP/model diagnostics remain explicit opt-in work. In particular,
test_guardrails_run_http.py uses the configured database and temporary records;
it is not a database-free model test. Use reviewed rehearsal/disposable targets,
not production, for those diagnostics. No schema migration should be inferred
from the offline verification command.

| Result | Check |
| --- | --- |
| 422 creating a configuration with provider=ollama or another unknown protocol | Use azure/azure_openai or openai_compatible; native vendor names belong in the gateway adapter configuration |
| 400 creating a model configuration | Endpoint/key-name approval, endpoint syntax, nonblank name/deployment or invalid env reference |
| 409 creating a configuration | Name already exists; inspect admin catalogue before creating another |
| 403 selecting a model | App/purpose grant and management role; even explicit null/unchanged choices need approval |
| 503 during runtime setup | Both grants/configs, approved endpoint/key, Azure defaults when selected, compatible metadata, connector and policy state; inspect the controlled error category |
| Model request fails after setup succeeds | Azure deployment/API version, temperature/tool compatibility, provider access, content filtering or connectivity |

## Pre-Integration Handover Evidence And Limits

The initial Azure-only guide audit (before the gateway proposal) checked api/app_schemas.py, api/llm_configs.py,
api/app_llm_grants.py, api/apps.py, llm_access.py, llm_security.py,
llm_credentials.py, runtime_factory.py, api/policy_assistant.py and the frontend
app route/imports. Executable request examples and documented route names are
checked separately against the actual request schemas and router definitions.
Validation passed for all six JSON request examples against their actual
Pydantic schemas, 15 documented method/path definitions against source routers,
and all five named offline checks against the explicit runner catalogue. The
example endpoint/key-name approvals also passed the current validators, and
the unsupported-provider example was rejected. These checks disabled dotenv
and external sockets and did not execute the live HTTP switching sequence.
The offline suite passed earlier in this home session; the user also reported
four model/security checks passing. Live alternate-Azure switching and arbitrary
new provider compatibility are not certified by those results.

The user downloaded qwen3:4b and generated text through local Ollama on
2026-10-20. ollama ps reported 3.2 GB, 100% CPU and context 4096. Its exact READY
probe did not satisfy the requested output despite think=false and a 32-token
budget. This establishes local inference only; it does not establish reliable
classification, tool calling, NeMo integration or GMS provider support. The
response metadata needed to attribute the exact-output failure was not supplied.

## Integration Verification Scope

The exact provider-neutral patch was approved and applied on 2026-10-20 after
baseline/patch fingerprint verification. The applied source passed the complete
offline runner: 33 passed, 0 failed. The gateway check exercises real protocol
clients with synthetic HTTP transports, API/RBAC, grant/cache revocation, real
agent/tool and NeMo rail behavior, malformed/truncated classifiers and independent
authoring. It does not call a real provider or connect to PostgreSQL.

Whole-project TypeScript, changed-file legacy ESLint 8 lint, Python syntax and
whitespace checks passed. Home dependencies differ from committed pins; current
source ESLint 9, clean pinned-install/image checks, browser interactions and actual
upstream-model tests remain open. No .env, database, gateway or deployment changed.
For the live setup sequence see [the integration guide](model-gateway-integration.md).
