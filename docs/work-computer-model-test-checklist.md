# Work Computer Model-Test Checklist — 22 October 2026

Prepared on 21 October 2026. For the combined work session, first resume the
[paused online security/optimization checks](work-computer-security-test-checklist.md),
then use this model-switch checklist. Neither checklist starts a production
deployment or new classifier integration.

## What Today Established

| Area | Evidence / status |
| --- | --- |
| Local main agent | Qwen2.5 1.5B through Ollama worked in GMS with actual GitHub MCP branch-list calls and both rails passing |
| Azure/Ollama switching | User reported the switch-back test passed; successful tool calls were verified, but audit events do not independently retain historical model identity per request |
| Input restriction | An issue-creation request was blocked by NeMo before the agent/tools ran |
| Output restriction | The branch-name word policy blocked a response containing test; removing that policy allowed the response. This demonstrated deterministic output-phrase enforcement, not independent NeMo classifier accuracy |
| Local classifier | Not accepted: Qwen2.5 1.5B passed 5/8 final smoke cases; Qwen2.5 7B passed 8/11 original-prompt cases |
| Performance versus quality | The 7B matrix completed on CPU at about 0.56–3.11 seconds per check, but made decision errors. Qwen3 follow-up probes timed out at a 45-second diagnostic limit |
| Current home selection | Qwen2.5 1.5B main agent; Azure guardrail classifier |
| Llama 3.1 8B | Download/testing postponed at the user's request; not downloaded |

The main-agent feasibility goal was demonstrated. These small test sets are
not general accuracy measurements, certification of every provider, or a
production acceptance result. A GPU can improve latency and usable model size;
it does not automatically correct a model's policy decisions.

Detailed evidence: [main-agent results](model-switch-test-results.md),
[classifier results](local-classifier-test-results.md), and
[follow-up experiments](local-classifier-next-step-review.md).

## 1. Bring The Current Source And Notes

From the repository root on each machine:

~~~powershell
git status --short
git log -1 --oneline
~~~

At preparation time, the home source commit was dbcf10e (Add LLM switch guide).
There are later modified/untracked handoff/result documents. Make sure those
reach work as well; pulling a commit does not transfer uncommitted files.
Review frontend/next-env.d.ts and frontend/tsconfig.json changes separately;
do not assume generated-file changes are required for model switching.

The approved provider integration is already applied. Do not reapply
.waylog/model-gateway-integration.patch to an updated checkout. The separate
Next.js 13 compatibility draft remains unapplied; current source uses
Next.js 16 / React 19, with Node 24 used by the images.

Keep .env, API keys, PATs, database credentials and database dumps out of Git.
Recreate dependencies on the work computer rather than copying .venv or
node_modules. The home database backup is private and is not required when
continuing against the existing work rehearsal database.

## 2. Verify The Work Environment And Offline Checks

~~~powershell
node --version
py -3.12 --version
ollama --version
ollama list
Get-CimInstance Win32_VideoController | Select-Object Name
Get-CimInstance Win32_OperatingSystem |
    Select-Object @{Name='TotalRAMGiB';Expression={[math]::Round($_.TotalVisibleMemorySize / 1MB, 2)}},
                  @{Name='FreeRAMGiB';Expression={[math]::Round($_.FreePhysicalMemory / 1MB, 2)}}
~~~

Use the Python 3.12 environment and preferably Node 24 to match the current
source/image baseline. GPU inventory is only an inventory: check ollama ps
while a model is loaded to establish what Ollama actually uses.

If dependencies need to be recreated, create .venv only if it does not already
exist, then install from the repository's requirements and lockfile:

~~~powershell
# New environment only:
py -3.12 -m venv .venv

# Existing or newly created environment:
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
npm.cmd --prefix frontend ci
~~~

Run the explicit safe regression catalogue:

~~~powershell
.\.venv\Scripts\python.exe -B scripts/run_security_checks.py
~~~

Expected current catalogue: 33 passed, 0 failed. It excludes external/manual
database, MCP and model diagnostics. Do not replace it with unrestricted test
discovery.

For clean frontend verification, from a separate terminal at the repository root:

~~~powershell
Set-Location frontend
npm.cmd run lint
npm.cmd exec -- tsc --noEmit
npm.cmd run build
~~~

