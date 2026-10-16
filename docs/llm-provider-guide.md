# LLM Provider Guide

This guide explains how an application developer selects an LLM for a GMS
application and how maintainers add support for a new provider.

## App Grant Management - 2026-10-15

Patches 008a/008b/008c are applied in source: grant storage/tooling,
admin-managed grants, app-scoped options, management selection checks and live
runtime enforcement. Both model purposes are checked on every runtime build
request, including warm-cache hits and requests with caching disabled. The
unmounted selector uses app-scoped options. Offline checks passed; PostgreSQL,
browser and deployment verification remain open in the
[backlog](open-work-backlog.md#008-app-specific-modelcredential-grants).
No live migration ran. Before rollout, administrators must review existing
named/default selections and approve grants for both purposes. Missing grants
produce a controlled runtime 503.

## Policy Authoring Model - 2026-10-09

Live input/output policy drafting through `/policy-assistant/suggest` uses the
backend `AZURE_OPENAI_*` environment deployment, not the selected app's main or
guardrail LLM configuration. Credentials remain server-side. The management
JWT authorizes drafting; an app API key is not used. Tagged JSON validation
rejects the wrong rail and unknown fields. Output drafting is independent of
GitHub metadata and does not run a classifier or connector. A dedicated
authoring-model selector/provider extension remains future work; see
`open-work-backlog.md` and `frontend-api-map.md`.

## Runtime Model

Each GMS application can select two independent models:

- **Main Agent LLM:** interprets the user request, selects connector tools, and
  produces the response. Linked app developers select only app-approved choices.
- **Guardrail LLM:** runs NeMo input and output policy classifications. Only a
  GMS administrator should select this model.

```text
Client application
-> GMS input rails using the guardrail LLM
-> LangChain agent using the main-agent LLM
-> guarded connector tools
-> GMS output rails using the guardrail LLM
-> client application
```

The client application's GMS API key only authenticates calls to
`POST /v1/guardrails/run`. It does not configure or authenticate an LLM.
Model endpoints and credentials must be available to the GMS backend.

## Current Support

The runtime currently supports:

- Azure OpenAI using provider `azure` or `azure_openai`.
- A separate Azure deployment for the main agent and guardrail classifier.
- Backend credential references in the form `env:VARIABLE_NAME`.
- Environment-default Azure settings when an app has no selected configuration
  and has an explicit default grant for that model purpose.
- Administrator-only configuration creation and backend-approved HTTPS origins.

## Credential Destination Controls - 2026-10-15

`GET /llm-configs` and `POST /llm-configs` require a system administrator.
Developers use `/apps/{app_id}/llm-options?purpose=main` or `purpose=guardrail`
for their linked app's readable choices; equivalent client-ID aliases exist.
Only administrators can change guardrail selections. Every explicitly supplied
selection needs an enabled grant for that app and purpose, including null and
unchanged values. Missing or unavailable choices get generic 403 responses;
grant-store failures get generic 503 responses. Omitted selections are untouched.
The app LLM settings component is currently not mounted by an application route;
use the management API for provisioning and assignment until it is connected.
Its adapter now loads separate app-scoped main/guardrail options and disables
saving unavailable choices. Creating a configuration does not grant app access.

The `AZURE_OPENAI_ENDPOINT` origin is automatically approved. Additional model
origins require a comma-separated backend setting, for example:

```env
GMS_ALLOWED_LLM_ENDPOINTS=https://second-resource.openai.azure.com
```

Origins must use HTTPS with no embedded credentials, path other than `/`, query,
or fragment. Matching uses the exact normalized origin, including a non-default
port; wildcard and hostname-suffix matching are unsupported. Both synchronous
and asynchronous runtime model clients refuse HTTP redirects.

Creation rejects invalid or unapproved endpoints with HTTP 400. Runtime checks
also cover existing stored configurations before resolving their selected
credential references; rejected endpoints produce a controlled HTTP 503.
A malformed backend allowlist fails closed. Restart the backend after changing
endpoint approval or credentials. Endpoint approval needs no schema change;
the separate grant table and reviewed grants are required for runtime rollout.

Credential references also require backend name approval through
`GMS_ALLOWED_LLM_CREDENTIAL_ENV_VARS`, a comma-separated list of exact environment
names. `AZURE_OPENAI_API_KEY` is automatically approved. No wildcard matching is
supported. Invalid/unapproved references return 400 at creation, and malformed
backend approval settings fail closed even for the default. Provisioning and
grant validation do not resolve credential values. Backend operators remain
trusted to approve appropriate names. Runtime resolution validates legacy
references before reading their values. Unapproved references or missing keys,
including the default key, produce a generic setup 503. Endpoint and credential
approval are checked alongside the app's purpose-specific grant.

The runtime does not yet execute Ollama, Gemini, Anthropic, or generic
OpenAI-compatible configurations. `runtime_factory.py` deliberately rejects
these providers until their adapters and tests are implemented.

## Select Another Azure Deployment

### 1. Provision the credential

Add the deployment key to the GMS backend environment, not the frontend:

```env
APP_A_AZURE_KEY=replace-with-the-real-key
```

Restart the backend after changing its environment. For deployed containers,
configure the variable through the deployment platform rather than committing
it to `.env`.
Add the exact name `APP_A_AZURE_KEY` to
`GMS_ALLOWED_LLM_CREDENTIAL_ENV_VARS` before using that reference. Approving a
variable name does not grant any app a model.

### 2. Create the configuration

As a system administrator, call `POST /llm-configs` with the following metadata
after approving its endpoint in the backend environment:

```text
Configuration Name: App A GPT-4o
Deployment Name: the Azure deployment name
Azure Endpoint: https://<resource>.openai.azure.com
Credential Environment Variable: APP_A_AZURE_KEY
```

Use `credential_reference: "env:APP_A_AZURE_KEY"`; send the reference, never the key.

### 3. Assign it

Create the app without named model selections first; non-null initial selections
return 400. As a system administrator, approve its model using
`PUT /apps/{app_id}/llm-grants/main/{config_id}` with an explicit boolean
`enabled` decision. Guardrail approval uses purpose `guardrail` independently.
The same operations exist under `/apps/by-client-id/{client_id}`. Only an
explicit admin operation can create or re-enable a grant.

Update the app through `PUT /apps/{app_id}` with `main_llm_config_id`.
Administrators may independently set `guardrail_llm_config_id`.

Selecting **Environment default** uses `AZURE_OPENAI_DEPLOYMENT`,
`AZURE_OPENAI_ENDPOINT`, and `AZURE_OPENAI_API_KEY`; explicit null selections
require a grant with config reference `default` for the corresponding purpose.
New apps receive no automatic grants, including default grants.

Read grants through `GET /apps/{app_id}/llm-grants`. Admin PUT can enable/disable;
DELETE at the same purpose/config route revokes by retaining a disabled row.
It does not change the app's selection. Ordinary metadata edits remain allowed
while a revoked selection awaits repair. Bootstrap manifests never re-enable
an existing disabled grant. Runtime requests recheck grants even with a warm
cache; requests already admitted may finish after concurrent revocation.

### 4. Verify it

Run an app Runtime Test and confirm:

- Input, tool guard, and output stages complete.
- The selected model can perform required tool calls.
- Existing input and output policies still block expected test prompts.

## Add A Local Or Non-Azure Provider

Adding a provider is a backend feature, not only a configuration change.
The repository already installs `langchain-ollama` and
`langchain-google-genai`, but runtime construction is still Azure-only.

Implement the provider in these locations:

1. `runtime_factory.py`: import its LangChain chat adapter and add a provider
   branch to `build_chat_model()`.
2. Change the model return type from `AzureChatOpenAI` to LangChain's common
   chat-model interface.
3. Require Azure environment values only when an Azure model is selected.
4. `app_schemas.py`: add the provider to the accepted provider values and
   validate its required endpoint and credential reference.
5. `create-llm-config-modal.tsx`: add a provider selector and provider-specific
   field labels.
6. `api-client.ts`: extend the provider payload type.
7. `test_runtime_llm_selection.py`: test model construction, missing settings,
   disabled configurations, and unsupported providers.
8. `llm_access.py`: extend approved provider validation and add app grant/option
   coverage without weakening purpose-specific access or credential approval.

Example Ollama metadata after the adapter is implemented:

```json
{
  "name": "Local Llama",
  "provider": "ollama",
  "model_name": "llama3.1:8b",
  "endpoint": "http://host.docker.internal:11434",
  "credential_reference": null,
  "enabled": true
}
```

Use `http://127.0.0.1:11434` when the backend runs directly on the same host.
From a Docker container, use a container-reachable hostname such as
`host.docker.internal`. In an Azure Container Instances group, a model sidecar
can be reached through `http://127.0.0.1:<port>`.

## Provider Requirements

Before enabling a model, confirm that:

- Main-agent models support the tool-calling behavior required by LangChain.
- Guardrail models reliably follow NeMo's classification prompts.
- Runtime Azure endpoints satisfy the backend origin approval described above.
- API keys remain in backend environment variables or a production secrets
  manager and never enter the database or browser.
- Requests use timeouts and do not expose the local model port publicly.
- Input, output, and tool-guard tests pass before production assignment.

After changing a provider implementation, run:

```powershell
.\.venv\Scripts\python.exe tests\test_runtime_llm_selection.py
.\.venv\Scripts\python.exe tests\test_guardrails_run_http.py
```

Then restart the backend and perform one authenticated Runtime Test.
