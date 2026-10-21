# Setup Guide For NVIDIA's Supported LLM Providers In This GMS


Current form/API instructions were reconciled with the applied source on
22 October 2026. All 11 JSON examples across the model guides validate against
the current schemas; app-owned Azure registration and a real guarded native-MCP
read pass in the final clean image. This does not certify every provider recipe.
See [the final home results](home-verification-results-2026-10-22.md).

## App-owned main-model registration - 22 October 2026

Applied source now lets linked app developers/admins use Models > Add model profile
with their own endpoint and API key. Direct Azure and compatible API/gateway
protocols are supported. A profile gets immediate main-purpose access for that
app; Save model selections activates it. It cannot be granted to another app or
used for classification. Existing global catalogue provisioning below remains
admin-managed.

The endpoint must still satisfy backend destination approvals. For Azure, API
version remains backend-configured. Provision the dedicated
GMS_MODEL_CREDENTIAL_ENCRYPTION_KEY privately and apply the additive app-owned
model schema before restarting an existing backend database. Stored keys are
encrypted and omitted from responses/log bodies. Keep a protected encryption-key
backup separate from database backups. The user subsequently confirmed home schema application and private key setup.
See [the rollout and test record](developer-main-model-registration-review.md).


Checked on 2026-10-20. This is an implementation-aware companion to
[NVIDIA's supported LLM page](https://docs.nvidia.com/nemo/guardrails/about-nemo-guardrails-library/supported-llms),
not a claim that every listed model has been tested in this project.

## Read This Before Following The NVIDIA Examples

The linked page describes the latest NeMo library. This repository pins
nemoguardrails==0.21.0 and injects an app-selected LangChain model into LLMRails.
The management API currently accepts azure, azure_openai and openai_compatible.
NeMo engine names and GMS profile API types are different configuration layers.
Installing a vendor package or changing config/config.yml does not change the
GMS model factory, app selections or grants. Do not upgrade NeMo, set newer
framework switches or install every provider SDK into the application just to
follow the latest page. A native adapter/version migration is separate work.

The guide covers every named inference engine/alias, each compatible example
named by NVIDIA, the generic community-provider entry and the embedding list.
Providers expose many model IDs: use the exact ID currently enabled in your
account/deployment rather than treating a fixed example as universally available.

A recipe labelled DIRECT means the applied adapter can express that HTTP/auth
contract. It is a compatibility inference from source and vendor documentation,
not a live service/model certification. SERVE FIRST means another serving process
must exist. EXTRA INTEGRATION means the current profile cannot express the
native API/process/authentication requirements as-is.

## Coverage And Navigation

| NVIDIA engine or named example | Project route | Recipe |
| --- | --- | --- |
| azure, azure_openai | Existing Azure adapter | [Azure](#azure) |
| openai | Compatible Chat Completions profile | [OpenAI](#openai) |
| anthropic | Claude's compatible API, or gateway | [Claude](#anthropic) |
| cohere | Cohere compatibility API | [Cohere](#cohere) |
| google_genai | Gemini compatible API | [Gemini](#google-genai) |
| nim, nvidia_ai_endpoints | Hosted NIM or a served NIM endpoint | [NIM](#nim) |
| ollama | Ollama /v1 API | [Ollama](#ollama) |
| huggingface_endpoint | Deployed chat-compatible endpoint | [HF endpoint](#huggingface-endpoint) |
| huggingface_hub | Compatible routed inference, not a legacy wrapper | [HF Hub](#huggingface-hub) |
| huggingface_pipeline | Serve the model or add an adapter | [HF pipeline](#huggingface-pipeline) |
| trt_llm | Compatible TensorRT-LLM server or translation | [TensorRT-LLM](#trt-llm) |
| self_hosted | Depends on the server protocol | [Self-hosted](#self-hosted) |
| vertexai | Gateway for managed IAM; constrained direct token test | [Vertex AI](#vertexai) |
| vllm_openai / vLLM | vLLM's compatible server | [vLLM](#vllm) |
| deepseek / DeepSeek | Compatible service endpoint | [DeepSeek](#deepseek) |
| TGI | Messages-compatible server | [TGI](#tgi) |
| OpenRouter | Compatible service; constrain upstream routing | [OpenRouter](#openrouter) |
| Together.ai | Compatible service endpoint | [Together](#together) |
| Fireworks.ai | Compatible service endpoint | [Fireworks](#fireworks) |
| Groq | Compatible service endpoint | [Groq](#groq) |
| llama.cpp | llama-server with a suitable chat template | [llama.cpp](#llamacpp) |
| NVIDIA Nemotron | Model family served through NIM/another server | [Nemotron](#nemotron) |
| &lt;provider_name&gt; | Compatible endpoint, gateway adapter, or new code | [Other community providers](#community-provider) |
| content-safety, topic-control, jailbreak-detect models | Dedicated rail integration required | [Specialist rails](#specialist-rails) |
| Embedding providers | Separate retrieval/embedding configuration | [Embeddings](#embeddings) |

## Common Steps A: Before Any Switch

1. Choose a MAIN AGENT model first. Preserve the existing working guardrail
   configuration, its grant, current app model IDs and app API key for rollback.
   Main-agent tool calling, guardrail classification and policy-authoring JSON
   are three different acceptance targets.
2. Use a prepared local/rehearsal database and a normal management account.
   Linked app developers can register their own main models; administrators also
   manage global profiles, grants and classifiers. Provider probes below need no database; profile CRUD, grants, login
   and full runtime do. If the home Azure DB still times out, finish only the
   provider probes and stop before management/runtime steps. Home localhost:5433
   is a separate database; consult work-computer-handoff.md for its state.
3. Run the Python backend directly on Windows for the localhost recipes. A Docker
   container, WSL machine or ACI group may have a different localhost. GMS permits
   remote HTTPS and explicitly approved literal loopback HTTP only. A remote
   http://host.docker.internal or private-IP HTTP URL is not accepted.
4. Store backend secrets in the ignored ROOT .env/backend secret environment.
   For an app-owned main profile, enter its provider key in the masked form; the
   backend encrypts it. Do not put keys in frontend dotenv files, URLs or Git.
   Approval lists contain names/URLs, never keys. Merge new entries into existing
   comma-separated lists, with one definition per setting. Keep the existing
   four Azure defaults if either selected runtime role uses Azure.
5. Keep GITHUB_MCP_READ_ONLY=1 for these model checks. A reachable model does not
   repair missing GitHub connector access, PAT, Docker/native MCP launcher,
   policies or grants.

The GPU-serving recipes assume suitable separate hardware and a reviewed serving
environment. Your earlier Ollama run reported CPU inference; it does not establish
that the home computer can run the NVIDIA GPU examples.

## Common Steps B: Test A Compatible Endpoint Without PostgreSQL

Open PowerShell in the project root. Define these two functions once in that
terminal. These are interactive diagnostic snippets, not new project scripts.
PowerShell does not automatically load a .env file. The first function sets only
the current process environment; if you start the API from that terminal it
inherits that key. Persistent setup still needs the backend secret environment.

~~~powershell
function Set-ProbeCredential {
    param([Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z_][A-Za-z0-9_]*$')][string]$Name)
    $probeSecret = Read-Host "Enter the credential for $Name (hidden)" -AsSecureString
    $probeCredential = [System.Management.Automation.PSCredential]::new('unused', $probeSecret)
    [Environment]::SetEnvironmentVariable($Name, $probeCredential.GetNetworkCredential().Password, 'Process')
}

function Test-CompatibleModel {
    param(
        [Parameter(Mandatory=$true)][string]$BaseUrl,
        [Parameter(Mandatory=$true)][string]$Model,
        [Parameter(Mandatory=$true)][string]$KeyEnv,
        [ValidateSet('max_tokens','max_completion_tokens')][string]$TokenField = 'max_tokens'
    )
    $probeKey = [Environment]::GetEnvironmentVariable($KeyEnv, 'Process')
    if ([string]::IsNullOrWhiteSpace($probeKey)) { throw "Set $KeyEnv in this terminal first." }
    $probePayload = @{
        model = $Model
        stream = $false
        messages = @(@{ role = 'user'; content = 'Reply with exactly READY.' })
    }
    $probePayload[$TokenField] = 512
    $probeBody = $probePayload | ConvertTo-Json -Depth 8
    $probeTimer = [System.Diagnostics.Stopwatch]::StartNew()
    $probeResponse = Invoke-RestMethod -Uri ($BaseUrl.TrimEnd('/') + '/chat/completions') -Method Post -ContentType 'application/json' -Headers @{ Authorization = "Bearer $probeKey" } -Body $probeBody -TimeoutSec 180
    $probeTimer.Stop()
    $probeText = [string]$probeResponse.choices[0].message.content
    [pscustomobject]@{
        Model = $probeResponse.model
        FinishReason = $probeResponse.choices[0].finish_reason
        ExactReady = ($probeText.Trim() -eq 'READY')
        Seconds = [math]::Round($probeTimer.Elapsed.TotalSeconds, 1)
    }
}
~~~

Set the recipe's base URL/model/key, then run its probe. Remote probes are real
provider requests. A normal complete response has FinishReason=stop; empty or
length-terminated output is not a passing format check. This probe sends a bounded
output option; it does not persist generation options in GMS. Providers can
require a different supported token field/budget. Do not infer role suitability
from a successful READY response.

GMS compatible requests have a 60-second request timeout and the full runtime
has a 120-second outer timeout. A 180-second standalone success may still be too
slow for GMS. Check cold/warm latency, full tool-context size and thinking defaults.
The standalone probe does not apply GMS guardrails or its endpoint allowlist.

## Common Steps C: Register, Approve And Select The Profile

API Type and credential storage are separate choices. Both administrators and
linked developers start with the same API Type-first Add model profile form.
Use the default app-owned path for a main model with your own provider key.

### Default: app-owned main model (developer or administrator)

1. A backend operator approves the exact destination first. Compatible APIs use
   GMS_ALLOWED_COMPATIBLE_LLM_ENDPOINTS including /v1 or the recipe's path; Azure
   uses GMS_ALLOWED_LLM_ENDPOINTS with the resource HTTPS origin. The backend
   default Azure endpoint is already approved. Preserve existing approvals.
2. On an existing database, the reviewed app-owned model schema must be present
   and GMS_MODEL_CREDENTIAL_ENCRYPTION_KEY provisioned privately before backend
   startup. Home schema/key setup is already complete; keep the existing key.
   For Azure runtime roles, retain all four AZURE_OPENAI_* defaults as required
   by the current factory. Restart after backend approval/environment changes.
3. Start the local frontend using the same-origin proxy:

~~~powershell
$env:NEXT_PUBLIC_API_BASE_URL = '/api/gms'
$env:GMS_API_BASE_URL = 'http://127.0.0.1:8000'
npm.cmd --prefix frontend run dev
~~~

4. Sign in, open Apps -> your linked app -> Models -> Add model profile (to the
   right of Save model selections). Set API Type, Profile Name, Model / Gateway
   Alias (or Azure Deployment Name), API Base URL (or Azure Endpoint), and
   Provider API key. Enter the actual provider key in the masked field. For a
   deliberately unauthenticated local server only, a non-secret placeholder
   such as ollama-local-placeholder is sufficient. An endpoint is required here.
5. Click Add model profile. The backend encrypts the key and creates this app's
   main-only grant automatically. Choose the new Main agent and click Save model
   selections. Registration alone does not change the active selection. Keep the
   working classifier; developers cannot change it or register classifier models.
6. In Runtime Test, enter the existing GMS app API key, use a fresh Conversation
   ID per independent test, and request a permitted read such as list_branches.
   This is a different key from Provider API key. Verify actual tool execution
   and expected result names, not only green rail badges. Reusing a conversation
   ID loads stored history; sending conversation_history=[] does not erase it.
7. Restore the previous main selection if needed. Save changes without a backend
   restart. Keep its grant until rollback is verified.

App-owned API automation uses a management JWT and
POST /apps/{APP_ID}/main-models (or /apps/by-client-id/{CLIENT_ID}/main-models):

~~~json
{
  "name": "App main model v1",
  "provider": "openai_compatible",
  "model_name": "your-tested-model-or-alias",
  "endpoint": "https://provider.example/v1",
  "api_key": "replace_privately_with_provider_key"
}
~~~

Use real approved metadata, not provider.example. Do not add credential_reference,
enabled or owner_app_id to this strict payload. The returned profile has an ID
and owner_app_id but no plaintext key, ciphertext or credential reference. Select
it with PUT /apps/{APP_ID} and {"main_llm_config_id": CONFIG_ID}. The main-only
grant is already created; another app or classifier cannot use this owned model.

### Administrator: backend-managed main/classifier profile

Use this path for a reusable admin-managed profile or a classifier. Provision the
provider key privately on the backend and approve its variable NAME:

~~~env
GMS_ALLOWED_COMPATIBLE_LLM_ENDPOINTS=https://provider.example/v1
GMS_ALLOWED_LLM_CREDENTIAL_ENV_VARS=PROVIDER_API_KEY
PROVIDER_API_KEY=replace_privately_with_the_actual_credential
GITHUB_MCP_READ_ONLY=1
~~~

Merge existing lists and restart the backend after changes. Open the same Add
model profile form, choose API Type, expand Advanced credentials, then check
Use a backend-managed credential. Enter only the variable NAME in Credential
Environment Variable, without its value or env: prefix. For Azure only, blank
endpoint/key reference intentionally uses backend defaults. Compatible profiles
require an explicit approved base URL and credential variable; a local no-auth
server still uses a non-secret placeholder variable in this mode.

Click Add model profile, then select the new profile and purpose under Approve
model access for this app and click Approve access. This admin-managed creation
path grants nothing automatically. Select the granted main/classifier profile
and Save model selections. The Approve access button is right-aligned below Add
model profile. Advanced credentials and grant administration are absent for devs.

API automation for this mode remains POST /llm-configs with credential_reference
set to env:PROVIDER_API_KEY, followed by the explicit app/purpose grant PUT and
selection PUT. Never send a raw api_key field to /llm-configs. Classifiers are
per-app and admin-only; they must pass the separate yes/no acceptance tests.

The form clears its provider-key state after submission/closing. Stored keys
cannot be read back. Keep the backend encryption key backed up separately from
DB backups. Do not rotate the GMS app API key or encryption key just to switch
models. The Models tab does not switch policy authoring: it uses independent
GMS_POLICY_AI_* settings and needs its own JSON acceptance checks.

<a id="azure"></a>
## Azure OpenAI: azure And azure_openai

Status: DIRECT, through the existing Azure-specific adapter.

1. Ask the resource owner for its HTTPS Azure OpenAI resource endpoint, enabled
   chat deployment name, supported API version and appropriate model credential.
   Database/registry credentials are unrelated.
2. Keep/provision all four existing defaults privately in the ROOT .env:

~~~env
AZURE_OPENAI_API_KEY=replace_privately
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_VERSION=your_supported_api_version
AZURE_OPENAI_DEPLOYMENT=your_actual_deployment_name
~~~

3. For a different resource, append its HTTPS ORIGIN to
   GMS_ALLOWED_LLM_ENDPOINTS. Only the admin backend-managed path also needs its
   key variable NAME in GMS_ALLOWED_LLM_CREDENTIAL_ENV_VARS. Azure origins do not include /v1 or a
   deployment path. The configured default Azure origin/key name is already
   approved. Restart the backend after environment changes.
4. For an independent native API probe, supply the actual deployment/version:

~~~powershell
$azureEndpoint = (Read-Host 'Azure resource HTTPS endpoint').TrimEnd('/')
$azureDeployment = Read-Host 'Actual Azure deployment name'
$azureVersion = Read-Host 'Supported Azure API version'
Set-ProbeCredential -Name 'AZURE_OPENAI_API_KEY'
$azureProbeBody = @{ messages = @(@{ role = 'user'; content = 'Reply with exactly READY.' }); stream = $false } | ConvertTo-Json -Depth 6
$azureProbeUri = $azureEndpoint + '/openai/deployments/' + [uri]::EscapeDataString($azureDeployment) + '/chat/completions?api-version=' + [uri]::EscapeDataString($azureVersion)
$azureProbe = Invoke-RestMethod -Uri $azureProbeUri -Method Post -ContentType 'application/json' -Headers @{ 'api-key' = $env:AZURE_OPENAI_API_KEY } -Body $azureProbeBody -TimeoutSec 90
$azureText = [string]$azureProbe.choices[0].message.content
[pscustomobject]@{ Model = $azureProbe.model; FinishReason = $azureProbe.choices[0].finish_reason; ExactReady = ($azureText.Trim() -eq 'READY') }
~~~

5. Follow Common Steps C, choose API Type Azure OpenAI, and use the deployment
   name and resource origin. The default app-owned form takes the actual provider
   key and creates main access automatically. The admin Advanced credentials
   path instead takes an approved Azure key variable NAME or its default fallback
   and requires an explicit purpose grant.
   azure and azure_openai are aliases, not two separately provisioned services.

The runtime Azure adapter uses the shared API version and temperature=0; a
probe with omitted temperature does not prove that a deployment accepts that
runtime setting. Entra/token refresh is not added by this key-based recipe.
[Microsoft chat-completions documentation](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/chatgpt?view=foundry-classic).

<a id="openai"></a>
## OpenAI public API

NVIDIA entry: openai. Status: DIRECT compatible HTTP contract; live model
acceptance is still required.

1. Create a project API key in the OpenAI API platform and select a model available to that project that supports Chat Completions and function tools. Use an API model ID, not a ChatGPT UI label.
2. Store the credential privately under OPENAI_API_KEY; approve that NAME and the
   exact base URL https://api.openai.com/v1 using Common Steps C.
3. In the probe terminal, use the helpers from Common Steps B:

~~~powershell
Set-ProbeCredential -Name 'OPENAI_API_KEY'
$probeModel = Read-Host 'Exact enabled model ID for OpenAI public API'
Test-CompatibleModel -BaseUrl 'https://api.openai.com/v1' -Model $probeModel -KeyEnv 'OPENAI_API_KEY' -TokenField 'max_completion_tokens'
~~~

4. Restart the backend after environment changes, then register a Compatible
   API / Model Gateway profile with that base URL, model ID and credential
   variable name. Approve Main agent access, select and save (Common Steps C).
5. Verify an allowed real read-tool round trip and a policy block. Keep the
   working guardrail selection until separate classification tests pass.

The current GMS client uses Chat Completions; selecting a Responses-only model does not add Responses API support. Use max_completion_tokens in the standalone probe if the model requires it. Actual GMS agent requests do not inherit the probe token setting.
[Provider setup reference](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create).

<a id="anthropic"></a>
## Anthropic / Claude

NVIDIA entry: anthropic. Status: DIRECT compatible HTTP contract; live model
acceptance is still required.

1. Create a Claude API key and copy a model ID enabled for that account from the Claude Console. Use a suitable workspace-scoped key for this direct route.
2. Store the credential privately under ANTHROPIC_API_KEY; approve that NAME and the
   exact base URL https://api.anthropic.com/v1 using Common Steps C.
3. In the probe terminal, use the helpers from Common Steps B:

~~~powershell
Set-ProbeCredential -Name 'ANTHROPIC_API_KEY'
$probeModel = Read-Host 'Exact enabled model ID for Anthropic / Claude'
Test-CompatibleModel -BaseUrl 'https://api.anthropic.com/v1' -Model $probeModel -KeyEnv 'ANTHROPIC_API_KEY'
~~~

4. Restart the backend after environment changes, then register a Compatible
   API / Model Gateway profile with that base URL, model ID and credential
   variable name. Approve Main agent access, select and save (Common Steps C).
5. Verify an allowed real read-tool round trip and a policy block. Keep the
   working guardrail selection until separate classification tests pass.

The compatible API is an evaluation route, not the native Messages API. Keys requiring an anthropic-workspace-id header need a suitable gateway or additional integration because GMS has no profile header field. The compatibility layer ignores some native/structured-output options. Start with the main agent; see model-switch-walkthroughs.md for detailed Claude steps.
[Provider setup reference](https://platform.claude.com/docs/en/cli-sdks-libraries/libraries/openai-sdk).

<a id="cohere"></a>
## Cohere

NVIDIA entry: cohere. Status: DIRECT compatible HTTP contract; live model
acceptance is still required.

1. Create a Cohere API key in its dashboard. Choose an enabled conversational model with tool support; an embedding or reranking model is not a main-agent model.
2. Store the credential privately under COHERE_API_KEY; approve that NAME and the
   exact base URL https://api.cohere.ai/compatibility/v1 using Common Steps C.
3. In the probe terminal, use the helpers from Common Steps B:

~~~powershell
Set-ProbeCredential -Name 'COHERE_API_KEY'
$probeModel = Read-Host 'Exact enabled model ID for Cohere'
Test-CompatibleModel -BaseUrl 'https://api.cohere.ai/compatibility/v1' -Model $probeModel -KeyEnv 'COHERE_API_KEY'
~~~

4. Restart the backend after environment changes, then register a Compatible
   API / Model Gateway profile with that base URL, model ID and credential
   variable name. Approve Main agent access, select and save (Common Steps C).
5. Verify an allowed real read-tool round trip and a policy block. Keep the
   working guardrail selection until separate classification tests pass.

Use the compatibility path shown here, rather than the native /v2/chat endpoint. Cohere-specific options outside the standard API need a gateway mapping or a new adapter.
[Provider setup reference](https://docs.cohere.com/docs/compatibility-api).

<a id="google-genai"></a>
## Google Gemini Developer API

NVIDIA entry: google_genai. Status: DIRECT compatible HTTP contract; live model
acceptance is still required.

1. Create a Gemini API key in Google AI Studio and select an available text/tool-capable model ID. Confirm that the key/project may use the model.
2. Store the credential privately under GEMINI_API_KEY; approve that NAME and the
   exact base URL https://generativelanguage.googleapis.com/v1beta/openai using Common Steps C.
3. In the probe terminal, use the helpers from Common Steps B:

~~~powershell
Set-ProbeCredential -Name 'GEMINI_API_KEY'
$probeModel = Read-Host 'Exact enabled model ID for Google Gemini Developer API'
Test-CompatibleModel -BaseUrl 'https://generativelanguage.googleapis.com/v1beta/openai' -Model $probeModel -KeyEnv 'GEMINI_API_KEY'
~~~

4. Restart the backend after environment changes, then register a Compatible
   API / Model Gateway profile with that base URL, model ID and credential
   variable name. Approve Main agent access, select and save (Common Steps C).
5. Verify an allowed real read-tool round trip and a policy block. Keep the
   working guardrail selection until separate classification tests pass.

This uses the Gemini Developer API, not Vertex AI IAM credentials. Preserve the /v1beta/openai path. Native Google tools and model-specific thinking controls are separate features; the GMS agent uses its own guarded MCP tools.
[Provider setup reference](https://ai.google.dev/gemini-api/docs/openai).

<a id="nim"></a>
## NVIDIA NIM / NVIDIA AI Endpoints

NVIDIA entry: nim, nvidia_ai_endpoints. Status: DIRECT compatible HTTP contract; live model
acceptance is still required.

1. Open the NVIDIA API Catalog, select a general chat/instruct model with the required tool support, obtain an API key and copy the exact model ID from its API example.
2. Store the credential privately under NVIDIA_API_KEY; approve that NAME and the
   exact base URL https://integrate.api.nvidia.com/v1 using Common Steps C.
3. In the probe terminal, use the helpers from Common Steps B:

~~~powershell
Set-ProbeCredential -Name 'NVIDIA_API_KEY'
$probeModel = Read-Host 'Exact enabled model ID for NVIDIA NIM / NVIDIA AI Endpoints'
Test-CompatibleModel -BaseUrl 'https://integrate.api.nvidia.com/v1' -Model $probeModel -KeyEnv 'NVIDIA_API_KEY'
~~~

4. Restart the backend after environment changes, then register a Compatible
   API / Model Gateway profile with that base URL, model ID and credential
   variable name. Approve Main agent access, select and save (Common Steps C).
5. Verify an allowed real read-tool round trip and a policy block. Keep the
   working guardrail selection until separate classification tests pass.

Both NeMo engine names map to this GMS recipe; do not enter either alias as the GMS API Type. NVIDIA Nemotron models can use this route when offered by the selected endpoint. Specialized content-safety/topic/jailbreak models need their dedicated rail schemas; they are not automatic replacements for this app's yes/no self-check model.
[Provider setup reference](https://docs.api.nvidia.com/nim/reference/llm-apis).

<a id="huggingface-hub"></a>
## Hugging Face Hub / routed inference

NVIDIA entry: huggingface_hub. Status: DIRECT compatible HTTP contract; live model
acceptance is still required.

1. Create a Hugging Face token with Inference Providers permission. In the Hugging Face playground, choose a served chat model/provider combination and copy its exact request model string.
2. Store the credential privately under HF_TOKEN; approve that NAME and the
   exact base URL https://router.huggingface.co/v1 using Common Steps C.
3. In the probe terminal, use the helpers from Common Steps B:

~~~powershell
Set-ProbeCredential -Name 'HF_TOKEN'
$probeModel = Read-Host 'Exact enabled model ID for Hugging Face Hub / routed inference'
Test-CompatibleModel -BaseUrl 'https://router.huggingface.co/v1' -Model $probeModel -KeyEnv 'HF_TOKEN'
~~~

4. Restart the backend after environment changes, then register a Compatible
   API / Model Gateway profile with that base URL, model ID and credential
   variable name. Approve Main agent access, select and save (Common Steps C).
5. Verify an allowed real read-tool round trip and a policy block. Keep the
   working guardrail selection until separate classification tests pass.

A Hub repository name alone does not guarantee hosted inference. Preserve any explicit provider suffix shown in the request (for example organization/model:provider). This is the compatible routed alternative to the legacy Hub wrapper. Choose an approved upstream route; do not silently rely on unrestricted provider changes.
[Provider setup reference](https://huggingface.co/docs/inference-providers/tasks/chat-completion).

<a id="deepseek"></a>
## DeepSeek

NVIDIA entry: deepseek; also a compatible-provider example. Status: DIRECT compatible HTTP contract; live model
acceptance is still required.

1. Create a DeepSeek API key and choose an available chat model ID from its current API documentation/dashboard. The root base URL shown here is intentional.
2. Store the credential privately under DEEPSEEK_API_KEY; approve that NAME and the
   exact base URL https://api.deepseek.com using Common Steps C.
3. In the probe terminal, use the helpers from Common Steps B:

~~~powershell
Set-ProbeCredential -Name 'DEEPSEEK_API_KEY'
$probeModel = Read-Host 'Exact enabled model ID for DeepSeek'
Test-CompatibleModel -BaseUrl 'https://api.deepseek.com' -Model $probeModel -KeyEnv 'DEEPSEEK_API_KEY'
~~~

4. Restart the backend after environment changes, then register a Compatible
   API / Model Gateway profile with that base URL, model ID and credential
   variable name. Approve Main agent access, select and save (Common Steps C).
5. Verify an allowed real read-tool round trip and a policy block. Keep the
   working guardrail selection until separate classification tests pass.

The client appends /chat/completions. A model's reasoning mode and extra response fields need separate evaluation. GMS does not store arbitrary thinking options in profiles; do not assume a reasoning model satisfies NeMo's short classifier calls.
[Provider setup reference](https://api-docs.deepseek.com/).

<a id="openrouter"></a>
## OpenRouter

NVIDIA entry: openai with a custom base URL (named example). Status: DIRECT compatible HTTP contract; live model
acceptance is still required.

1. Create an OpenRouter key and choose the exact model slug from its catalogue. Restrict the permitted upstream providers/models through the service's controls or an approved gateway.
2. Store the credential privately under OPENROUTER_API_KEY; approve that NAME and the
   exact base URL https://openrouter.ai/api/v1 using Common Steps C.
3. In the probe terminal, use the helpers from Common Steps B:

~~~powershell
Set-ProbeCredential -Name 'OPENROUTER_API_KEY'
$probeModel = Read-Host 'Exact enabled model ID for OpenRouter'
Test-CompatibleModel -BaseUrl 'https://openrouter.ai/api/v1' -Model $probeModel -KeyEnv 'OPENROUTER_API_KEY'
~~~

4. Restart the backend after environment changes, then register a Compatible
   API / Model Gateway profile with that base URL, model ID and credential
   variable name. Approve Main agent access, select and save (Common Steps C).
5. Verify an allowed real read-tool round trip and a policy block. Keep the
   working guardrail selection until separate classification tests pass.

A fixed model slug may still be routed to different underlying providers. Profile grants do not constrain routing inside OpenRouter. If an approved route needs request-body routing options that GMS cannot express, enforce them in a gateway instead of assuming an endpoint/profile grant is enough.
[Provider setup reference](https://openrouter.ai/docs/quickstart).

<a id="together"></a>
## Together AI

NVIDIA entry: openai with a custom base URL (named example). Status: DIRECT compatible HTTP contract; live model
acceptance is still required.

1. Create a Together API key and select an available chat/tool model in its model catalogue. Copy the full namespaced model ID.
2. Store the credential privately under TOGETHER_API_KEY; approve that NAME and the
   exact base URL https://api.together.ai/v1 using Common Steps C.
3. In the probe terminal, use the helpers from Common Steps B:

~~~powershell
Set-ProbeCredential -Name 'TOGETHER_API_KEY'
$probeModel = Read-Host 'Exact enabled model ID for Together AI'
Test-CompatibleModel -BaseUrl 'https://api.together.ai/v1' -Model $probeModel -KeyEnv 'TOGETHER_API_KEY'
~~~

4. Restart the backend after environment changes, then register a Compatible
   API / Model Gateway profile with that base URL, model ID and credential
   variable name. Approve Main agent access, select and save (Common Steps C).
5. Verify an allowed real read-tool round trip and a policy block. Keep the
   working guardrail selection until separate classification tests pass.

Use the currently documented api.together.ai base URL rather than assuming an older host redirects. GMS refuses redirects. Select the exact model ID instead of a family/display name.
[Provider setup reference](https://docs.together.ai/docs/inference/openai-compatibility).

<a id="fireworks"></a>
## Fireworks AI

NVIDIA entry: openai with a custom base URL (named example). Status: DIRECT compatible HTTP contract; live model
acceptance is still required.

1. Create a Fireworks API key. Select an available serverless or dedicated chat deployment and copy its exact model/deployment identifier from the request example.
2. Store the credential privately under FIREWORKS_API_KEY; approve that NAME and the
   exact base URL https://api.fireworks.ai/inference/v1 using Common Steps C.
3. In the probe terminal, use the helpers from Common Steps B:

~~~powershell
Set-ProbeCredential -Name 'FIREWORKS_API_KEY'
$probeModel = Read-Host 'Exact enabled model ID for Fireworks AI'
Test-CompatibleModel -BaseUrl 'https://api.fireworks.ai/inference/v1' -Model $probeModel -KeyEnv 'FIREWORKS_API_KEY'
~~~

4. Restart the backend after environment changes, then register a Compatible
   API / Model Gateway profile with that base URL, model ID and credential
   variable name. Approve Main agent access, select and save (Common Steps C).
5. Verify an allowed real read-tool round trip and a policy block. Keep the
   working guardrail selection until separate classification tests pass.

Preserve /inference/v1. Deployment/model identifiers may be namespaced. Availability of text generation alone does not establish tool-call support for the chosen model.
[Provider setup reference](https://docs.fireworks.ai/tools-sdks/openai-compatibility).

<a id="groq"></a>
## Groq

NVIDIA entry: openai with a custom base URL (named example). Status: DIRECT compatible HTTP contract; live model
acceptance is still required.

1. Create a key in the Groq console and choose an available chat model with the required tool capabilities.
2. Store the credential privately under GROQ_API_KEY; approve that NAME and the
   exact base URL https://api.groq.com/openai/v1 using Common Steps C.
3. In the probe terminal, use the helpers from Common Steps B:

~~~powershell
Set-ProbeCredential -Name 'GROQ_API_KEY'
$probeModel = Read-Host 'Exact enabled model ID for Groq'
Test-CompatibleModel -BaseUrl 'https://api.groq.com/openai/v1' -Model $probeModel -KeyEnv 'GROQ_API_KEY'
~~~

4. Restart the backend after environment changes, then register a Compatible
   API / Model Gateway profile with that base URL, model ID and credential
   variable name. Approve Main agent access, select and save (Common Steps C).
5. Verify an allowed real read-tool round trip and a policy block. Keep the
   working guardrail selection until separate classification tests pass.

Preserve /openai/v1. Provider-specific parameter restrictions remain relevant, especially for classification and structured output. GMS does not expose arbitrary request options in a saved profile.
[Provider setup reference](https://console.groq.com/docs/openai).

<a id="ollama"></a>
## Ollama

NVIDIA entry: ollama. Status: DIRECT compatible server on the backend's host.

1. Open the Ollama Windows application, then check its model catalogue:

~~~powershell
ollama list
Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 10
~~~

2. Your earlier pull already installed qwen3:4b. Only if missing, run ollama
   pull qwen3:4b. If using the standalone server instead of the Windows app,
   leave ollama serve running in another terminal.
3. Set an explicit non-secret placeholder and probe the compatible API:

~~~powershell
$env:OLLAMA_LOCAL_KEY = 'ollama-local-placeholder'
Test-CompatibleModel -BaseUrl 'http://127.0.0.1:11434/v1' -Model 'qwen3:4b' -KeyEnv 'OLLAMA_LOCAL_KEY'
~~~

4. Add that URL to GMS_ALLOWED_COMPATIBLE_LLM_ENDPOINTS, add OLLAMA_LOCAL_KEY
   to the credential-name list and persist the same placeholder on the backend.
   Restart, then create/approve/select the compatible main profile in Common C.
5. Run a full read-tool test. Qwen3 is thinking-capable and your prior native
   format probe failed. This profile does not persist think=false or arbitrary
   reasoning settings; investigate incomplete/slow responses before using it.

See the more detailed [Windows Ollama walkthrough](model-switch-walkthroughs.md#2a-test-ollama-without-the-database)
and [Ollama compatible API](https://docs.ollama.com/api/openai-compatibility).

<a id="huggingface-endpoint"></a>
## Hugging Face Inference Endpoint

NVIDIA entry: huggingface_endpoint. Status: DIRECT only when the deployed
endpoint serves the compatible CHAT API; otherwise EXTRA INTEGRATION.

1. In Hugging Face Inference Endpoints, deploy an approved chat/instruct model
   with the necessary hardware and serving engine. Confirm model access and
   endpoint readiness. This is a separate provisioning action, not a GMS setting.
2. Open its generated client example. Confirm /v1/chat/completions is exposed and
   copy the actual base URL, served model ID and required token strategy. A
   text-generation-only endpoint with a different JSON schema is insufficient.
3. In PowerShell, supply the generated values:

~~~powershell
Set-ProbeCredential -Name 'HF_ENDPOINT_TOKEN'
$hfEndpointBase = Read-Host 'Actual HTTPS compatible base URL from your endpoint example'
$hfEndpointModel = Read-Host 'Actual served model ID'
Test-CompatibleModel -BaseUrl $hfEndpointBase -Model $hfEndpointModel -KeyEnv 'HF_ENDPOINT_TOKEN'
~~~

4. Approve that exact URL and HF_ENDPOINT_TOKEN in the backend lists. Register
   the compatible profile, approve main access and select it using Common C.
5. Verify full tool calling. If the endpoint is native text generation only,
   re-serve through a suitable TGI/vLLM chat endpoint or a gateway adapter. Merely
   using a model repository URL as the API Base URL does not create a server.

[Hugging Face chat API](https://huggingface.co/docs/inference-providers/tasks/chat-completion)
and [TGI Messages API](https://huggingface.co/docs/text-generation-inference/en/messages_api).

<a id="huggingface-pipeline"></a>
## In-Process Hugging Face Pipeline

NVIDIA entry: huggingface_pipeline. Status: EXTRA INTEGRATION for the native
in-process route; SERVE FIRST for the configuration-only GMS alternative.

1. Choose an approved chat/tool model and suitable CPU/GPU memory. A Python
   transformers pipeline is an object, not an HTTP endpoint.
2. Choose a serving layer that supports the checkpoint: a dedicated HF endpoint,
   vLLM/TGI, or an appropriate converted llama.cpp/Ollama model. Follow its recipe
   below. Conversion, chat templates and tool behavior require separate review.
3. Start that server and obtain its compatible base URL, served ID and credential.
4. Probe that URL using Common B; approve it and register a compatible profile
   using Common C. The checkpoint stays at the server, outside GMS.
5. If you specifically require an IN-PROCESS pipeline instead, stop here: it needs
   a reviewed native GMS adapter, dependency/hardware changes and security tests.
   No endpoint-only step can enable that currently unimplemented factory branch.

[HF deployment options](https://huggingface.co/docs/inference-providers/tasks/chat-completion)
and [vLLM serving](https://docs.vllm.ai/en/latest/serving/online_serving/).

<a id="vllm"></a>
## vLLM And The Legacy vllm_openai Engine

Status: SERVE FIRST, then DIRECT compatible HTTP. GMS uses openai_compatible,
not vllm_openai, for the saved profile.

1. On a separate suitable serving environment, install/pin the operator-reviewed
   vLLM release and model dependencies using its hardware instructions. Do not
   install its dependency stack into this GMS virtual environment.
2. Select a supported chat checkpoint and the matching tool parser/template from
   vLLM's documentation. After setting MODEL_ID, TOOL_PARSER and VLLM_API_KEY
   privately on that serving host, a Linux shell launch pattern is:

~~~bash
vllm serve "$MODEL_ID" --host 127.0.0.1 --port 8100 --api-key "$VLLM_API_KEY" --enable-auto-tool-choice --tool-call-parser "$TOOL_PARSER"
~~~

3. Configure a compatible chat template too if the checkpoint needs one. Parser
   names are model-specific; do not use an arbitrary parser just to start it.
   For a remote serving host, expose an approved authenticated HTTPS endpoint
   through the deployment's proxy; the Windows backend cannot reach the server's
   loopback as its own localhost.
4. For a truly same-host server, approve/probe http://127.0.0.1:8100/v1 with
   VLLM_API_KEY. Otherwise use its actual HTTPS base URL. Get the served model
   ID from the server's /v1/models or startup configuration.
5. Register that URL/ID/key name as a compatible main profile and follow Common C.
   Verify automatic tool choice and a tool-result round trip, not only text chat.

[vLLM serving](https://docs.vllm.ai/en/latest/serving/online_serving/),
[vLLM tool parsers and templates](https://docs.vllm.ai/en/latest/features/tool_calling/).

<a id="tgi"></a>
## Hugging Face Text Generation Inference: TGI

Status: SERVE FIRST. The selected deployment must support the Messages-compatible
chat API and the chosen model's tool format.

1. Select a supported chat checkpoint, appropriate serving hardware and a pinned
   TGI image/release from the operator-reviewed Hugging Face deployment guide.
2. Launch that release with the selected model on the serving host. For a local
   Docker GPU example, use an explicit host port that does not collide with GMS:

~~~powershell
$tgiImage = Read-Host 'Operator-reviewed TGI image including pinned tag/digest'
$tgiModel = Read-Host 'Approved model repository ID'
docker run --rm --name gms-tgi-test --gpus all --shm-size 1g -p 127.0.0.1:8101:80 $tgiImage --model-id $tgiModel
~~~

3. Private/gated model downloads may need an HF token passed privately to the
   serving container per its guide. A download token does not automatically
   authenticate incoming client calls. The loopback example assumes a deliberate
   local no-auth server; use an explicit placeholder key in that case.
4. Verify /v1/chat/completions and the actual served model ID. For a same-host
   deployment, approve/probe http://127.0.0.1:8101/v1 with TGI_LOCAL_KEY; remote
   deployments require an approved authenticated HTTPS route instead.
5. Register a compatible main profile and follow Common C. If that TGI release
   or checkpoint lacks tool calling, choose another server/model or an adapter;
   text-only success is insufficient for the GMS agent.

[TGI deployment](https://huggingface.co/docs/text-generation-inference/en/quicktour),
[TGI Messages API](https://huggingface.co/docs/text-generation-inference/en/messages_api).

<a id="llamacpp"></a>
## llama.cpp / llama-server

Status: SERVE FIRST. This is a practical local-server route when the selected
GGUF model and chat template implement the required tool protocol.

1. Obtain an approved llama.cpp build and GGUF chat model from their official
   distribution/model source. Keep model files outside committed source.
2. On Windows, an example launch pattern from the directory containing the
   executable is below. Use a suitable context size for your hardware/workload.
   The key is passed through the server's documented environment variable:

~~~powershell
$ggufPath = Read-Host 'Absolute path to the approved chat model GGUF file'
Set-ProbeCredential -Name 'LLAMA_API_KEY'
.\llama-server.exe -m $ggufPath --host 127.0.0.1 --port 8102 --ctx-size 8192 --jinja
~~~

3. Leave the server running; use another terminal for probes. Supply the same
   LLAMA_API_KEY privately in that terminal/backend and copy the served ID from
   /v1/models. A correct tool-capable template/parser is required.
4. Approve/probe http://127.0.0.1:8102/v1 when on the same backend host, then
   register the compatible main profile with LLAMA_API_KEY (Common C).
5. Verify a complete tool-call/result round trip. Do not use raw thought/tool
   markup in message.content as if it were a parsed safe tool call.

[Official llama-server options and API](https://github.com/ggml-org/llama.cpp/tree/master/tools/server).

<a id="trt-llm"></a>
## TensorRT-LLM / trt_llm

Status: SERVE FIRST for a compatible TensorRT-LLM server. A legacy native
Triton/TensorRT protocol needs EXTRA INTEGRATION if it lacks that surface.

1. Use a compatible NVIDIA GPU serving host and the operator-approved
   TensorRT-LLM environment/model deployment instructions. This is not a package
   to install blindly into the CPU-based home GMS environment.
2. Confirm the CLI form for the pinned release. Current upstream documents a
   serve subcommand and compatible chat endpoint. In that serving environment,
   set MODEL_PATH to the approved supported checkpoint/engine and run:

~~~bash
trtllm-serve serve --host 127.0.0.1 --port 8103 "$MODEL_PATH"
~~~

3. Configure required model/tokenizer/backend/tool settings for that release.
   Add the serving deployment's authentication/TLS when exposing it remotely.
   An older Triton generate/gRPC endpoint cannot be used as a chat API base URL.
4. Find the exact served model ID using /v1/models. For a deliberate same-host
   no-auth server, use http://127.0.0.1:8103/v1 and an explicit TRT_LOCAL_KEY
   placeholder. Otherwise use its approved HTTPS URL and real client credential.
5. Probe, approve/register the compatible profile and run Common C's tool tests.
   If only the legacy native path is available, use a protocol-translating gateway
   or prepare a native GMS adapter; the engine name alone enables neither.

[TensorRT-LLM server commands](https://nvidia.github.io/TensorRT-LLM/commands/trtllm-serve.html).

<a id="self-hosted"></a>
## Other Self-Hosted Models / self_hosted

Status: DIRECT only after the serving contract is established.

1. Obtain the server's actual API documentation, deployed model ID, endpoint,
   authentication scheme and tool/context capabilities from its operator.
2. Confirm it accepts standard chat messages and emits standard text/tool-call
   responses at base-url/chat/completions. A bare model directory is not a server.
3. If compatible with bearer credentials, run Common B and register that exact
   base URL/model/credential name using Common C. Same-host local no-auth servers
   still need an explicit placeholder; remote services need approved HTTPS.
4. If it needs custom headers/query parameters, different authentication or a
   different protocol, expose an approved compatible gateway that performs those
   functions, or prepare a reviewed adapter change. GMS profiles cannot currently
   express all those fields, even if newer NeMo engines can.
5. Test actual tools and role behavior. Custom weights do not imply chat-template,
   tool calling or yes/no-classification compatibility.

[Existing project boundary](model-gateway-integration.md) and the serving framework
recipes above describe the supported HTTP route.

<a id="vertexai"></a>
## Google Cloud Vertex AI / vertexai

Status: gateway is the durable integration route; a DIRECT short-lived token
experiment is possible for an eligible compatible Vertex endpoint.

1. Have the Google Cloud operator enable the required service/model access,
   project permissions and selected location. A Gemini Developer API key is not
   interchangeable with this IAM authentication setup.
2. For regular operation, provision a separately managed gateway with the
   appropriate Vertex credentials/workload identity, token refresh, project and
   location. Keep cloud IAM credentials at the gateway, and expose a fixed,
   versioned model alias with a restricted gateway client key to GMS.
3. Approve the gateway's HTTPS base URL and its client-key variable, probe the
   alias, then register that compatible main profile using Common C. See the
   gateway integration guide; creating that service is separate deployment work.
4. For a temporary direct test, first authenticate the Google Cloud CLI's
   application-default credentials with the intended authorized account. These
   commands are for you to run in your local terminal:

~~~powershell
gcloud auth application-default login
$vertexProject = Read-Host 'Authorized Google Cloud project ID'
$vertexLocation = Read-Host 'Supported model location'
$vertexModel = Read-Host 'Exact compatible Vertex model ID (including required publisher prefix)'
$env:VERTEX_TEST_ACCESS_TOKEN = (gcloud auth application-default print-access-token | Out-String).Trim()
$vertexBase = "https://$vertexLocation-aiplatform.googleapis.com/v1/projects/$vertexProject/locations/$vertexLocation/endpoints/openapi"
Test-CompatibleModel -BaseUrl $vertexBase -Model $vertexModel -KeyEnv 'VERTEX_TEST_ACCESS_TOKEN'
~~~

5. If evaluating this DIRECT route in GMS, approve that exact generated URL and
   VERTEX_TEST_ACCESS_TOKEN name and launch the backend from the token-bearing
   terminal. Register the compatible profile. Access tokens expire: GMS does
   not refresh them automatically, and a warm client can retain an expired token.
   Refresh the token and restart after changes; do not treat this experiment as
   a complete production IAM integration. Switch away when the experiment ends.

[Google's compatible Vertex example](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/samples/generativeaionvertexai-gemini-chat-completions-non-streaming),
[Gateway Vertex/workload identity](https://docs.litellm.ai/docs/providers/vertex).

<a id="nemotron"></a>
## NVIDIA Nemotron Model Family

1. Choose the specific Nemotron model in the NVIDIA catalogue or your serving
   platform. Nemotron is a family of weights, not another credential/API protocol.
2. If hosted by NVIDIA, follow the NIM recipe with that exact model ID and
   NVIDIA_API_KEY. If served locally/remotely elsewhere, use that server's recipe.
3. Preserve its actual context, reasoning and tool requirements. A large model
   may require remote hardware; its name is not evidence it fits the home machine.
4. Register a separate versioned profile, grant main access and verify tools.
5. Evaluate guardrail classification separately. Specialized safety/jailbreak
   models need dedicated task handling rather than assuming generic yes/no output.

[NVIDIA model/API catalogue](https://docs.api.nvidia.com/nim/reference/llm-apis).

<a id="community-provider"></a>
## Any Other LangChain Community Provider

NVIDIA entry: &lt;provider_name&gt;. This denotes an open-ended integration category,
not a finite set of additional models that can all be listed here.

1. Identify the concrete provider, exact model and intended role. Get its current
   official API/authentication/tool documentation.
2. If it offers a standard compatible API with an expressible credential strategy,
   use Common B/C and create a new approved GMS profile; no native SDK is needed.
3. Otherwise check whether a reviewed gateway has an adapter for it. Configure
   that adapter and fixed alias at the gateway, then use the compatible GMS route.
4. If it is only a LangChain in-process/native client, the current GMS factory
   still needs an adapter branch, schema/validation/grant integration and tests.
   Installing langchain-PROVIDER by itself does not make it selectable.
5. Prepare an exact code/dependency/security diff for that unsupported case under
   AGENTS.md. Do not remove grants, endpoint approvals, strict classifiers or
   execution guards to simulate support. This documentation task adds no adapter.

[NVIDIA's provider boundary](https://docs.nvidia.com/nemo/guardrails/about-nemo-guardrails-library/supported-llms)
and [GMS integration guide](model-gateway-integration.md).

<a id="specialist-rails"></a>
## Guardrail-Specific NVIDIA Models

The source page also mentions content-safety, topic-control and jailbreak-detect
models. They are task-specific models, not interchangeable general chat agents.

1. Choose the exact task/model from its NVIDIA catalogue page and obtain the
   required endpoint/authentication from the deployment owner.
2. Test the vendor's task-specific request and response format in isolation.
   A label, score or structured safety object is not this GMS classifier's yes/no
   contract and must not be accepted as a generic model decision.
3. Prepare a separately reviewed rail integration with explicit task prompts,
   response parsing, error handling and independent model selection. Preserve
   mandatory app/global policies and execution guards.
4. Add allow/block/unknown/error tests for both rail placement and policy scope.
   Do not silently interpret unknown labels as safe.
5. Enable that new rail only after its code/configuration and live model behavior
   are verified. The current Models tab alone does not wire these task adapters.

This is an EXTRA INTEGRATION boundary, not an already-working profile recipe.
See the [NVIDIA task/model catalogue](https://docs.api.nvidia.com/nim/reference/llm-apis).

<a id="embeddings"></a>
## Embedding Providers: Separate From Chat LLM Switching

The linked page also lists embeddings. They produce vectors and are not valid
main-agent/yes-no-classifier profile selections. GMS has no embedding selector.

| Listed provider/engine | Preparation for a future embedding integration |
| --- | --- |
| NVIDIA NIM: nim | Choose an embedding NIM and its authorized endpoint |
| NVIDIA AI Endpoints: nvidia_ai_endpoints | Same provider family/alias; select an embedding model |
| FastEmbed: fastembed | Select an approved local embedding model/runtime |
| OpenAI: openai | Choose an embedding model and API credential |
| Azure OpenAI: azure | Obtain an embedding deployment and resource settings |
| Cohere: cohere | Choose an embedding model and its input-type requirements |
| SentenceTransformers: sentence_transformers | Select a local embedding model/runtime |
| Google: google | Choose the appropriate Google embedding service/auth |

For each: select the retrieval use case, configure the embedding client in that
separate component, test vector dimensions/output, rebuild/version affected
indexes and verify retrieval isolation. This needs a reviewed retrieval/NeMo
configuration slice; there is no honest Models-tab-only setup for these today.
Do not replace a chat profile with an embedding model.

[NVIDIA embedding configuration reference](https://docs.nvidia.com/nemo/guardrails/configure-guardrails/other-configurations/embedding-search-providers).

## Validate A Guardrail Or Policy-Authoring Model Separately

1. Keep the first trial main-only. For later classifier trials, separately grant
   guardrail access and select that profile as an administrator.
2. Test safe/matching/nonmatching input policies and safe/secret/output-policy
   cases, plus model errors, timeouts, malformed and truncated decisions. The
   compatible classifier requires a completed stop answer containing exactly
   yes/no, with no tool/refusal response. These checks cannot establish accuracy
   from a single format probe. Input and output share the selected classifier.
3. NeMo sends short output budgets and model options for self-checks. A current
   reasoning model may need thinking disabled, a larger provider-specific budget
   or parameter mapping that the present profile cannot store. Use a reviewed
   gateway mapping or an adapter change; never bypass fail-closed validation.
4. If switching policy authoring, configure GMS_POLICY_AI_PROVIDER/ENDPOINT/MODEL/
   CREDENTIAL_REFERENCE independently on the backend and test real JSON drafts.
   The authoring path sends json_object and token options; compatible support
   varies by model/provider. Main-agent success is not authoring certification.
5. Keep execution-level tool enforcement and required global policies in place.
   Normal model checks remain read-only; selective PR merge refusal remains.

## Latest NeMo Instructions Versus This Pinned Project

The upstream page can change as NeMo releases change. Its newer framework
switches, engine registry and model-level headers/query options are library
features, not an automatic expansion of this project's profile schema. This
project deliberately builds clients through runtime_factory.py and injects the
classifier into LLMRails; it also builds a separate main-agent client. To adopt
new native NeMo APIs, prepare a separate migration against pinned dependencies
and preserve all three model roles and current security boundaries.

[Upstream migration details](https://docs.nvidia.com/nemo/guardrails/reference/0-22).

## Verification And Remaining Evidence

The instructions were checked against vendor documentation and current GMS
schemas, validators, UI labels and launch code. Commands are examples for you to
run. No real credentials were read, no provider request/server deployment/model
download ran, and no dependency or database changed for this guide. Profile and
snippet syntax validation is recorded in testing-notes.md. Compatible metadata
acceptance is not successful upstream inference, tool use or model quality.

The applied source's 33 isolated regressions remain the safe code check. They
use fake HTTP responses/disposable data and do not certify these real services:

~~~powershell
.\.venv\Scripts\python.exe -B scripts/run_security_checks.py
~~~

Use a fresh conversation for each live acceptance case. Record the selected
profile, endpoint/model version, actual tool outcome, rail decisions, latency and
failure behavior. Keep private prompts/results and keys out of public handover
artifacts. See [the backlog](open-work-backlog.md) for remaining deployment,
clean pinned-install/image and browser verification.
