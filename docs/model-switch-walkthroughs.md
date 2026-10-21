# Change Models: Claude And Ollama On Windows


Current form/API instructions were reconciled with the applied source on
22 October 2026. All 11 JSON examples across the model guides validate against
the current schemas; app-owned Azure registration and a real guarded native-MCP
read pass in the final clean image. This does not certify every provider recipe.
See [the final home results](home-verification-results-2026-10-22.md).

Local-classifier follow-up: qwen2.5:1.5b and qwen2.5:7b were tested on
2026-10-21 with the real NeMo checks. Neither met acceptance; Azure guardrail
classification remains selected. See [the measured results](local-classifier-test-results.md).

Follow-up checked on 2026-10-21: a real GitHub branch-read request now passed
with the selected Qwen2.5 1.5B main profile and Azure classification. See
[the scoped result and pending acceptance cases](model-switch-test-results.md).

Checked against the applied source and provider documentation on 2026-10-20.
These are instructions for you to run; this walkthrough did not contact a real
model, edit your .env, download models, or change database records.

For every provider/engine named in NVIDIA's supported-model page, use the
[complete supported-provider setup guide](supported-llm-setup-guide.md).

## Start Here

This walkthrough assumes the Python GMS backend runs directly on your Windows
computer. Start by changing only the MAIN AGENT. Keep the existing working,
explicitly granted guardrail model selected. This separates agent compatibility
from classification behavior. Both purposes still need valid grants at runtime.

| Candidate | GMS API type | API base URL | Model value | Provider API key in the default form |
| --- | --- | --- | --- | --- |
| Claude direct compatibility API | Compatible API / Model Gateway | https://api.anthropic.com/v1 | Exact model ID available in your Claude Console | Actual Claude key, entered privately |
| Your installed Ollama model | Compatible API / Model Gateway | http://127.0.0.1:11434/v1 | qwen3:4b | ollama-local-placeholder (local no-auth only) |

The provider probes below do not need PostgreSQL. Saving a model profile,
management login, grants and a full GMS Runtime Test DO need a reachable,
prepared PostgreSQL database. If the Azure database still times out, finish the
provider probes and stop before the GMS steps. Your local home port 5433 is a
separate database, not the Azure rehearsal copy. Follow the current handoff for
its target/schema state; do not run migrations or switch databases blindly.

Claude has an official compatible API, so a separate gateway is not required
for this evaluation route. This is a protocol-based inference from the applied
adapter and Anthropic's documentation, not a completed live Claude certification.
Native provider features or an API that lacks this surface may still need a
gateway. Keep policy-authoring AI unchanged for this first test.

## 1. Prepare Backend Approval Settings

Open PowerShell in the repository:

~~~powershell
Set-Location 'C:\Users\adibi\Downloads\nemo-mcp-guardrails-test'
~~~

In the ROOT .env, add/update these settings. Keep one definition per setting.
If approval lists already have entries, APPEND these values to the existing
comma-separated list; do not replace other apps' approvals.

~~~env
GMS_ALLOWED_COMPATIBLE_LLM_ENDPOINTS=https://api.anthropic.com/v1,http://127.0.0.1:11434/v1
GMS_ALLOWED_LLM_CREDENTIAL_ENV_VARS=ANTHROPIC_API_KEY,OLLAMA_LOCAL_KEY
OLLAMA_LOCAL_KEY=ollama-local-placeholder
GITHUB_MCP_READ_ONLY=1
~~~

OLLAMA_LOCAL_KEY is a non-secret SDK placeholder for your local unauthenticated
Ollama server. It is not your Azure password, PAT, database password or Claude key.
Keep existing Azure settings while either runtime role uses Azure. No new Python
provider package is needed for these compatible endpoints.

For Claude, provision ANTHROPIC_API_KEY privately on the backend. The steps below
can set it only for the current PowerShell session so it is not typed into shell
history. For persistent setup, store it privately in the ignored root .env or the
backend deployment's secret environment. Do not put it in frontend/.env.local,
a committed example or a chat message. The default app-owned form is the approved
place to enter that provider key for encrypted backend storage. Environment
variables in this probe section are for direct probes or the admin Advanced
credentials path; app-owned registration does not require a credential-variable
approval. Both paths still require endpoint approval and the backend encryption
key/schema must be ready for app-owned registration.

Process environment values take precedence over .env values. Restart an existing
backend after changing approvals/credentials; a running process does not reload
these settings automatically. If using session-only credentials, launch the API
from that same terminal after probing.

## 2A. Test Ollama Without The Database

1. Confirm the installed model and service:

~~~powershell
ollama --version
ollama list
Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 10 |
    Select-Object -ExpandProperty models |
    Select-Object name
