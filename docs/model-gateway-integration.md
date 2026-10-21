# Provider-Neutral Model Integration


Current form/API instructions were reconciled with the applied source on
22 October 2026. All 11 JSON examples across the model guides validate against
the current schemas; app-owned Azure registration and a real guarded native-MCP
read pass in the final clean image. This does not certify every provider recipe.
See [the final home results](home-verification-results-2026-10-22.md).

Status: source integration applied on 2026-10-20 after the user approved the exact
26-file patch with "ok". Both direct Azure and approved compatible API profiles
are implemented. No gateway, image, database, upstream subscription or production
service was created by this work. Gateway configuration and live model acceptance
remain deployment/testing follow-ups.

For every provider/engine named in NVIDIA's supported-model page, use the
[complete supported-provider setup guide](supported-llm-setup-guide.md).

## Current registration form and API contracts - 22 October 2026

Both roles use Models -> Add model profile, with API Type first. The action is
at the right of Save model selections. API Type selects Azure OpenAI versus a
Compatible API / Model Gateway; credential storage is a separate choice.

| Path | Who can use it | Credential field | API | Access after creation |
| --- | --- | --- | --- | --- |
| Default app-owned main profile | Linked app developer or admin | Provider API key (actual value, masked) | POST /apps/{app_id}/main-models or its by-client-id alias | Automatic main-only grant for this app; select/save separately |
| Advanced backend-managed profile | System admin | Credential Environment Variable (NAME only) | POST /llm-configs | No automatic grant; explicitly approve main or classifier access |

For the admin path, expand Advanced credentials and check Use a backend-managed
credential. The default app-owned path is the same for admins and developers;
owned profiles cannot become classifiers, including when an admin creates them.
Developers cannot see advanced credentials, edit classifier selection or manage
grants. The form submit button is Add model profile in both modes.

Default app-owned creation uses a management JWT and this strict payload:

~~~json
{
  "name": "App main model v1",
  "provider": "openai_compatible",
  "model_name": "your-tested-model-or-alias",
  "endpoint": "https://provider.example/v1",
  "api_key": "replace_privately_with_provider_key"
}
~~~

Allowed provider values for this route are azure_openai and openai_compatible.
Azure model_name is the deployment name and endpoint is the resource origin;
compatible endpoint is the exact approved API base URL including its path. Do
not include credential_reference, enabled or owner_app_id in this request. The
response omits the key and ciphertext. Its main-purpose grant is atomic with
creation; use the returned ID in PUT /apps/{app_id} with main_llm_config_id to
activate it. Registration does not select the model automatically.

Backend destination approvals still apply. App-owned storage also needs the
additive database schema and a private GMS_MODEL_CREDENTIAL_ENCRYPTION_KEY.
Keep the encryption key; do not regenerate it on restart or model switches.
Back it up separately from the database. Raw provider keys belong only in the
masked form/app-owned request, never in Git, URLs or frontend dotenv settings.
A deliberately unauthenticated local server can use a non-secret placeholder.
The app-owned request does not need an environment credential reference/name.

The admin-managed route below still uses credential_reference=env:VARIABLE_NAME,
with an approved backend variable and explicit app/purpose grants. This is the
path for classifiers. Vault references/native secret-manager adapters are not
implemented. Both paths preserve the current runtime Azure defaults/API-version
requirements whenever an Azure role is selected. Policy authoring remains a
separate backend profile.

For a runtime request, X-App-ID is the app client ID and X-API-Key is the GMS app
API key, not the provider key or management JWT. Keep existing app keys when
switching models. Use a fresh conversation ID per independent test: reusing one
loads stored messages even if the request sends an empty conversation_history.
Green policy rail badges do not certify factual correctness or tool execution;
inspect actual tool events and compare the returned result with the answer.