Clean pinned-install/current-lint/image verification was still open on the home
machine because its installed dependencies were older. Record failures rather
than downgrading dependencies or applying the parked Next.js 13 patch.

## 3. Select And Verify The Work Rehearsal Database

| Target | How to treat it |
| --- | --- |
| Azure: guardrails-postgresql.postgres.database.azure.com:5432 / nemo_restore_check_20261016 | Existing work rehearsal continuation target |
| Same Azure host / nemo_mcp_guardrails | Production; do not use for this evaluation |
| Home: localhost:5433 / nemo_restore_check_ollama_20261020_153213 | Separate repaired home rehearsal; not automatically present at work |
| Work: 127.0.0.1:5432 / nemo_mcp_guardrails | Historical local target; previously missing password-state columns |

Do not copy the home DATABASE_URL or port 5433 into the work setup blindly.
Home app 33, model IDs 1/2 and policy IDs 5/6/7 are home-specific. Use the actual
work test app, its assignments and its existing credentials.

In the backend PowerShell terminal, follow the credential-prompt and
read-only schema-verification blocks in
[Reconnect The Home Backend To The Rehearsal Copy](work-computer-handoff.md#reconnect-the-home-backend-to-the-rehearsal-copy).
Despite that historical heading, those commands select the Azure rehearsal
above and can be used at work. Keep that terminal open: DATABASE_URL is a
session setting. Do not clear it after selecting the verified rehearsal.

Optional network check, which does not verify credentials or schema:

~~~powershell
Test-NetConnection guardrails-postgresql.postgres.database.azure.com -Port 5432
~~~

Verify the database identity, users password-state columns, app_llm_grants
table and the app's effective policy/grant state before starting runtime tests.
A successful SELECT 1 alone does not prove schema compatibility. Do not rerun
completed migrations/conversions, apply old manifests, disable legacy branch
definitions, or substitute production when a check fails.

The home policy repairs did not modify the work rehearsal database. If the work
snapshot fails validation, inspect its actual definitions and compiled rows
before proposing any repair.

## 4. Prepare Ollama And The Backend Settings

First check the local service and installed models:

~~~powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 10 |
    Select-Object -ExpandProperty models |
    Select-Object name
ollama list
~~~

If Ollama is not running, start the installed Ollama application. Alternatively,
run ollama serve in a separate terminal only when no server is already running.

For the first repeat, use the model already demonstrated as the main agent:

~~~powershell
# Run only if absent from ollama list:
ollama pull qwen2.5:1.5b
~~~

In the work backend's private .env, merge these entries into any existing
allowlists; retain other approved endpoints and credential-variable names:

~~~dotenv
GMS_ALLOWED_COMPATIBLE_LLM_ENDPOINTS=http://127.0.0.1:11434/v1
GMS_ALLOWED_LLM_CREDENTIAL_ENV_VARS=OLLAMA_LOCAL_KEY
OLLAMA_LOCAL_KEY=ollama-local-placeholder
GITHUB_MCP_READ_ONLY=1
~~~

The placeholder is the local SDK key value, not an Azure key. Retain the valid
Azure settings because Azure remains the classifier:
AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_VERSION and
AZURE_OPENAI_DEPLOYMENT. Keep the management JWT secret and connector credential
configuration available privately too.

Use direct Windows Python execution for this evaluation so 127.0.0.1 points to
the same machine as Ollama. A backend container has a different loopback
interface; do not replace the URL with unapproved host.docker.internal HTTP
or expose Ollama on all interfaces as a shortcut.

Restart the backend after changing environment settings. A stored model
selection change by itself does not require a restart.

## 5. Start GMS And Establish The Azure Baseline

In the SAME terminal where the rehearsal database was selected and verified:

~~~powershell
$env:GITHUB_MCP_READ_ONLY = '1'
.\.venv\Scripts\python.exe -B scripts/run_api.py
~~~

Direct-source GitHub MCP launch requires Docker Desktop running. This does not
mean the backend itself needs to run in Docker.

In another terminal, from the repository root:

~~~powershell
Set-Location frontend
$env:NEXT_PUBLIC_API_BASE_URL = '/api/gms'
$env:GMS_API_BASE_URL = 'http://127.0.0.1:8000'
npm.cmd run dev
~~~

Open http://localhost:3000. Sign in with an existing work management account,
complete password setup if required, and open the actual work test app.

Check its GitHub connector link, effective policy snapshot, main/guardrail
selections and separate purpose grants. Use its existing app API key in Runtime
Test; this is separate from your login, model credential and database password.
Do not regenerate it solely to test.

First run the read below with an approved Azure main model and Azure classifier.
If the baseline fails, resolve the work environment/policy issue before blaming
the local model.

## 6. Select Ollama For The Main Agent And Repeat The Read

Apps → chosen app → Models → Add model profile:

| Field | Value |
| --- | --- |
| API Type | Compatible API / Model Gateway |
| Configuration Name | Ollama Qwen2.5 1.5B main work test v1 |
| Model / Gateway Alias | qwen2.5:1.5b |
| API Base URL | http://127.0.0.1:11434/v1 |
| Credential Environment Variable | OLLAMA_LOCAL_KEY |

Enter only the environment variable NAME in that final field. If an equivalent
valid work profile already exists, reuse it.

As an administrator, approve this profile for this app's Main agent purpose.
Select it in the Main agent dropdown, leave the approved Azure Guardrail
classifier selected, and save. The Azure main default needs its own main-purpose
grant for the later switch-back test; a guardrail grant alone does not cover it.

In Runtime Test, use a fresh conversation ID, such as
work-ollama-read-20261022-1, and send:

> Use GitHub MCP to list branches in octocat/Hello-World.

Check all of the following:

- Input rail passed.
- The actual GitHub list_branches tool started and returned.
- Output rail passed, unless an active output policy legitimately blocks the returned content.
- The final response agrees with the tool result.
- Elapsed time and any timeout/error stage are recorded.

Repeat three independent reads with new conversation IDs to check repeatability.
Use ollama ps during a run to record actual CPU/GPU use.

Then select the approved Azure main model, repeat the same read with a new
conversation ID, and switch back to Ollama for one final read. Keep the classifier,
connector and policies fixed so the comparison changes only the main profile.
Do not disable a policy just to make a comparison pass.

Today's input-block and branch-name output-word tests are already documented;
there is no need to recreate the deleted word-ban policy just to repeat them.
If checking an existing issue-title restriction at work, verify that policy is
actually assigned, retain read-only mode and inspect the input block stage.
A model refusal or absence of a write tool does not independently prove that
the input policy blocked the request.

## 7. Treat A Local Classifier As Separate Follow-Up Work

This is optional after the main-agent handoff, not a requirement to establish
that another provider works. Keep Azure selected for classification meanwhile.

Read the existing classifier matrices before choosing another experiment.
Preserve exact conditions in BOTH NeMo and the tool guard, as requested.
Keep strict complete yes/no validation and fail-closed behavior. Selective
branch merging remains unavailable; no real merge tests are needed here.

If classifier work resumes, first reproduce the unchanged-prompt matrix using
the work app's policy snapshot in an isolated, provider-aware NeMo test with no
MCP tools. Include restricted/exempt branch routes, exact versus other issue
titles, safe reads, synthetic credential outputs, safe refusals and adversarial
wording. Record semantic errors separately from format errors and timeouts.
Do not grant/select a candidate as the active classifier merely because it
answers yes/no or passes the original examples.

The earlier local-classifier runs were isolated experiments; there is not yet a
committed reusable provider-aware classifier runner. Existing
scripts/debug_nemo_self_check.py and scripts/debug_nemo_output_check.py explicitly
construct Azure models and do not validate the app's selected Ollama classifier.
Any reusable harness or prompt/source change needs its exact diff reviewed
before application.

Llama 3.1 8B downloading/testing is on hold. Nothing in this checklist
authorizes starting it automatically at work.

## Evidence To Record Tomorrow

Record the source commit, dependency-check results, verified rehearsal database
name, work app identity, exact main/classifier profile labels and aliases,
Ollama version, actual CPU/GPU use, fresh conversation ID, outcome, tool
invocation/result, block stage where applicable and elapsed time. Do not record
keys, passwords, full credential-bearing URLs or real secret output.

A successful handoff result is: the work Azure baseline and Ollama-main reads
both execute the real read tool, Azure/Ollama switching works, and enforced
policies remain effective. Other vendors, policy authoring, a fully local
classifier and production rollout remain separate acceptance work.