~~~

If the service cannot be reached, open the Ollama Windows application. If you
use its standalone server instead, run ollama serve in another terminal and
leave it running. A port-already-in-use error normally means it is already running.
Only if qwen3:4b is missing, download it with ollama pull qwen3:4b; your earlier
successful pull means that download should not be needed again.

2. Test the SAME compatible API family that GMS uses. /api/chat is Ollama's
native route; GMS profiles must use a /v1 base URL instead.

~~~powershell
$ollamaModel = 'qwen3:4b'
$ollamaBody = @{
    model = $ollamaModel
    stream = $false
    max_tokens = 512
    messages = @(@{ role = 'user'; content = 'Reply with exactly READY.' })
} | ConvertTo-Json -Depth 6

$ollamaTimer = [System.Diagnostics.Stopwatch]::StartNew()
$ollamaResponse = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/v1/chat/completions' -Method Post -ContentType 'application/json' -Headers @{ Authorization = 'Bearer ollama-local-placeholder' } -Body $ollamaBody -TimeoutSec 180
$ollamaTimer.Stop()
$ollamaText = [string]$ollamaResponse.choices[0].message.content
[pscustomobject]@{
    Model = $ollamaResponse.model
    FinishReason = $ollamaResponse.choices[0].finish_reason
    ExactReady = ($ollamaText.Trim() -eq 'READY')
    Seconds = [math]::Round($ollamaTimer.Elapsed.TotalSeconds, 1)
}
~~~

A normal completed answer should have FinishReason=stop. ExactReady=True is a
useful format check. If content is empty, FinishReason=length, or it gives an
explanation, do not mark that probe successful. Your earlier native READY probe
already failed the format check. Qwen3 is a thinking-capable model, and this GMS
profile does not automatically send think=false or reasoning_effort=none.
Sending such an option in a standalone probe does not configure GMS to send it.

Resolve the model/server thinking settings, try a suitable non-thinking model,
or normalize options through an approved gateway if necessary. One small optional
non-thinking candidate is qwen2.5:1.5b (ollama pull qwen2.5:1.5b); use that exact
name in BOTH the probe and the model profile if testing it. Its tools metadata
is not a guarantee of GMS tool reliability or policy accuracy.

GMS compatible calls have a 60-second request timeout and the full runtime has
an outer 120-second timeout. A slow CPU-only model can pass a 180-second direct
probe and still fail GMS. Warm the model, measure the full tool request and check
its context capacity; one tiny chat probe does not prove those requirements.

### Observed Home Qwen3 Result - 2026-10-20