For the complete field-by-field workflow, see
[Common Steps C](supported-llm-setup-guide.md#common-steps-c-register-approve-and-select-the-profile).

## Requested Outcome

The project should switch model providers through approved configuration rather
than new Python code for every vendor. GMS uses a standard text chat/tool API;
a gateway translates that API for supported upstream providers. A model still
needs the capabilities required by its selected role. An embedding-only model,
a text model without tool support, or a classifier that cannot return complete
yes/no decisions cannot fulfill every GMS role merely because it is reachable.

The architecture is:

    GMS main agent / NeMo classifier / policy authoring
        -> approved compatible API endpoint + model profile + explicit credential
        -> optional external model gateway
        -> configured upstream provider/model

The existing direct Azure adapter remains available. Direct compatible model
servers can use the same new protocol path without a gateway. Native APIs that
do not implement this contract need a gateway adapter; unsupported/custom APIs
still require an adapter at that boundary.

LiteLLM is the proposed gateway because its documented provider catalogue covers
many hosted and local services. This integration does not embed its SDK or server in
the GMS backend or add its dependency tree to requirements.txt. The gateway is a
separately reviewed/deployed service. Its exact release, image digest, provider
credentials, network access and supported upstream model IDs must be verified by
the deployment team. Adding it to ACI topology is a separate deployment decision.

## Implemented Behavior

- Add provider=openai_compatible to the existing llm_configs API/schema. Existing
  database columns are sufficient; this patch adds no migration.
- Use ChatOpenAI from the already-pinned langchain-openai package with explicit
  base_url/model/key, Chat Completions mode, a 60-second request timeout and no
  SDK retries. Keep Azure's existing construction and defaults.
- When both runtime choices are compatible profiles, Azure environment settings
  are unnecessary. A mixed/default Azure selection retains existing Azure setup
  requirements. Model construction stops rewriting OPENAI_API_KEY globally.
- Admin-managed compatible profiles require an explicit env: credential reference.
  App-owned main profiles instead use their encrypted submitted key. Blank
  credentials do not fall back to Azure; credential-name approval applies to the
  environment-reference mode and destination approval applies to both modes.
- Use a separate GMS_ALLOWED_COMPATIBLE_LLM_ENDPOINTS list of exact base URLs,
  including their paths. Remote services require HTTPS; explicitly listed HTTP
  endpoints may use only literal 127.0.0.1 or [::1]. Reject embedded credentials,
  queries, fragments, traversal/encoded path components and malformed approvals.
  Keep Azure's HTTPS-origin validation separate. Disable redirects on both SDK
  transports. Restart after backend approval/credential changes.
- Preserve separate app/purpose grants, selection permissions, snapshot/cache
  checks and revocation. Do not silently substitute a model on failure.
- Wrap compatible guardrail models to require a complete stop response containing
  exactly yes/no (case/outer whitespace normalized), with no tool call or refusal.
  Reject empty, explanatory or truncated decisions before NeMo interprets/logs
  them. Return a controlled 503 for runtime model evaluation errors; do not store
  an unvalidated answer as a successful turn.
- Mount an app Models tab: administrators create profiles, approve/revoke each
  purpose, and select models. Developers register app-owned
  main profiles and select their approved main choices; they cannot change
  guardrail selection or administer grants. App-owned creation grants main access
  automatically; admin-managed catalogue creation grants nothing.
- Support the independently configured policy-authoring client through the same
  compatible protocol/metadata validation. Keep JSON validation, management JWT,
  timeouts, safe errors and the review-only draft flow.

For concrete Windows steps for Claude and Ollama, read the
[model-switch walkthroughs](model-switch-walkthroughs.md). Claude also provides
an official compatible endpoint for direct evaluation; a separate gateway is
needed only when the selected API requires translation or additional routing.

## Configure An Admin-Managed Profile

First provision an approved gateway/server separately. For example, a TLS gateway
can expose https://llm-gateway.example.com/v1. Keep upstream vendor credentials
at the gateway, and put only its scoped client credential on the GMS backend.
The optional [gateway configuration example](../examples/model-gateway.example.yml)
contains placeholder model IDs, two versioned aliases and environment references;
it is not a deployment manifest or a tested upstream configuration.

On the GMS backend, set these privately (placeholders shown):

    GMS_ALLOWED_COMPATIBLE_LLM_ENDPOINTS=https://llm-gateway.example.com/v1
    GMS_ALLOWED_LLM_CREDENTIAL_ENV_VARS=GMS_MODEL_GATEWAY_KEY
    GMS_MODEL_GATEWAY_KEY=<restricted gateway client key>

Preserve any existing approved credential names in the comma-separated list.
Restart the backend after provisioning. An administrator then creates a profile
through the Models tab or POST /llm-configs:

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

Approve that configuration for the app's main purpose, then select it. Create
and separately approve a guardrail-v1 profile for the guardrail purpose. The
existing grant endpoints and app update API work with these profiles; the Azure
switching guide documents their ordering. Do not auto-grant the whole catalogue.

For independent policy authoring, configure the backend explicitly:

    GMS_POLICY_AI_PROVIDER=openai_compatible
    GMS_POLICY_AI_ENDPOINT=https://llm-gateway.example.com/v1
    GMS_POLICY_AI_MODEL=authoring-v1
    GMS_POLICY_AI_CREDENTIAL_REFERENCE=env:GMS_MODEL_GATEWAY_KEY

Provision and test that authoring alias at the gateway as well. The committed
default remains azure_openai. App model selections do not authorize the authoring
client or supply its configuration.

For local diagnostics, an explicitly approved base URL such as
http://127.0.0.1:4000/v1 is possible when the gateway is on the backend's host.
Ollama's direct compatible URL is http://127.0.0.1:11434/v1. A direct unauthenticated
local server still needs a non-secret SDK placeholder. App-owned registration
accepts it in Provider API key; the admin-managed path uses an approved env
reference containing the placeholder. GMS does not infer no-auth or reuse another
provider's key.
A container's localhost identifies the container/group, not the home computer.
A remote or host.docker.internal service needs an approved HTTPS endpoint in
this patch; it does not permit arbitrary private-network HTTP destinations.

## Gateway Controls And Model Compatibility

Use scoped gateway keys restricted to the approved aliases. Keep each alias's
upstream mapping fixed/versioned; changing the provider behind an existing alias
is invisible to GMS database grants/cache checks. Register a new version/profile
and approve it when changing its upstream destination or model. Do not configure
wildcard routing or automatic fallbacks that move data to unapproved models.
Keep GMS policies and tool execution inside GMS; no gateway MCP routing is needed.

Only standard chat text, tool calls/results and completion metadata are in the
new protocol contract. Provider-specific reasoning/multimodal fields are not
promised. The gateway must normalize parameter/token limits and keep private
thinking separate from answer text. NeMo sends short classifier budgets and
model options; reasoning models can need different budgets or thinking disabled.
If the selected gateway/model cannot satisfy the contract, evaluation fails closed;
a general adapter does not prove model quality or feature equivalence.

Test each candidate for main-agent tool calling, guardrail allowed/blocked and
secret-output cases, classification errors/timeouts, and authoring structured JSON
as applicable. Measure latency and accuracy using the actual provider/version.
The synthetic tests do not establish real Claude/Gemini/Bedrock/Ollama behavior.

## Review And Verification

The approved patch and baseline hashes are retained in the ignored .waylog review
artifacts. Baseline and patch hashes were verified before applying, and applied
contents matched the reviewed copy. Tests
use the existing home Python environment; it differs from committed dependency
pins, so clean pinned-install/container verification remains required before
release. A gateway install/deployment is outside this source integration.

The complete offline catalogue passed on the applied source: 33 passed, 0 failed.
Whole-project TypeScript, changed-file legacy ESLint 8 lint, Python syntax and
whitespace checks also passed. The current ESLint 9 configuration, clean pinned
dependencies/image build, browser interactions, PostgreSQL and actual upstream
models remain unverified. Run the safe offline catalogue from the repository root:

~~~powershell
.\.venv\Scripts\python.exe -B scripts/run_security_checks.py
~~~

Then perform opt-in live gateway/model testing against a rehearsal database.
Normal GitHub MCP settings remain read-only, and selective merge refusal remains.

Primary references checked on 2026-10-20:

- [LiteLLM gateway](https://docs.litellm.ai/docs/simple_proxy)
- [Gateway provider catalogue](https://docs.litellm.ai/docs/providers)
- [Gateway aliases and configuration](https://docs.litellm.ai/docs/proxy/configs)
- [Gateway function calling](https://docs.litellm.ai/docs/completion/function_call)
- [LangChain standard API scope](https://docs.langchain.com/oss/python/integrations/chat/openai)
- [Ollama compatible endpoint](https://docs.ollama.com/api/openai-compatibility)