The first real GMS attempt passed the Azure input rail but failed in the Ollama
agent stage at approximately the 60-second client timeout. The installed Qwen3
4B runs on CPU with 4096 context. Small compatible probes exhausted 128/256
output-token budgets without a complete requested answer or tool call, including
/no_think prompts; reasoning_effort=none also did not complete the READY check.
Do not mark this particular setup as accepted. This is not a universal Qwen3
incompatibility claim. A smaller non-thinking candidate remains an untested next
comparison. See [diagnostic evidence](testing-notes.md#local-ollama-agent-timeout-diagnosis---2026-10-20).

## 2B. Test Claude Without The Database

1. Obtain a Claude API key with access to the chosen model from your Claude
Console. The Azure database/registry/OpenAI credentials are different credentials.
Use an appropriate workspace-scoped key: Anthropic documents an additional
anthropic-workspace-id header for personal/service keys spanning workspaces, but
GMS currently has no per-profile custom-header field. If your key requires that
header, use an appropriately configured gateway or a suitable workspace key;
do not assume a standalone header-enabled probe proves the GMS profile can use it.

2. In the PowerShell terminal that will later start the backend:

~~~powershell
$claudeSecret = Read-Host 'Paste your Claude API key (hidden)' -AsSecureString
$claudeCredential = [System.Management.Automation.PSCredential]::new('unused', $claudeSecret)
$env:ANTHROPIC_API_KEY = $claudeCredential.GetNetworkCredential().Password
$claudeModel = Read-Host 'Paste the exact Claude model ID available in your Console'
~~~

Use the exact Anthropic model ID, not a display name, Azure deployment name or
an anthropic/ prefix. No particular model ID is assumed to be enabled for your
account. Avoid selecting a model only by asking its generated answer to identify
itself; inspect configuration and provider records for identity evidence.

3. Send one small probe. This makes a real provider API request:

~~~powershell
$claudeBody = @{
    model = $claudeModel
    stream = $false
    max_tokens = 512
    messages = @(@{ role = 'user'; content = 'Reply with exactly READY.' })
} | ConvertTo-Json -Depth 6

$claudeResponse = Invoke-RestMethod -Uri 'https://api.anthropic.com/v1/chat/completions' -Method Post -ContentType 'application/json' -Headers @{ Authorization = "Bearer $env:ANTHROPIC_API_KEY" } -Body $claudeBody -TimeoutSec 90
$claudeText = [string]$claudeResponse.choices[0].message.content
[pscustomobject]@{
    Model = $claudeResponse.model
    FinishReason = $claudeResponse.choices[0].finish_reason
    ExactReady = ($claudeText.Trim() -eq 'READY')
}
~~~

If authentication or model access fails, resolve that before changing GMS. A
length termination is not a complete response. Thinking models may need a
larger budget/provider-side settings; this probe's max_tokens value is not a
persistent GMS model option. The main-agent adapter currently omits a fixed
temperature; classifier calls have separate NeMo options and short budgets.

Claude's compatibility layer supports text/tool fields but ignores some fields,
including response_format and strict function-schema mode. GMS still validates
tool arguments and authoring drafts locally, but do not treat that endpoint as
native structured-output support. Evaluate the main-agent path first; leave
policy authoring and guardrails on their working configurations initially.

## 3. Start The GMS Backend And Frontend

Only continue when the intended rehearsal/local database is reachable and
prepared, and you have an existing normal system-admin management account.
Starting scripts/run_api.py invokes prototype table creation on the configured
database, so choose the intended target deliberately; do not use production
as a connectivity probe. This walkthrough does not require a new schema change.

1. Stop the previous local API with Ctrl+C in its terminal. In the terminal with
any session-only Claude key, start the API from the repository root:

~~~powershell
.\.venv\Scripts\python.exe -B scripts/run_api.py
~~~

2. In a separate terminal, start the frontend from the repository root:

~~~powershell
$env:NEXT_PUBLIC_API_BASE_URL = '/api/gms'
$env:GMS_API_BASE_URL = 'http://127.0.0.1:8000'
npm.cmd --prefix frontend run dev
~~~

The local frontend uses its same-origin /api/gms proxy to the backend on 8000.
The production frontend listens on port 80; the backend remains private on 8000. Open http://127.0.0.1:3000/login
and sign in as a system administrator. Finish any required password setup first.
If startup fails because PostgreSQL is unreachable, the provider probe can still
be completed independently, but management/runtime switching must wait.

## 4. Create A Profile In GMS

1. Sign in as a linked developer or administrator. Open Apps -> your app ->
   Models and record the current selections for rollback.
2. Click the single Add model profile button at the right of Save model selections.
   API Type is the first field for both roles. The default fields are:

| Field | Claude example | Ollama example |
| --- | --- | --- |
| API Type | Compatible API / Model Gateway | Compatible API / Model Gateway |
| Profile Name | Claude main test v1 | Ollama Qwen main test v1 |
| Model / Gateway Alias | Your exact tested Claude model ID | Your installed tested model, e.g. qwen2.5:1.5b |
| API Base URL | https://api.anthropic.com/v1 | http://127.0.0.1:11434/v1 |
| Provider API key | Actual Claude key, entered privately | ollama-local-placeholder, only for deliberate local no-auth |

3. Click Add model profile. This app-owned path encrypts the key and immediately
   creates main-only access for the app. Select the new Main agent and click
   Save model selections. Keep the working Guardrail classifier unchanged.
   Creating a profile does not test its connection or automatically select it.

Administrators using an existing backend key instead expand Advanced credentials
and check Use a backend-managed credential in the same form. In that mode,
Credential Environment Variable replaces Provider API key: enter ANTHROPIC_API_KEY
or OLLAMA_LOCAL_KEY as a NAME only, without a value or env: prefix. Those variables
must be privately provisioned/approved on the backend first. Click Add model
profile, explicitly Approve access for the intended app/purpose, then select/save.
Only this admin-managed mode can provision a classifier; owned models are main-only
even for administrators. Developers do not see Advanced credentials or grants.

Profile names are unique. There is no profile edit/delete API: use a new versioned
profile for a changed endpoint/model/key bundle and verify it before switching.
An unavailable classifier needs an admin to restore a valid existing grant/choice;
do not turn off rails or grant every profile. Selection changes do not need a
restart; backend environment/approval changes do.

For exact payloads and both registration routes, see
[Common Steps C](supported-llm-setup-guide.md#common-steps-c-register-approve-and-select-the-profile).

## 5. Verify The Real GMS Flow

Open Runtime Test for that app. Enter the existing app API key in App API Key,
set a fresh Conversation ID for each independent test (for example
claude-main-test-1 or ollama-main-test-1), and enter this Message:
Use GitHub MCP to list branches in octocat/Hello-World. Click Run Guardrails.
If your rehearsal policies restrict that repository or action, use an explicitly
permitted repository/read instead. The app must have enabled GitHub connector
access, a working backend PAT, enforceable policies, both model grants and a
working guardrail model. Local source MCP runs also require its Docker launcher.

Confirm that a real read tool ran and its result was used. A plausible response
without tool execution does not prove model tool compatibility. Check existing
runtime logs/metadata and the provider's model/deployment records where needed.
Run one matching block test from the app's actual policies and confirm it stays
blocked; do not invoke GitHub writes for this model-switch test.

The runtime endpoint is POST /v1/guardrails/run. It uses the app client_id in
X-App-ID and the app's existing API key in X-API-Key. Management JWTs, model keys
and registry/database passwords are different credentials. The UI Runtime Test
sends the app credentials you enter; management login alone does not supply its
API key. Use the existing key you already hold. A lost key needs a deliberate
rotation coordinated with its app consumers, not a rotation just to switch models.
API automation details are in llm-provider-guide.md.

Provider-only probes do not run GMS policies. The new offline suite validates
integration with synthetic responses; it does not certify your live model.

## 6. Switch Again Or Roll Back

Once both profiles are created and approved for main use, changing between them
is: Apps -> your app -> Models -> Main agent -> choose profile -> Save model
selections -> run a fresh Runtime Test. No Python changes or restart is needed
for that stored selection change. Keep old grants until rollback is verified.

Restore the previous approved main selection to roll back. A previous Azure
environment default requires its explicit main/default grant. Revoke unwanted
new grants separately after switching away; revocation alone does not select a
replacement model. Do not rotate the app API key or rewrite policies to switch.

To test a different guardrail model later, separately approve that profile for
Guardrail classifier, select it as an administrator, and test both input and
output rails, safe/blocked prompts, secrets, malformed/truncated responses and
failure handling. NeMo sends short yes/no budgets and model options. Current
thinking-capable models or newer Claude parameter constraints may not satisfy
those calls directly; a gateway can map supported options, but real classifier
quality still needs evaluation. Do not copy a successful main-agent result as
proof that guardrail or policy-authoring roles work.

## Troubleshooting

| Symptom | First check |
| --- | --- |
| GMS will not start / management cannot log in | Intended PostgreSQL target, schema and management account; provider probes are independent |
| Profile creation says not approved | Correct compatible base-URL list, exact path/port, credential-name list, one definition per env setting, backend restart |
| Claude 401/403 | Claude API key, account/model/workspace access; keys requiring a workspace header need supported routing |
| Claude 404 | Exact available model ID and /v1/chat/completions endpoint; not an Azure deployment or prefixed gateway model |
| Ollama connection refused | Ollama app/server running, /api/tags reachable from the backend host |
| Direct probe works but GMS times out | Warm/CPU latency, full tool-context size, 60-second model request / 120-second runtime budgets |
| Claude or Ollama not in Main agent dropdown | Explicit main-purpose approval for this app and currently valid profile metadata |
| Model metadata saves but /run fails | Both purpose grants, existing Azure guardrail settings when selected, connector/PAT/Docker, policies and actual model capabilities |
| Guardrail returns 503 | Classifier must finish with exactly yes/no; inspect completion/parameter compatibility, do not disable validation |
| Switching main does not change Create Policy AI | Authoring has its own backend GMS_POLICY_AI_* profile; app selection does not change it |

These URL examples assume backend and Ollama run directly on the same Windows
host. A container/ACI backend has a different localhost. The current adapter
allows plain HTTP only for explicitly approved literal loopback addresses;
host.docker.internal over HTTP is not accepted. Use an approved HTTPS service
when crossing that boundary; see model-gateway-integration.md.

## References And Evidence

Primary documentation checked on 2026-10-20:

- [Claude compatible API, headers and feature limits](https://platform.claude.com/docs/en/cli-sdks-libraries/libraries/openai-sdk)
- [Claude model IDs/access](https://platform.claude.com/docs/en/models/overview)
- [Ollama compatible endpoint](https://docs.ollama.com/api/openai-compatibility)
- [Ollama Windows service](https://docs.ollama.com/windows)
- [Ollama thinking controls](https://docs.ollama.com/capabilities/thinking)
- [Installed Qwen3 4B model metadata](https://ollama.com/library/qwen3:4b)
- [Optional Qwen2.5 1.5B model metadata](https://ollama.com/library/qwen2.5:1.5b)

UI fields and request schemas were checked against current source. Configuration
examples are verified without resolving real secrets or connecting to services.
No live Claude/Ollama GMS success is claimed by this document.
