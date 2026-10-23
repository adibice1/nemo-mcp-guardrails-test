# Work/Home Computer Handoff

## Final working-day priority and fresh deployment - 23 October 2026

Start with [the latest release/handoff plan](final-workday-handoff-2026-10-23.md).
The user confirmed an existing deployed service and wants its second deployment
with a fresh database, not legacy apps/data. Supervisor takes over GMS/admin,
release, secret/key and recovery ownership; initial admin email/username is
admin@gmail.com. User has a backup to transfer privately and permits release
with the recorded dependency findings. Both local release images are ready;
fresh-start rehearsal passes. Actual registry/Azure authentication is unavailable
on this home setup, so nothing was published/redeployed or provisioned online.

At work, capture actual Azure resource/image/database identities, create/bootstrap
the fresh target, complete supervisor first login, publish/deploy the verified
pair, check the actual release and confirm private backup/key/access handover.
Direct home SQL access times out at TCP, but the supplied deployed URL and its
proxy DB health are reachable. Do not substitute keys, clear the old DB or apply
the superseded policy-210 plan. The supplied SE-EDU templates are now applied to
[UserGuide.md](UserGuide.md) and [DeveloperGuide.md](DeveloperGuide.md); review
them with the supervisor and final deployed configuration.

## Current continuation point - 22 October 2026, after presentation

For the laptop, use the [concise 22 October home handover](home-handoff-2026-10-22.md).
It distinguishes home-local work from Azure-only follow-ups and preserves the
separate home/work database and encryption-key settings.

Start with [post-presentation results and the complete test map](post-presentation-verification-2026-10-22.md)
and [the updated deployment checklist](deployment-checklist-2026-10-22.md).
This checkpoint supersedes historical pending items below. Azure work access
was supplied privately for Test app 3, then the temporary access file was removed.
No secrets belong in this handoff or Git.

- Verified actual target: guardrails-postgresql.postgres.database.azure.com /
  nemo_restore_check_20261016. Root .env still has a local database default;
  preserve the verified process override when restarting. Never infer target
  identity from a healthy login alone.
- Work venv now uses approved aiohttp 3.14.5, certifi 2026.10.19 and yarl 1.25.1;
  all 120 constraints match, pip check passes, all 38 offline checks pass and a
  subsequent real proxy Azure/native-MCP read passes with all stages/tool events.
- App 221 retains Azure defaults for both roles and its existing grants,
  including the unused Qwen classifier grant explicitly retained by the user.
  Fixed-model timings, real tool events, no-tool status, existing input blocks
  without tool execution and management audit persistence are now verified.
- Authorized repair: app 214 assignment 190 now references supported policy 212,
  preserving its ID/label/enabled state. Definitions/compiled rows unchanged;
  exact snapshot and six matcher cases pass. This approved reuse replaces the
  earlier proposed in-place repair of 210. Full app 214 HTTP acceptance needs its
  existing app key or a manual Runtime Test if that app is in release scope.
- All six authorized rehearsal apps' policy snapshots validate. App 208 lacks
  usable selected-default-model grants; app 222 selects Qwen for classification,
  which earlier quality matrices did not accept. Their release intent needs a
  decision; no automatic grant/selection changes were made.
- Backend restarted hidden after the approved installation: PID 31988,
  127.0.0.1:8000, rehearsal target, GITHUB_MCP_READ_ONLY=1. Frontend preserved.
  Output: .waylog/post-presentation-20261022/backend-after-update.log. Verify PID
  ownership before stopping it to restart under a terminal. Health/DB health pass.
- The saved root .env encryption key is preserved. Six synthetic key checks
  pass; no owned profiles currently exist in the rehearsal. Private key backup
  remains an operational requirement; do not regenerate a key to repeat a test.

Home can continue source/docs/local synthetic verification; it still cannot
complete the actual Azure-specific optional follow-ups without connectivity.
Remaining production groups: exact target schema/configuration, actual target
backup/key recovery/rollback and deployed image-pair acceptance. They require
the intended target, release/recovery owners and authorized access. Browser
rendering can be checked manually if the presentation did not already cover it;
automated proxy timing and backend persistence are complete. No repeat of the
whole browser/model/PR suite is requested. Known Pillow/FastEmbed and development
braces findings remain open; no production deployment/security clearance is claimed.

No application source was edited or committed/pushed in this testing session.
Transfer the updated docs through the normal Git workflow before switching PCs.

## Historical presentation workflow prepared - 22 October 2026

The user deferred remaining tests and requested a live-demo workflow. Start with
[the plain-text Notepad runbook](live-demo-2026-10-22.txt). They confirmed the
repository adibice1/nemo-mcp-guardrails-test. The agent created only two requested
text fixtures: development commit 21ffd61962aa72f3b6d933551d5740cc510e6690 and
staging commit 7bb188076f440d00774e6bb6bf7051ebe2f4ce81. Remote reads and compare
results independently confirm them; staging has one unique commit relative to
production, development has four. Main/production stayed unchanged; no PR or
merge was created. The GitHub integration returned 403; the authorized file
creation used the project's existing credential privately, without changing its
permissions. No GitHub MCP mode, database, user, app or model selection changed
as part of this preparation. Remaining tests are deferred, not passed.

Qwen qwen2.5:1.5b is installed; local Ollama catalogue and root endpoint approval
were checked. The runbook provides only its local non-secret placeholder and
credential variable names, never real keys. It explicitly explains selective
merging still fails closed and includes temporary write-mode/cleanup commands
for the user to run during the authorized presentation.

## Work schema preflight - 22 October 2026

The first DBeaver column query returned zero rows. After migration instructions,
the user supplied passing schema results: owner_app_id integer nullable and
encrypted_api_key text nullable; fk_llm_configs_owner_app references apps(id)
ON DELETE CASCADE; ck_llm_configs_owned_credential enforces the two credential
modes; ix_llm_configs_owner_app_id is a btree owner index. Record the work
rehearsal owned-model schema as user-verified, not pending. The recorded target
is nemo_restore_check_20261016; no production migration is claimed and the agent
did not execute the migration. Do not rerun it just to repeat completed checks.

The user's backend probe reported `Encryption key: missing`; their rehearsal
query then confirmed zero rows with encrypted_api_key IS NOT NULL. The agent
provisioned a separate work-rehearsal Fernet key directly into the existing
private .env, first checking that it is Git-ignored and untracked. Persistence
and key format were verified without printing the value; other dotenv settings
were verified unchanged. No database, home key or production setting changed.
Private key backup remains the user's operational step; format verification
does not establish production recovery or live owned-model decryption.

The user then confirmed login works after the instructed backend restart.
Agent HTTP probes returned 200 for /health and /health/db. These probes establish
liveness/reachability, not independent database identity or owned-model decryption.
The initial direct-API frontend configuration caused /api/gms/health to return
503; instructions then set process variables NEXT_PUBLIC_API_BASE_URL=/api/gms
and GMS_API_BASE_URL=http://127.0.0.1:8000. Subsequent agent probes now return
HTTP 200/status ok for both /api/gms/health and /api/gms/health/db. The user
reported the instructed safe branch read passed Input, Tool guard and Output
and returned development, feat/add-user-management, main, production and staging.
Record successful user-reported read plus independent proxy-health evidence;
the individual request's browser route/tool trace/timing were not supplied.
Do not claim captured list_branches events solely from the passed badge.

The user subsequently confirmed the development-to-production smoke request was
blocked and appears in Traffic. Record the blocked outcome/Traffic visibility as
user-confirmed; individual stage values, block reason and event details were
not pasted. The successful read's list_branches event names remain unconfirmed.

Next collect fixed-provider cold/warm timings and actual tool-event evidence.
Keep Azure main/classifier fixed, restart only the backend once in its verified
read-only rehearsal terminal, and issue three identical safe branch reads with
fresh conversation IDs. Collect browser duration and the matching backend
gms_timing line for each /v1/guardrails/run. Server-Timing carries only total
gms duration; per-stage timings are in stages_ms/backend logs and Traffic events.
Verify actual list_branches tool.started/tool.returned events, not just badges.
Policy 210, classifier-grant review and remaining audit evidence remain pending.
Keep read-only mode and retain the saved private key.

## Heading to work: final checklist - 22 October 2026

Start with [the five-group deployment checklist](deployment-checklist-2026-10-22.md).
All requested home checks and hosted CI are complete. Remaining verification is
actual work/Azure smoke/logs/timing, affected policy/grants, target schema/config,
production recovery/rollback, and post-deployment image-pair acceptance. New
provider acceptance is conditional. Dependency findings and publication/rollout
are separate release work; this is not a production-ready declaration.

For the presentation, rehearse the intended existing app/setup once. Policy 210
needs actual repair only if app 214 is included; it is outside app 221's captured
effective set. Preserve completed browser/model/PR acceptance and read-only mode.
The new readiness/checklist docs are local changes until committed/pushed for
the work machine; source commit 5f84cffe already has successful hosted CI.

## Latest home follow-up and hosted CI - 22 October 2026

Read [the current results](home-readiness-results-2026-10-22.md). The user pushed
commit 5f84cffe; GitHub Verification passes both jobs, including 38 offline and 16
PostgreSQL diagnostics. A rebuilt local backend image passes all 38 checks and
real proxy plain/read/blocked status checks. Synthetic database/key recovery
passes; temporary resources are removed. All requested unconditional home checks
are complete. Actual Azure work-environment timing, policy 210/app 214 repair and
app 221 grant decisions still require that environment/scope. New-provider and
production-specific recovery/rollout remain separate. Do not replay completed
home/manual tests just because older sections below describe them as pending.

## Latest completed home checks - 22 October 2026

Read [the final home results](home-verification-results-2026-10-22.md) before
historical pending-test instructions. All four home groups are complete: 35
offline checks in the final pinned image, 16 PostgreSQL diagnostics, schema
idempotency/constraints and actual native-MCP image-pair reads passed. The title
block explanation is corrected and the runtime image no longer includes unused
pip. Four model setup guides and their API examples match the current form.
Work-network Azure evidence, policy 210/grant review and conditional gateway/
production work remain deferred. Transfer reviewed source/docs through the
normal private workflow; no commit/push or deployment ran in this continuation.


## Current Home Entry Point - 2026-10-21

Start with [the current home handover](home-handoff-2026-10-21.md). Home cannot
access Azure. Capture the read-only online inventory at work if possible, then
continue with home-local PostgreSQL on port 5433 or isolated offline tests.
Database capture is now complete: app 221 uses Azure defaults, its four effective
policies each have one current artifact, and policy 210 needs repair in Test App
Two (214). Review app 221's unused Qwen classifier grant. Two manual groups
remain (proxy and browser/timing/logs); source/finding/release work is separate.
PR 39 cleanup is complete, read-only restoration is user-confirmed, and no
production migration/deployment ran. Older access/setup instructions below are
historical where they conflict with this checkpoint and the acceptance record.

## Current Acceptance Checkpoint - 2026-10-21

Resume from [automated results and remaining manual tests](work-acceptance-2026-10-21.md).
Azure rehearsal identity is user-verified; Qwen is installed and selected for the
test app. Automated work now includes the full offline suite, frontend Node 24
image and real pinned MCP catalogue schemas. One legacy PostgreSQL runtime
explanation assertion and three Python dependency advisory findings remain open.
The user chose to perform the live browser checks manually after Escape stopped
Computer Use, and confirmed the Qwen-to-Azure-to-Qwen read sequence passed all
rails without a backend restart. The later user-submitted GMS write test is
recorded below; the agent did not submit a valid-key runtime request. No
production migration or deployment ran.
Policy 209 is now unassigned from all apps according to the user, with its
definition retained. Current active PR-create/merge conditions are source !=
staging AND target = production. Edit/cancel and both input-condition cases are
user-confirmed. Draft PR 39 development -> staging was created and independently
verified; the GitHub connection's cleanup returned 403. Cleanup then succeeded
with the project's existing credential: PR 39 is closed/unmerged. The user
confirmed read-only restoration. Do not repeat creation or reattach 209.
Scoped automated work and subsequent database capture are finished. Review the
policy 210 finding and unused Qwen classifier grant recorded in the home entry
point. Remaining manual evidence is local proxy alignment and browser/timing/log
checks; the acceptance record keeps source/advisory fixes separate.

## Earlier User Acceptance And Pending Access - 2026-10-21 (Historical)

The user confirms login, corrected AI drafts and all supplied injection previews
work; developers can select main models and cannot change the app classifier.
The developer Add model action is missing because creation remains admin-only.
The user clarified that developers must add/use their own main-agent models;
only classifier controls remain admin-only and per app. The registration flow
still needs an app-scoped credential/destination design and exact code preview.
Read the
[latest follow-up](policy-authoring-and-global-classifier-review.md#developer-model-registration-follow-up)
for auth needs, verified existing repository branches and the remaining test gaps.
No connected browser session is exposed to the agent; user sign-in alone does not
provide agent API/browser authentication. No PR test or production database move
has run. Keep release/cutover deferred until the remaining work is complete.

Current read-only runtime inspection supersedes the older local-backend diagnosis
below: the backend now has an Azure PostgreSQL socket, but the actual database
name is unverified. Do not infer it from root .env or DBeaver. Ollama is already
running locally; qwen2.5:1.5b has not been downloaded on this machine. Follow
[runtime verification, browser access and Ollama setup](work-runtime-access-and-ollama.md)
before live acceptance. No database or secret configuration was changed by these
checks.

## Earlier Request Before Manual Rehearsal - 2026-10-21 (Historical)

Read the [policy-authoring/global-classifier review](policy-authoring-and-global-classifier-review.md)
before the planned 22 October checklists. The user requested correcting inverted
AI branch drafts, then chose to KEEP admin-only per-app classifiers and Next.js 16.
The earlier global classifier proposal is withdrawn without implementation;
existing per-app permissions already implement the chosen model-access split.
No classifier scope migration is planned. The user approved the exact authoring
fix; all three files match the review and all 33 normal offline checks passed
after application. It compiles structured branch intent and derives consistent
wording/examples, rejecting conflicting or missing branch intent. Restart the
backend before live authoring tests. Actual model understanding/injection results
are still pending. The linked review records automated results, injection prompts,
test ownership and the ordered remaining acceptance checklist.

The user's subsequent login traceback reports missing users.must_change_password.
Read-only checks confirmed that the running backend connects to local 5432,
whose users table lacks both security password-state columns. This happens before
password verification. Restore the Azure rehearsal session override before
testing existing accounts; no password reset or automatic local migration ran.
User-supplied rehearsal identities are admin@gmail.com and dev@gmail.com (roles
not yet verified there). PR tests may use adibice1/nemo-mcp-guardrails-test and
created test PRs may be closed afterward; verify actual branches/scoped access.

## Resume At Work - Security And Optimization Tests - 2026-10-22

Start with the [security/optimization continuation checklist](work-computer-security-test-checklist.md),
then the [model-switch checklist](work-computer-model-test-checklist.md). The
security source work is complete; the missing evidence is online rehearsal/UI,
controlled PR-creation enforcement, actual grants/legacy definitions and
performance measurements. Azure rehearsal login/search and the five branch
conversions were already completed; do not repeat their migrations/manifests.

The user chose to retain Next.js 16. The Next.js 13 compatibility draft remains
unapplied and its older baseline is not a current task. No production rollout is
included in this checklist; older supervisor-pending notes are superseded.

## Work Model-Test Handoff - 2026-10-22

Follow the [work-computer model-test checklist](work-computer-model-test-checklist.md)
for the current provider-switch evaluation. Local main-agent use and real GitHub
reads have been demonstrated; local classifier candidates have not passed.
Further classifier work and the Llama download are postponed at the user's request.
Keep Azure classification selected and preserve exact NeMo/tool conditions.
Home database settings and IDs must not be assumed to exist at work.

## Home Local Testing Override - 2026-10-20

For the current home Ollama evaluation, root `.env` now targets the restored
local `nemo_restore_check_ollama_20261020_153213` database on localhost:5433.
Three user-reviewed legacy policies were repaired there, preserving IDs and
assignments; the four-policy app snapshot and both model grants validate. The
original home database and Azure targets were not changed. This local copy is
separate from the Azure rehearsal target below. Restart the backend to load the
new `.env` target and clear a terminal DATABASE_URL override if present. See
[repair evidence](testing-notes.md#local-ollama-policy-repair-completed---2026-10-20).


## Resume Here At Home - 2026-10-16

Historical checkpoint: use the [21 October home handover](home-handoff-2026-10-21.md)
for current home work; its local-database instructions supersede this section's
Azure continuation steps. At the time, this section superseded older notes. Read
the [single backlog](open-work-backlog.md) and [019 behavior/limitations](branch-routing-patch-019.md)
next. Patches 010-018 and the 019 source work are implemented; do not restart
historical 009 subdivisions or the old "010 next" sequence. The user approved
the five-file plain-English UI follow-up, which is applied and checked.

### Files And Configuration To Bring

At this handoff's start the working tree was clean at commit `4268d90`
(`!8 patches of security and code optimization`); the new source files and
plain-English formatter are tracked there. Remote/push availability was not
checked. This handoff update itself is a later working-tree change: ensure it
also reaches home. Confirm the source revision and files after transferring;
do not assume a Git pull includes changes that have not been pushed.

Keep real `.env` values, the GitHub token, app API key, database credentials and
backup archives out of Git. Arrange private access to the required credentials
at home. `.waylog/branch-conversion-review.json` and
`.waylog/llm-grants-rehearsal.json` are ignored local review files, so Git does
not transfer them. Keep them privately if needed as review records. Do not
replay an old conversion manifest; the converted records have changed.
Recreate the virtual environment and node_modules for the home machine rather
than copying generated dependencies. The current requirements.txt includes
constraints.txt automatically; use the committed frontend lockfile with npm ci.

### Database Targets And Completed Rehearsal Work

| Target | Host / port | Status |
| --- | --- | --- |
| Azure rehearsal | guardrails-postgresql.postgres.database.azure.com:5432 / nemo_restore_check_20261016 | Current continuation target; restored copy, not production |
| Azure production | Same Azure host:5432 / nemo_mcp_guardrails | No production migration, conversion or cutover performed in this session |
| Work local | 127.0.0.1:5432 / nemo_mcp_guardrails | Work .env target; missing the two security password-state columns when diagnosed |
| Home local | localhost:5433 / nemo_mcp_guardrails | Separate local Docker database; use 5433 only for local host access, not Azure |

The user completed the following on the Azure rehearsal copy:

- Created a PostgreSQL custom-format backup with PostgreSQL 18.6 tools after
  pg_dump 17 failed against server 18.6. Restored it into the rehearsal database.
  Restore screenshots showed system-catalog ACL warnings; the user reported
  matching application-table row counts. Full restore-log/error review is not
  documented, so row counts alone are not a complete recovery certification.
- Applied migrate_security_foundation.py --apply successfully, adding the
  password-state columns and conversation-tail index while preserving accounts.
- Applied migrate_app_llm_grants.py --apply-schema. The reviewed grant preview
  approved Test App (app 4) main and guardrail defaults only: two new grants,
  four unapproved entries. The apply output was not supplied; later successful
  runtime is evidence of working access for Test App, not a complete grant audit.
- Applied the reviewed branch conversion for policies 181, 182, 192, 193 and 209.
  SQL results showed all five still enabled with one enabled/current compiled
  row each. IDs, assignment scopes and names were retained.

| Policies | Intended condition in plain English |
| --- | --- |
| 181 and global 209 | Source is not development, and target is staging |
| 182 | Target is main |
| 192 and 193 | Source is not staging, and target is production |

The UI now renders these conditions in English in summaries, branch editing and
AI draft previews. Exact versioned comparisons remain in storage for enforcement.
Do not undo the conversion, disable these policies or restore unsupported prose
as a workaround for presentation. User confirmation of the refreshed UI layout
and edit/cancel behavior is still pending.

### Reconnect The Home Backend To The Rehearsal Copy

The work backend initially returned login HTTP 500 because it used local
127.0.0.1:5432, whose users table lacked the new columns. After restarting from
the PowerShell session with the Azure rehearsal override, the user confirmed
login worked. Health/db only checks SELECT 1 and did not detect that mismatch.

DATABASE_URL overrides belong to one PowerShell session. They do not travel
with Git or survive in a new terminal. Keep each machine's local .env database
setting; recreate the rehearsal override explicitly. From the home repository
root, with dependencies installed, obtain credentials through a local prompt:

```powershell
$rehearsalCredential = Get-Credential -UserName "guardrailsadmin" -Message "Azure rehearsal database credentials"
try {
    $env:GMS_REHEARSAL_DB_USER = $rehearsalCredential.UserName
    $env:GMS_REHEARSAL_DB_PASSWORD = $rehearsalCredential.GetNetworkCredential().Password
    $rehearsalDatabaseUrl = @'
import os
from sqlalchemy.engine import URL
print(URL.create(
    "postgresql+psycopg",
    username=os.environ["GMS_REHEARSAL_DB_USER"],
    password=os.environ["GMS_REHEARSAL_DB_PASSWORD"],
    host="guardrails-postgresql.postgres.database.azure.com",
    port=5432,
    database="nemo_restore_check_20261016",
    query={"sslmode": "require", "connect_timeout": "15"},
).render_as_string(hide_password=False))
'@ | .\.venv\Scripts\python.exe -B -
    if ($LASTEXITCODE -ne 0) { throw "Could not construct rehearsal connection setting." }
    $env:DATABASE_URL = $rehearsalDatabaseUrl
} finally {
    Remove-Item Env:GMS_REHEARSAL_DB_USER, Env:GMS_REHEARSAL_DB_PASSWORD -ErrorAction SilentlyContinue
    Remove-Variable rehearsalCredential, rehearsalDatabaseUrl -ErrorAction SilentlyContinue
}
```

The URL output is captured, not displayed. Never echo DATABASE_URL. Verify the
actual connection and schema without importing the src package or printing secrets:

```powershell
@'
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
load_dotenv(".env")
url = make_url(os.environ["DATABASE_URL"])
assert url.host == "guardrails-postgresql.postgres.database.azure.com", "Wrong server"
assert url.database == "nemo_restore_check_20261016", "Wrong database"
engine = create_engine(url)
try:
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT current_database()")) == "nemo_restore_check_20261016"
        columns = {column["name"] for column in inspect(connection).get_columns("users")}
        assert {"must_change_password", "temporary_password_expires_at"} <= columns
    print("Verified Azure rehearsal database and password-state columns.")
except Exception as error:
    print("Verification failed:", type(error).__name__)
    raise SystemExit(1) from None
finally:
    engine.dispose()
'@ | .\.venv\Scripts\python.exe -B -
```

If verification fails, resolve credentials, TLS/network/firewall access or schema
before starting the backend. Do not substitute production to get past the check.
Home public-IP access to Azure has not been verified. See the
[online connection guide](home-online-database.md) for network context.

After successful verification, start in that same terminal:

```powershell
$env:GITHUB_MCP_READ_ONLY = "1"
.\.venv\Scripts\python.exe -B scripts/run_api.py
```

Start the frontend in a second terminal from the home repository root:

```powershell
Set-Location frontend
$env:NEXT_PUBLIC_API_BASE_URL = "/api/gms"
$env:GMS_API_BASE_URL = "http://127.0.0.1:8000"
npm.cmd run dev
```

Open http://localhost:3000 and sign in again. The backend also needs the local
Azure OpenAI/GitHub settings and a valid GMS_JWT_SECRET from private configuration.
Direct source execution defaults to the Docker MCP launcher, so Docker must be
available. Compose's backend explicitly selects its own local postgres service;
use the direct Python launcher above for this rehearsal.

### Observed Browser Results And Immediate Next Tests

The user confirmed login after fixing the database target. A Test App runtime
search for octocat/Hello-World passed input, tool guard and output, with an actual
search_repositories call/result in the trace. Screenshots then showed an input
block for one branch-test request, and another request passing rails but receiving
the agent's read-only refusal. The branch prompts and policy attribution are not
visible in those screenshots. Neither demonstrates a write tool invocation or
independent execution-level branch enforcement. History used was 32 turns.

Continue in the order tracked in the backlog:

1. Confirm the English summary and structured editor for policy 209; edit/cancel
   must preserve its source-not-development and target-staging condition.
2. Test invalid app API credentials: expect 401 before models/tools, then restore
   the existing valid key. Do not regenerate keys just to perform the test.
3. Complete branch creation tests on a dedicated repository the user owns, using
   existing development, staging and feature/test branches and a fresh conversation
   ID for each independent case. Source feature/test into staging should be
   blocked by global policy 209; development into staging should not match 209.
   Record the input/tool stage, policy attribution, tool trace and actual repository
   result. A matching input block does not prove the execution-level guard ran.
4. Review remaining unsupported legacy definitions and actual LLM grants before
   full recompilation/production planning. Do not repeat already-completed schema
   or branch conversion operations merely because older notes list them.

The user explicitly requested enabling writes for manual testing. Instructions
were supplied to stop the backend, set GITHUB_MCP_READ_ONLY=0 in its verified
rehearsal terminal and restart it. Completion of that restart and a real write
have NOT been confirmed. Use mode 0 only for the requested controlled manual
test with a suitable existing token/repository; restart with mode 1 afterward.
Do not change the committed default or broaden token permissions automatically.
A rehearsal database does not sandbox GitHub: write tools can affect real repos.
Do not test writes against octocat/Hello-World. Change the Runtime Test conversation
ID from frontend-demo-1 to avoid earlier read-only responses influencing the test.

Selective branch merging remains unavailable. Matching trusted PR metadata blocks;
other branch-conditional merges fail closed because the pinned connector cannot
atomically enforce the target branch. Do not bypass this refusal or claim that
head-SHA checks alone fix it. Production cutover, production data changes, image
publication and deployment remain outstanding and require a concrete reviewed
rollout; --apply-rehearsal deliberately refuses production database names.

Latest local verification: the approved English UI follow-up passed the existing
branch-editor script, whole-project TypeScript, full lint and diff whitespace
checks. Earlier 019 Windows/Linux offline checks, images and disposable PostgreSQL
18.6 results are in [019 verification](branch-routing-patch-019.md#verification).
Those image builds precede the English UI follow-up; rebuild the frontend release
image before a future release. Earlier dated sections below are historical records.

## Patches 010-018 Implemented - 2026-10-16

Continue from the [completion report](security-run-2026-10-16.md), not historical
"next patch" entries. Current source uses Next 16.4.2/React 19.3.1, digest-pinned
Node 24, bounded management throttling, expiring setup-only passwords, bounded
runtime input/history, targeted membership backfills and the reduced/patched
Python dependency closure. The safe regression entry point is
`python scripts/run_security_checks.py`.

Before deploying the new API, separately review/apply
`python scripts/migrate_security_foundation.py --apply` against the intended
PostgreSQL database. Without `--apply`, the helper prints the plan without
connecting. It adds the two password-state columns and history-tail index, keeps
existing passwords, and does not grant memberships or repair policies. Management
users must sign in again after this release. Matching frontend deployment provides
`/setup-password`. No live rollout, migration, publish or deployment ran here.
Known development-tool upstream findings and real-service/browser verification
remain listed in the completion report.
## Patch 009 Source Work Complete; Patch 010 Next - 2026-10-15

009c3b, the final planned source slice of 009, is approved and applied unchanged:
four frontend files, 60 insertions/61 deletions. It aligns samples, mock
options, API resource-field types and modal help/submission availability with the
backend capability contract. Unsupported source/target/negation examples return
clarification with no draft. Existing selector text and payload/edit/summary
paths are preserved. No extra 009 subdivision or test framework is planned.

Whole-project saved-source TypeScript, scoped Next lint, focused extracted-function
sample/submission/edit checks, backend sample/mock contract checks and three
existing offline HTTP diagnostics passed. All four saved files match approved
drafts exactly; unchanged patch SHA256, reverse-patch and whitespace checks passed.
Browser inventory is empty; there is
no visual/browser-event verification. No real environment, live database/AI/MCP,
package installation, migration, resync, server restart or deployment ran. Exact
approved code preview remains in chat only. Patch 009 source implementation and
offline verification are complete; continue with 010-018. Keep real PostgreSQL/catalogue/model
quality, browser and reviewed legacy repair/resync checks open for rollout.

## Applied Assistant/Options Validation - 2026-10-15

009c3 is split into 009c3a backend assistant/options validation and 009c3b frontend
examples/help/round-trip closure. The 009c3a five-file diff is approved and applied
unchanged; all seven saved-source offline diagnostics passed. It canonicalizes primary/related selectors through the storage gate,
returns clarification with no drafts for unsupported conditions or changed
related scope, and filters options to enabled supported writes with additive
`condition_fields`. Empty field lists mean broad scope only. Cross-connector
metadata mismatches are excluded. Output drafting stays separate.

All five saved Python files parsed and matched approved drafts exactly; unchanged
patch SHA256, reverse-patch and whitespace checks passed. No real
environment, live database/AI/MCP, migration, resync, restart or deployment ran.
Contract-valid AI output still requires human intent review; live model quality
is unverified. The complete approved code preview remains in chat only; every
later non-doc patch still requires its own preview and approval. 009c3b now
completes frontend source work above; rollout checks remain open. Follow the
single backlog; patch 010 is next.

## Applied Runtime Policy Integration - 2026-10-15

009c2c's fourteen-file diff is approved and applied unchanged. It uses
one validated policy snapshot for rails, tools, attribution and output phrases;
checks exact contents on cold/warm/lock/build/cache-disabled paths; connects the
reviewed catalogue and field/method matcher; and distinguishes tool policy matches
from evaluation failures. Standalone DB loaders and conditional wrappers cannot
fall back to legacy scalar matching. The full runner receives catalogue filtering
while retaining read-only mode.

The new authenticated HTTP diagnostic and eighteen existing offline diagnostics
passed against saved source; all fourteen Python files parsed and matched the
approved drafts exactly. Approved-patch reverse verification, unchanged patch
SHA256 and whitespace checks passed. Tests use in-memory SQLite and fake
external boundaries. The new HTTP fixture exercises actual coordination and
history persistence, including empty scope, shared tools, stale state, exact
cache changes and controlled interleavings. It does not verify PostgreSQL
concurrency, actual server compatibility or model quality. The full runner was
parsed only; no real environment, live DB, model/MCP process, migration, resync,
restart or deployment ran. Requests already admitted may finish on their
validated snapshot after a concurrent policy change.

Snapshot/cache, catalogue filtering and field-bound enforcement are active.
009c3a/009c3b alignment and focused source closure checks are applied above;
patch 010 is next.
Before rollout, explicitly review/repair legacy conditions and resync changed
compiled rows through the admin path. Every later non-doc diff still needs full
chat preview and approval; no code previews are stored in docs.

## GitHub Tool Contract Foundation - 2026-10-15

009c2b's exact seven-file diff was approved in chat and applied unchanged.
It adds immutable field/method-bound rules with direct/indirect write
coverage and explicit errors for unobservable targets, a reviewed tool/schema
catalogue filter, conditional compiler text and tests using the actual literal,
and pins both Docker launch paths to the reviewed Dockerfile digest. It requires
the bundled native executable path; custom paths now reject.
The full runner keeps read-only mode and was not executed.

The new diagnostic and twelve existing offline diagnostics passed against saved
source. The standalone compiler CLI passed; all seven Python files parsed and
matched the approved drafts exactly. Approved-patch reverse verification and
whitespace checks passed. No real environment, live database, image pull, binary/container/
MCP process, model call, migration, restart or deployment ran. Fake catalogue
fixtures do not verify actual binary provenance or live MCP compatibility.

At 009c2b the matcher/catalogue and immutable snapshots were not yet connected
to runtime/cache. 009c2c now connects them and proves offline HTTP behavior above;
compiler reporting names alone do not close the boundary. Indeterminate related
writes must remain controlled evaluation failures, not false policy-match claims.
Conditional file rules may refuse merge/fork calls because affected paths are
unknown. Before eventual rollout, review/repair legacy conditions and explicitly
resync compiled artifacts for the new conditional text. No live resync ran.
009c3 and patches 010-018 retain their order. Full code previews stay in chat only.

## Policy Snapshot Foundation - 2026-10-15

009c2 is now split into 009c2a snapshot, 009c2b tool/compiler/MCP contract and
009c2c runtime/cache integration with HTTP proof. This addresses separate policy
reads and aggregate cache revisions before enabling the new guard. The single
backlog records the exact order; 009c3 and patches 010-018 retain their places.

009c2a's exact two-file diff was approved in chat and applied unchanged. It reads an
authorized app's selected definitions, normalized metadata and compiled artifacts
in one SELECT without autoflush, defaults, dotenv or ORM identity-map reuse.
It rejects unsupported/unreviewed selectors and inconsistent compiled state;
detached immutable values preserve exact policy content for later comparisons.
The new saved-source diagnostic, four related saved-source diagnostics, Python
parsing, approved-patch reverse verification and whitespace checks passed.
PostgreSQL SQL compiled only; actual PostgreSQL, concurrent database writers, HTTP/runtime/cache wiring and
live services remain unverified. No live inventory, migration, restart or
deployment ran in 009c2a. At that stage the reader had no runtime consumer;
009c2b and 009c2c are now applied above, including runtime/cache integration. The complete approved non-doc diff remains
in chat only; each subsequent non-doc diff still needs preview and approval.

## Versioned Input Condition Storage - 2026-10-15

009c1's exact six-file diff was approved in chat and applied unchanged. New input
selectors are validated against the supported action/field subset before saving
format version 1 in existing conditions JSON. Paths/branches retain case;
titles/repository names fold case without dropping punctuation or Unicode.
Legacy literal definitions stay separate from automatic reuse/deduplication.
Metadata-only edits require explicit condition resubmission for legacy literals;
exact disable-only edits remain available. Assignment-safe resolution preserves
other apps' existing assignments. Output storage is unchanged.

All four saved-source offline diagnostics passed: input storage HTTP/JWT/RBAC,
inventory, GitHub bindings and grammar. All six changed/new Python files parsed;
approved-patch reverse verification and whitespace checks passed. The HTTP test
uses disposable in-memory SQLite with dotenv disabled. The existing PostgreSQL
diagnostic's storage expectation/cleanup prefix changed but it was not run.
No live database inventory, real `.env`, migration, model/MCP execution, restart
or deployment ran.

Runtime enforcement remains unchanged. Continue with 009c2's runtime/cache/compiler
integration, then 009c3's assistant/UI alignment, in the single backlog. Format
version 1 is serialization metadata, not enforcement certification or admin
approval. Live policy review and PostgreSQL verification remain open. Every
subsequent non-doc diff still needs complete chat preview and approval.

## Resource Bindings And Inventory Helpers - 2026-10-15

009b's exact four-file diff was approved in chat and applied unchanged. The
standalone GitHub field bindings and read-only inventory helper had no
management/runtime consumers at 009b; 009c1 now uses them for management validation.
Both new saved-source diagnostics passed,
along with the 009a grammar diagnostic, Python parsing, approved-diff reverse
verification and whitespace checks. SQLite verifies assignment scope,
normalized metadata, no autoflush, private-value omission and CLI write refusal.
No real `.env`, live database inventory, PostgreSQL diagnostic, migration,
model/MCP execution, restart or deployment ran.

009c1 storage validation is applied above; continue with 009c2/009c3 in the single backlog.
The existing custom-resource guard is unchanged. Before runtime adoption, address
cross-tool routes and indirect side effects, the local Docker launcher's unpinned
image, lossy legacy canonicalization and actual saved-policy review. The reviewed
backend image identifies MCP 1.0.4 at revision
`c3dedbece0bf3834829f638a245fb3c51cd98d0b`; its public labels and upstream sources
were read during review without starting a container. Every next non-doc diff
still needs complete chat preview and approval.

## Custom-Resource Grammar Foundation - 2026-10-15

009a's exact two-file diff was approved in chat and applied. The pure parser and
standalone diagnostic preserve literal values and reject unsupported condition
syntax. Saved-source checks passed 22 supported selectors and 32 rejection
cases; Python parsing, approved-diff reverse verification and whitespace checks
also passed. Management adoption is now applied in 009c1 above; the
existing runtime custom-resource guard remains unchanged. No database, migration,
environment edit, external service, restart or deployment ran.

009b's compatibility inventory helper and verified tool-field bindings are now
applied above, along with 009c1. Continue with 009c2/009c3 runtime/assistant integration in
`open-work-backlog.md#009-custom-resource-enforcement-boundaries`. Do not route
literal parsing through the current lossy canonicalizer unchanged. Every later
non-doc diff still needs complete chat preview and approval.

## App Model/Credential Grant Foundation - 2026-10-15

Patch 008's design is approved. Its migration/backfill, rollback, implementation
slices and checks are in
`open-work-backlog.md#008-app-specific-modelcredential-grants`. Slices 008a/008b/008c
were approved in chat and applied. No live database migration or
environment change was performed. Every subsequent non-doc diff still needs
chat preview and approval.

008a adds the grant model, a schema/inventory/manifest helper with separate
explicit apply flags, and an offline regression. Saved-source checks passed
on disposable SQLite, including rollback and revocation preservation; existing
app-authorization and connector-security regressions also passed. AST, approved-
diff reverse verification, and whitespace checks passed. PostgreSQL DDL compiled
only; actual PostgreSQL verification remains required before deployment.
008b's 13-file diff adds grant management, scoped model options, credential-name
approval and explicit selection validation. The new real-JWT/SQLite HTTP
diagnostic and five related offline checks passed against saved source. All 12
changed/new Python files parsed; reverse-patch and whitespace checks passed.
Grant audit classification is included in 008b with its new mutation routes.
008c's approved 12-file diff adds legacy runtime credential checks, cold/warm
grant enforcement and the unmounted selector adaptation. The new runtime
diagnostic and eight related offline checks passed against saved source, alongside
full frontend TypeScript, scoped ESLint, Python AST, approved-diff reverse
verification and whitespace checks. Live grant reads cover
warm caches, lock waits and completed builds; model construction uses the same
validated snapshot. Unavailable defaults and legacy references fail closed.
The runtime boundary is implemented in source. PostgreSQL behavior and browser
verification remain unverified; two live diagnostic fixtures/expectations changed
but were not run. DELETE now retains a disabled row so an old bootstrap manifest
cannot restore access. See the backlog for scope and verification limits.

Before 008b, a reproduction with disposable SQLite and real JWT confirmed that
an App A developer can list/select a configuration used by App B, and can select
the environment default without an app grant. Only fake metadata/JWT settings
were used; no model/connector credential lookup, model/MCP construction, live
database or external service ran.

The approved design uses explicit app/purpose grants, including environment
defaults; grants cover the selected configuration and its credential together. Existing
selections are inventoried for explicit admin review, never automatically
approved. Runtime grant checks must run on warm caches as well as cold builds.
Missing grants now deny runtime use, including on warm caches. Review existing
named/default selections and approve grants for both purposes before rollout;
otherwise those apps intentionally receive runtime 503 responses. Review
rollback behavior before deployment. No real environment change, live migration,
restart or deployment ran. Patch 009a's grammar foundation is applied above;
009b is applied too; 009c and patches 010-018 remain in their order.

## Connector Credential Provisioning - 2026-10-15

- Approved patch 007 is applied. System admins provision new connector links and
  submit credential-reference fields, including null/blank/unchanged values.
  Linked developers retain existing-link toggles and unlink. Omitting credentials
  during POST upsert preserves the existing reference. A developer cannot unlink
  and recreate a link to obtain the shared default PAT.
- GitHub credential references require exact backend name approval before lookup.
  `GITHUB_PERSONAL_ACCESS_TOKEN` is automatically approved. Additional names go
  in `GMS_ALLOWED_GITHUB_CREDENTIAL_ENV_VARS`, comma-separated. Restart the backend
  after configuration changes; cached MCP clients do not observe env changes.
- Existing custom references must be approved before rollout. Unapproved/missing
  credentials yield a generic runtime-setup 503 before model/MCP construction.
  Admin API writes reject unapproved/invalid references with 400. Review legacy
  links: allowlisting does not establish their historical admin/app ownership.
- Frontend provisioning controls are admin-only; linked-developer toggles/unlink
  remain available. Other connector types remain metadata-only. No migration or
  change to the committed read-only GitHub default was required.
- The 60-case security regression, six related diagnostics, frontend TypeScript,
  scoped ESLint, Python AST, and diff checks passed against saved source. No live
  database, external service, real `.env` edit, service restart, or deployment ran.
  Browser verification was not performed. See `testing-notes.md` for limits.
- Next: patch 008, app-specific model/credential grants, beginning with design
  review against `target-architecture.md` before any schema proposal.

## App Authorization Security - 2026-10-15

- Approved patch 006 is applied. `PUT /apps/{app_id}` rejects developer bodies
  containing `authorized`, including unchanged values and null, before model
  reference validation or any field assignment. Only system admins can enable
  or disable runtime access. App admin/owner links do not grant that permission.
- Existing name/client-ID API edits remain available, including for disabled
  apps; a rename does not restore runtime authentication. The client-ID alias
  has no general metadata PUT route. Frontend authorization controls were already
  hidden and Client ID read-only; no UI or schema change was needed.
- The saved-source regression passed 24 protected-field cases plus RBAC,
  mixed-update atomicity, and real runtime-auth revocation/recovery cases.
  Password-change, management-audit, policy-loading, syntax, and diff checks
  passed. See `testing-notes.md` for limits. No live database, LLM, MCP call,
  service restart, or deployment ran. Already-authenticated requests are not
  cancelled by this change; API-key rotation behavior is unchanged.
- Connector credential provisioning was subsequently restricted by patch 007 above.

## Database Policy Loading Security - 2026-10-15

- Approved patch 005 is applied. Failed policy/compiled-rule reads and malformed
  selected rows stop runtime setup instead of silently reducing enforcement.
  Runtime setup returns a generic 503 without internal database error details.
- Policies are read/compiled before model or MCP construction. Tool-guard imports
  no longer read the database; wrappers load current rules unless explicitly
  supplied. The compatibility blocked-tools constant describes static defaults.
- Explicit default policy mode remains usable by offline diagnostics, including
  static prompt-rule generation. Authenticated runtime construction requires
  database policies, including when an app runtime is cached. Existing malformed
  rows require correction. No migration is needed.
- The saved-source policy regression and seven existing diagnostics passed;
  see `testing-notes.md` for coverage and limits. No real `.env` edit, live
  PostgreSQL test, Azure/GitHub call, service restart, or deployment ran.
- The generic 503 applies to runtime setup; authentication/history/startup
  database checks keep existing error handling. Policy snapshot consistency and
  active compiled-row completeness are not added by this patch.
- App authorization changes were subsequently restricted by patch 006 above.
  Continue to show code diffs in chat only and follow `open-work-backlog.md`.

## Output Classification Security - 2026-10-15

- Azure refusal of an output self-check produces a controlled block, including
  responses without obvious secret markers. Source remains `azure_content_filter`;
  reported category metadata is preserved. Unrelated provider failures propagate.
- Wrapped/raw Azure errors and LangChain filtered-completion ValueErrors are
  recognized. Normal NeMo classifications are unchanged.
- No schema migration or new configuration is required. Restart/redeploy after
  applying the source patch. No service or deployment was changed in this review.
- The approved patch is applied to source. Its regression reproduced the old
  bypass before application and passed against saved source: 12 offline
  HTTP/history/log cases plus normal/error controls. Earlier privacy, literal-
  rendering, and endpoint security regressions also passed. See
  `testing-notes.md`. No live-Postgres diagnostic was run.
- Harmless output may also be withheld if classification is refused. Address
  false positives through classifier evaluation. Database policy-loader
  fail-open behavior was addressed by patch 005 above.

## LLM Credential Destinations - 2026-10-15

- The approved source patch makes LLM configuration creation system-admin-only.
  Developers retain readable model choices and linked-app main-model selection.
- Runtime endpoints must match `AZURE_OPENAI_ENDPOINT` or an exact HTTPS origin
  in backend `GMS_ALLOWED_LLM_ENDPOINTS`. Existing stored endpoints are checked
  before their selected credential references are resolved. Unapproved runtime
  endpoints return a controlled 503; model clients refuse HTTP redirects.
- Additional origins require deployment configuration and a backend restart.
  No real `.env` change, database migration, service restart, image publish, or
  deployment was performed for this patch.
- The app LLM settings component guards its creation controls for admins but
  remains unmounted by application routes. Use the management API until wired.
- Saved-source authorization/endpoint/redirect tests, model-selection checks,
  both earlier privacy/literal-rendering regressions, and frontend TypeScript
  passed offline. See `testing-notes.md` for commands and limits.
- App-specific model/credential grants and the remaining fail-open policy and
  classifier paths need separate reviewed patches.

## Assistant UI And Password Changes - 2026-10-09

- Approved changes are applied to source. The assistant has one Generate policy
  button and no drafting-mode selector or Yes/No outcome boxes. Example buttons
  immediately load their saved draft/visualization; an edited description uses
  live AI. `/policy-preview` remains offline and does not call the backend.
- Copy Password now handles missing/denied Clipboard API access, tries a
  selection-based fallback, and shows an error if both copy methods fail.
- Settings has Current password, New password, and Confirm new password fields.
  `PUT /management-auth/me/password` accepts the authenticated user's current
  password and a new 15-256-character password. It rejects incorrect current
  passwords, unchanged/all-whitespace replacements, and concurrent hash changes.
- Management JWTs now carry an HMAC-derived password version. Password changes
  and admin resets invalidate that user's earlier sessions. Existing tokens
  without the version are rejected; sign in once after updating the backend.
  Successful self-service changes return to Login with a confirmation message.
- Password-change audit records contain metadata only. No schema migration was
  needed. Forced first-login replacement and temporary-password expiry remain
  unfinished; the older schema-only preview below was not applied.
- Actual-source password-change, policy-assistant, and audit tests, Python
  compilation, full frontend TypeScript, and scoped ESLint passed. See
  `testing-notes.md` for verification limits. No deployment/image publish ran.

## Home Computer: Accessing The Online Database - 2026-10-09

Read [home-online-database.md](home-online-database.md) before changing connection
settings. It explains using the deployed API from a local frontend, directly
connecting a local Python backend/DBeaver to online PostgreSQL, TLS/firewall
requirements, safe verification, and switching back to local development.

The work computer currently uses Docker PostgreSQL at `127.0.0.1:5432`; the
home local database uses port `5433`. Neither setting points directly to an
online database. Same login credentials do not establish database sharing;
an imported backup creates a separate copy with no automatic synchronization.
The online provider/hostname/credentials have not been supplied or verified.
The guide therefore uses placeholders and does not claim a remote connection
has been configured. Keep real credentials in ignored local configuration.

Important: Compose explicitly points its backend at the local `postgres`
service. Editing `.env` DATABASE_URL alone does not override that Compose value.
Use the direct Python launcher for the documented online-database option.

## Live Input/Output Policy Authoring - 2026-10-09

- Approved output-authoring changes are applied. Create Policy exposes the
  Input/Output selector before the assistant and sends `policy_type` to the
  JWT-protected `/policy-assistant/suggest` endpoint.
- GitHub input drafting still validates enabled write mappings and can suggest
  related input policies. Output drafts are independent of connector metadata,
  carry `output_rule`, use assistant-response examples, and do not suggest
  additional bans. The flowchart is `Output -> Custom resource`.
- The hello example fills `Do not include the word "hello" in assistant
  responses.` into the existing Output Rule field. Persistence still requires
  an explicit Create action and uses the existing assignment-safe CRUD path.
- No database migration, credential change, connector execution or runtime
  enforcement change was required. Backend Azure environment settings are used
  for drafting; app-selected runtime LLM configurations remain separate.
- `/policy-preview` stays login/database-free and sample-only, including its
  output sample and mock creation. Other-connector input authoring is deferred
  until those connectors are implemented in GMS.
- See `testing-notes.md` for offline/live/browser verification and
  `open-work-backlog.md` for remaining deployment and semantic evaluation work.

## Traffic And Audit Logs - 2026-09-23
- The admin Logs screen now has `Traffic Logs` and `Audit Logs` tabs. The old
  separate User Logs tab was removed because its prompt/response belongs to the
  same runtime request as the traffic metadata and execution events.
- Storage foundation: runtime_user_logs links input/final response to a
  traffic request. Existing API startup creates the new table; no backfill.
- Capture now links authenticated input and the final response to traffic logs,
  including requests without conversation IDs. Failed requests retain a null
  response; unauthenticated/invalid-body requests do not capture message content.
- Content is excluded from the persistence-failure logger, but submitted text
  may itself contain sensitive information. Admins can retrieve captured content
  through GET /runtime-logs/{request_id}/user-content.
- GET /runtime-logs?user_content_only=true lists only requests with captured
  content, retaining app/outcome filters and pagination without returning text.
- Every Traffic Log detail now attempts to load its captured input/final
  response and renders it above execution events. A request without captured
  content still renders normally.
- `management_audit_logs` is an append-only metadata table for management
  mutations. Central middleware records successful, rejected, and failed
  POST/PUT/PATCH/DELETE requests for apps, policies, assignments, connectors,
  users, LLM configurations, allowed test cases, and profile changes.
- Audit records snapshot the actor email/role and retain request ID, action,
  entity, path, method, status, outcome, client IP, user agent, and timestamp.
  Request/response bodies, passwords, API keys, credentials, and private model
  reasoning are deliberately not captured.
- Admin-only `GET /audit-logs` supports entity/outcome filters and bounded
  pagination. The frontend Audit Logs tab displays these records alongside the
  existing Traffic Logs view.
- Traffic and Audit table headers and values are centered on the same grid.
  Audit columns now share the available width proportionally and wrap long
  emails/request paths, so the table does not require horizontal scrolling.
- The Policies table also uses a compact fluid grid. All policy, scope, date,
  and action columns remain visible while long values wrap within their cells.
  The inactive triple-dot control was removed; policy rows open summaries and
  retain only the functional Edit and Delete actions.
  Connector-independent rows display `None` in Policy Connector instead of
  `Global` or generic `Policy`; their separate Global badge remains unchanged.
  The Global column reserves a small right-side gap before Edit/Delete so the
  scope badge and action controls do not appear clumped together.
- `tests/test_management_audit_http.py` uses an isolated SQLite database and
  real JWT permission checks to verify successful, rejected, and failed capture,
  exclusions, filters, pagination, actor attribution, and secret omission.
- Local PostgreSQL now has the `management_audit_logs` table because an existing
  API test started the real application lifespan after this model was added.
  There is no backfill. Run API tests sequentially during schema creation;
  simultaneous `create_all` startup processes can race on a brand-new table.
- Verification: the isolated `tests/test_runtime_logs_http.py` passed with
  SQLite foreign keys enabled, covering traffic-response content exclusion,
  dry-run preservation, and cascading retention deletion of message pairs.
  The content endpoint also passed real-JWT access checks, exact response-field
  and no-store checks, and 404 checks for missing requests or absent content.
  The user-content-only listing passed filtering, pagination, empty-result,
  invalid-boolean, no-store, and message-content exclusion checks in SQLite.
  All six `tests/test_runtime_events.py` checks and Python compilation passed.
  All four `tests/test_request_timing.py` checks also passed. Temporary inline
  fake-runtime checks verified authenticated capture, final blocked/tool-error
  responses, missing/shared conversation IDs, invalid credentials/body rejection,
  runtime failures, concurrent request isolation, interrupted/non-2xx response
  suppression, and metadata-only persistence-failure logging. These additional
  checks were not saved as permanent regression tests.
  No real database migration, live Azure/GitHub calls, or deployment was run.

## Resume Here - 2026-09-11

The current priority is the password lifecycle, not further retention work.
This handover update is documentation-only. The password Stage 1 code was
previewed in chat but has NOT been approved or applied; no password migration
has run. Do not interpret the request to update docs as code approval.

Confirmed workflow for developers and administrators:

1. An admin creates an account and GMS generates its temporary password.
2. The recipient uses it to choose a personal password before accessing normal
   GMS features. The backend must enforce this restricted setup flow.
3. An admin can regenerate a temporary password for a forgotten password;
   the recipient repeats the required replacement step.
4. Users who know their password can change it voluntarily through Settings
   by verifying their current password.

Already implemented: User Management's Reset Password action and
`POST /management-users/{user_id}/password` can target either role. The secret
is displayed only once, but that does NOT currently make it single-use or
expiring. Required replacement, self-service change, and invalidation of old
JWTs after a password reset are not implemented.

Pending Stage 1 preview (schema only):

- Add `UserRecord.must_change_password` with false defaults,
  `temporary_password_expires_at` as nullable timezone-aware datetime, and
  `session_version` with zero defaults in `database/models.py`.
- Extend `scripts/migrate_management_auth.py` with idempotent PostgreSQL
  column additions; leave existing passwords/accounts unchanged.
- Add `tests/test_password_lifecycle_schema.py`, an isolated SQLite defaults
  check for both roles. This file does not exist yet.
- Once approved, migrate an existing database before starting backend code
  that expects these columns. Schema defaults alone enforce nothing.

Later stages must cover authenticated change/setup APIs, restricted temporary
sessions, expiry, atomic password/version updates, validation of JWT versions
on every protected management request, and frontend first-login/Settings
screens. Account creation and admin reset must set required replacement and
expiry explicitly; replacing or resetting credentials must invalidate prior
sessions. Include negative tests for direct-API bypass and both user roles.

Security direction discussed: random temporary credentials, approved secure
delivery and verified reset requesters, password-only minimum length of 15,
support for at least 64 characters, common/compromised-password blocking,
rate limiting, reviewed salted password hashing, HTTPS, and metadata-only
account audit events. Do not add arbitrary composition rules or routine
password rotation. These controls are targets, not a compliance claim.
Temporary expiry duration and production throttling/deployment details still
need selection. MFA for admins is a production priority. Email recovery and
notifications remain unimplemented; recovery for the only admin is unresolved.

Reference guidance discussed in chat:
- [NIST password requirements](https://pages.nist.gov/800-63-4/sp800-63b/authenticators/)
- [OWASP recovery guidance](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html)

Preview every proposed code file in the final chat response using unified
diffs, filename/line references, and a per-file summary. Wait for approval
before non-doc edits. Do not create preview markdown files. List commands run
in the final response; never expose `.env` values or passwords.

Before moving machines, review `git status --short`: the mobile-filter/docs
changes, retention-test additions, and new `scripts/cleanup_runtime_logs.py`
are still uncommitted at handover. The cleanup script is untracked and must
be included when the user chooses to commit/transfer this work. No commit,
image rebuild, registry push, or Azure deployment was performed here.

## Runtime Logging Foundation - 2026-09-09

- Added `RuntimeLogRecord` and `RuntimeLogEventRecord` to the ORM models.
- `runtime_logs` holds request metadata; `runtime_log_events` holds ordered
  execution events. Neither table has fields for prompts, responses,
  credentials, tool arguments, or private model reasoning.
- Deleting an app preserves its logs with a null app reference. Deleting a
  runtime log removes its associated events.
- No database migration or deployment was run for this change. The existing
  API startup creates the missing tables when the updated backend runs.
- Request-level recording now covers POST `/v1/guardrails/run`, including
  rejected requests and handled runtime outcomes. App identity is attached
  only after successful authentication, using the existing request ID.
- Request lifecycle events bracket observed rail, agent, and tool events.
  Classifier verdicts are distinct from call return/exception events.
  Unreached stages receive `not_run` markers.
- Each capture retains at most 256 detailed events, plus bounded truncation,
  skipped-stage, and request lifecycle markers.
  Persistence runs after the downstream request completes; forced process
  termination can lose an in-flight log. A failed write emits metadata-only
  JSON to backend logs without retrying the agent or tools.
- `tests/test_runtime_events.py` provides offline collector regression checks.
- Admin-only `GET /runtime-logs` returns paginated request metadata with
  optional app/outcome filters. `GET /runtime-logs/{request_id}` returns
  ordered execution events. Both use management JWT authentication.
- Lists default to 25 records, cap at 100, and limit offsets to 10000.
  They return `has_more` without a total-count query.
- `tests/test_runtime_logs_http.py` checks access and query behaviour using
  an isolated in-memory database and real management tokens.
- The admin-only frontend `/logs` screen lists requests with app/outcome
  filters, manual refresh, and 25-record pagination. `/logs/[requestId]`
  displays metadata and ordered execution events using UTC timestamps.
- Frontend log requests are cancellable and are not persisted in browser
  storage. Successful API responses remain `no-store`.
- The shared API client ignores stale authentication failures from an old
  session when a different management session has already been established.
- Frontend verification on 2026-09-10: TypeScript and scoped Next ESLint
  checks passed. Temporary headless Edge tests with synthetic API responses
  passed pagination, filtering, details, empty/error/retry states, cancellation,
  and admin/developer/anonymous access checks. Inline API-client checks passed
  stale/current 401 handling and session preservation after a 503.
  Screenshots were inspected at desktop and narrow mobile sizes; cramped mobile
  filter values were identified. The approved correction was applied on
  2026-09-11: App and Outcome filters stack below the `sm` breakpoint while
  preserving the side-by-side desktop layout.
  The correction passed TypeScript, scoped ESLint, and isolated headless Edge
  layout checks at 320, 390, and 1440 pixels, with screenshots inspected.
  These checks did not contact PostgreSQL, Azure, or GitHub and are not yet
  committed regression tests. No production image build or deployment ran.
- Manual retention: `python scripts/cleanup_runtime_logs.py --days 30`
  previews up to 500 expired completed requests; add `--apply` to delete
  those requests and their events. Repeat for further batches. No scheduler.
  Age uses `completed_at < UTC cutoff`; null completion times and exact-cutoff
  records are retained. `--days` accepts 1 through 3650, defaulting to 30.
  Do not shorten retention just to force deletion of real logs during testing.
- Retention verification (2026-09-11): `tests/test_runtime_logs_http.py`
  passed with dry-run, cutoff, unfinished-request, and event-cleanup checks;
  all six `tests/test_runtime_events.py` checks passed. An additional inline
  SQLite test with foreign keys enabled verified the 500-request cap,
  rollback of request/event deletion, and repeated batches. No cleanup was
  run against the real database; PostgreSQL retention verification is pending.
- Scheduled retention, PostgreSQL endpoint verification, HTTP recorder regression
  coverage, and automated frontend regression coverage remain unfinished.
  Preview their code before edits.

## Current Deployment Milestone - 2026-08-28

The backend and frontend are ready to be built as separate Linux AMD64 images
for Azure Container Registry and Azure Container Instances:

```text
guardrail.azurecr.io/guardrail-be:latest  -> internal port 8000
guardrail.azurecr.io/guardrail-fe:latest  -> public/internal port 80
```

The backend image now bundles the pinned official GitHub MCP executable and
launches it natively over stdio. No Docker socket mount, nested Docker daemon,
or root runtime user is required. Direct local Python runs still default to the
existing Docker-based MCP launcher.

Build from the repository root without Compose:

```powershell
docker build --platform linux/amd64 -t guardrail-be:latest .
docker build --platform linux/amd64 --build-arg NEXT_PUBLIC_API_BASE_URL=/api/gms -t guardrail-fe:latest .\frontend
```

For ACI, place both images in one container group, expose only frontend port
`80`, and set frontend `GMS_API_BASE_URL=http://127.0.0.1:8000`. The frontend
process listens directly on `80`; ACI is not expected to map `80` to `3000`.
The backend remains on internal port `8000`, and browser calls use the
same-origin `/api/gms` route. An Azure ingress service is optional future work
for TLS, a custom domain, WAF behavior, or other production ingress features.

Read `docs/containerisation.md` before building, pushing, or changing ports. It
contains direct `docker run`, ACR tag/push, ACI topology, secrets, and health
check instructions. Actual ACI resource creation remains with the supervisor's
deployment team; this developer handoff contains the verified backend image
and the contract for producing the final matching image pair.

Run the new launch-mode check after pulling this milestone:

```powershell
.\.venv\Scripts\python.exe tests\test_runtime_mcp_launch.py
```

### Latest Local Verification - 2026-08-28

The backend image was rebuilt after expanding deterministic output-rule phrase
parsing. The local container verification proved:

```text
backend /health: ok
backend /health/db: reachable
frontend /api/gms/health proxy: ok
backend GitHub MCP launch mode: native
GITHUB_MCP_READ_ONLY=0 manual mode: write tools offered
explicit output rule "Do not allow the word 'hello'": compiled to "hello"
output guard and HTTP authentication regression tests: passed
```

The corrected backend image currently exists locally as
`guardrail-be:latest`; it has not yet been pushed to ACR. Rebuild and verify
the frontend before pushing one matching frontend/backend release pair.

## Read This First

This file records the exact project state needed to continue safely between
the work and home computers.

Also follow the repository-level rules in `AGENTS.md`, especially the
requirement to preview exact non-doc code diffs and wait for approval.

After pulling on the home computer, use host port `5433` for project Postgres.
Start the database and run the fast regression checks before new work:

```powershell
git pull
docker compose up -d postgres
.\.venv\Scripts\python.exe tests\test_app_auth_http.py
.\.venv\Scripts\python.exe tests\test_policy_assignment_api.py
.\.venv\Scripts\python.exe tests\test_policy_auto_compile.py
.\.venv\Scripts\python.exe tests\test_guardrails_run_http.py
.\.venv\Scripts\python.exe tests\test_output_guard.py
.\.venv\Scripts\python.exe tests\test_runtime_connector_access.py
.\.venv\Scripts\python.exe tests\test_app_connector_api.py
.\.venv\Scripts\python.exe tests\test_runtime_connector_credentials.py
.\.venv\Scripts\python.exe tests\test_app_policy_scope.py
.\.venv\Scripts\python.exe tests\test_tool_guard.py
```

Keep `tests/test_nemo_mcp.py` as the slower opt-in live Azure/GitHub check after
the fast suite is green. Normal scripted runs must use
`GITHUB_MCP_READ_ONLY=1`.

### Home Computer Direct-Docker Resume

The home computer's host tools use Postgres port `5433`. A backend container
must instead reach that host database through `host.docker.internal:5433`.
After substituting the local database username and password, the direct-image
workflow is:

```powershell
docker build --platform linux/amd64 -t guardrail-be:latest .
docker build --platform linux/amd64 --build-arg NEXT_PUBLIC_API_BASE_URL=/api/gms -t guardrail-fe:latest .\frontend

docker rm -f guardrail-be guardrail-fe
docker run -d --name guardrail-be --env-file .env -e DATABASE_URL="postgresql+psycopg://<user>:<password>@host.docker.internal:5433/nemo_mcp_guardrails" -p 8000:8000 guardrail-be:latest
docker run -d --name guardrail-fe -e GMS_API_BASE_URL=http://host.docker.internal:8000 -p 80:80 guardrail-fe:latest

Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/health/db
Invoke-RestMethod http://127.0.0.1/api/gms/health
```

Open `http://127.0.0.1/login`. Swagger is available locally at
`http://127.0.0.1:8000/docs`. If host port `80` is occupied, publish the
frontend with `-p 3000:80` and use `http://127.0.0.1:3000`; the image still
listens on port `80` internally.

Before leaving the home computer, make sure this milestone is committed and
pushed. The work computer cannot see unpushed local files:

```powershell
git status
git add .
git commit -m "Prepare backend and frontend handoff for GMS demo"
git push
```

The frontend and backend are now containerized too. To run the complete local
stack instead of separate Python/npm development servers:

```powershell
docker compose build backend frontend
docker compose up -d
docker compose ps
```

Open `http://127.0.0.1/login`. Backend health is available at
`http://127.0.0.1:8000/health`, and the frontend proxy can be checked at
`http://127.0.0.1/api/gms/health`. Read `docs/containerisation.md` before
changing the Docker or Azure Container Instances layout.

If local host port `80` is occupied, set `FRONTEND_PORT=3000` in `.env` and use
the previous `http://127.0.0.1:3000` local URLs. This override does not change
the deployed image contract: the frontend container still listens on `80`.

Review `git status` before committing and confirm `.env` is not staged.

The work computer may use Postgres host port `5432`. The home computer uses
host port `5433` because Windows PostgreSQL already owns `5432`. Keep each
computer's local `.env` correct and never commit it.

GitHub MCP read/write mode is controlled from `.env`:

```env
GITHUB_MCP_READ_ONLY=1  # safe default for scripted tests
GITHUB_MCP_READ_ONLY=0  # manual local write testing
```

For a direct Python API run, restart `scripts/run_api.py` after flipping this
value. For a containerized API, remove and recreate the backend container;
`docker restart` does not reload values from `--env-file`. Rebuilding the image
is required only when code or dependencies changed, not for an `.env`-only
change. Verify the live container value with:

```powershell
docker exec guardrail-be printenv GITHUB_MCP_READ_ONLY
```

The committed `.env.example` keeps the safe read-only default.

## Current Milestone

The authenticated, app-scoped runtime foundation is implemented:

```text
X-App-ID + X-API-Key
-> require_authenticated_app
-> authenticated AppRecord
-> app-scoped global + app policy assignments
-> app-scoped compiled NeMo prompt rules
-> app-scoped blocked MCP tool names
```

App/global policy assignment POST bodies now use `policy_ids`, so one endpoint
handles both single and bulk assignment. Bulk update/delete also uses
`policy_ids` and returns `404` if a requested policy is not assigned in that
scope:

```json
{
  "policy_ids": [26, 12, 13],
  "enabled": true
}
```

Assignment responses include readable app and policy labels beside numeric IDs
for Swagger and the future frontend.

Developer-friendly client-ID aliases are also available:

```text
GET  /apps/by-client-id/{client_id}
GET  /apps/by-client-id/{client_id}/policy-assignments
POST /apps/by-client-id/{client_id}/policy-assignments
PUT  /apps/by-client-id/{client_id}/policy-assignments/{assignment_id}
DELETE /apps/by-client-id/{client_id}/policy-assignments/{assignment_id}
GET  /apps/{app_id}/effective-policy-assignments
GET  /apps/by-client-id/{client_id}/effective-policy-assignments
```

These routes resolve `client_id` to the internal app ID and then use the same
assignment logic. The effective-policy routes are read-only summaries that show
mandatory global assignments and app-specific assignments for one app together.

Policy create/update now refreshes `compiled_policy_rules` automatically.
Old compiled rows are marked stale and disabled, and a fresh active row is
created when the policy remains enabled. `POST /policies/compile-rules` remains
available as a manual full resync/debug endpoint.

`POST /v1/guardrails/run` now builds that runtime context and executes the
submitted message through the reusable guarded flow. It also supports hybrid
conversation history: stored turns for `(app_id, conversation_id)` are loaded
when available, client-supplied `conversation_history` bootstraps a new
conversation, and older turns are trimmed by `NEMO_MAX_RUNTIME_CONTEXT_CHARS`
before the agent sees them.

Reusable single-request guardrail coordination is also implemented:

```text
execute_guarded_message()
-> NeMo input rail
-> stop before action execution when blocked
-> otherwise run LangChain agent with guarded MCP tools
-> return status=tool_error when a connector tool raises ToolException
-> deterministically check explicit quoted prohibited output phrases
-> NeMo output rail
-> return controlled blocked response when Azure filters output self-check
-> GuardedExecutionResult
```

`runtime_factory.py` loads app-scoped output policy objects and uses
`output_guard.py` to compile explicit quoted prohibitions such as
`Cannot say 'hello'`. `guarded_execution.py` checks those phrases
case-insensitively before NeMo classifies broader semantic rules. A match uses
the normal output safety refusal and debug source
`deterministic_output_phrase`.

`POST /v1/guardrails/run` now exposes `output_rail_source` and
`output_rail_categories` outside debug mode. The app Runtime Test displays
`blocked (Azure: category)` for confirmed Azure completion filtering,
`blocked (Azure)` when no category is available, and `blocked (GMS)` for NeMo
or deterministic GMS enforcement. A normal polite model refusal is not an
Azure filter event and may still pass the output rail.

Azure can also filter the prompt used by NeMo `self_check_input`. Those
`LLMCallException` failures are caught in `execute_guarded_message()` and
returned as `Input: blocked (Azure: category)`, with output marked `not run`,
instead of surfacing to the frontend as `Failed to fetch` from an HTTP `500`.

When Azure filters the main agent completion, the current LangChain Azure
adapter may raise a plain `ValueError` and discard category metadata. The
runtime recognizes its exact provider-filter message and returns
`Output: blocked (Azure)` rather than an HTTP `500`.

Tool-guard policy matches now raise `ToolGuardViolation` before the wrapped MCP
tool executes. Runtime Test displays `Tool guard: blocked (GMS)` and leaves the
output rail as `not run`; connector failures remain the separate `tool_error`
path. `Guarded tool types` is a policy-coverage count, not a count of calls made
by the current request.

The frontend Runtime Test has an app API key field for local/manual testing
convenience. Real apps still call `POST /v1/guardrails/run` from their own
backend with `X-App-ID` and `X-API-Key`.
The app Runtime Test now displays the request path as an
`Input -> Tool guard -> Output` progress bar: green means passed, red means the
blocked/error stage, and grey means the stage did not run.

Runtime debug is disabled in `.env.example`. When `NEMO_RUNTIME_DEBUG=1`,
`/v1/guardrails/run` includes tool-event names and tool names only in
`debug_tool_trace`; Runtime Test displays these under Connector debug trace.
Raw agent output, tool arguments/results/errors, and output rule text never
appear in client debug fields. Legacy content fields remain null.

`tests/test_nemo_mcp.py` calls this reusable function and still prints the
same detailed terminal workflow. The full read-only NeMo + GitHub MCP run
passed after the extraction.

`tests/test_guardrails_run_http.py` now proves authenticated
`POST /v1/guardrails/run` uses real temporary DB app assignments,
`compiled_policy_rules`, app-scoped prompt rules, and app-scoped blocked tools.
It fakes rails/agent so it does not start Docker, GitHub MCP, or Azure.

Runtime now checks `app_connectors` before building GitHub MCP tools. An app
must have an enabled link to the enabled GitHub connector, or `/run` returns
`403` before Docker/Azure/MCP startup.

App connector links can now be managed through HTTP instead of SQL:

```text
GET    /apps/{app_id}/connectors
POST   /apps/{app_id}/connectors
PUT    /apps/{app_id}/connectors/{connector_ref}
DELETE /apps/{app_id}/connectors/{connector_ref}

GET    /apps/by-client-id/{client_id}/connectors
POST   /apps/by-client-id/{client_id}/connectors
PUT    /apps/by-client-id/{client_id}/connectors/{connector_ref}
DELETE /apps/by-client-id/{client_id}/connectors/{connector_ref}
```

`credential_reference="env:VAR_NAME"` is executable for GitHub PAT selection only
when that name is backend-approved. Extra names require
`GMS_ALLOWED_GITHUB_CREDENTIAL_ENV_VARS` and a backend restart; see patch 007 above.
Blank references fall back to `GITHUB_PERSONAL_ACCESS_TOKEN`; `vault:...`
remains future production work.

Frontend planning docs are ready:

```text
docs/frontend-api-map.md
docs/frontend-screen-plan.md
docs/frontend-demo-flow.md
```

The first frontend backend-integration slice is also in place. The
`/policies` page now has a typed client-side API adapter:

```text
frontend/lib/api-client.ts
frontend/app/policies/page.tsx
frontend/.env.example
```

## Frontend Initial-Load Optimisation

- The Policies page loads apps and assignments first, reducing its initial
  backend request set from four requests to two.
- Policy definitions and builder mappings are fetched only when Create or Edit
  is opened, then reused for the current Policies page session.
- Editing fetches only the selected reusable policy definition instead of the
  complete policy catalogue.
- Backend runtime construction caching is implemented independently below so
  frontend lazy loading and runtime-object reuse can be tuned separately.

## Backend Runtime Cache

- Repeated requests reuse each app's NeMo rails, Azure clients, guarded MCP
  tools, and LangChain agent for five minutes by default.
- One lightweight database revision query detects policy, assignment,
  connector, app, compiled-rule, connector-metadata, or LLM changes before a
  cached runtime is reused. Relevant changes therefore rebuild immediately.
- Concurrent cold requests for one app share a single build, and least-recently
  used entries are capped at 32 apps by default.
- Set `NEMO_RUNTIME_CACHE_TTL_SECONDS=0` to disable reuse while debugging.
- Compare the existing `runtime_setup` entry in `Server-Timing` between cold
  and warm requests when validating Azure performance.

The normal-developer Apps workflow is now implemented:

```text
/apps
-> real app list, search, pagination, create and delete
-> click row to open /apps/[clientId]

/apps/[clientId]
-> Overview: edit name and rotate API key
-> Connectors: link/enable/disable/unlink GitHub
-> LLM: update main and guardrail config IDs
-> Policies: effective summary and link to filtered policy management
-> Runtime Test: authenticated POST /v1/guardrails/run
```

SharePoint is hidden from active connector selectors because only GitHub has
normalized runtime metadata and an executable adapter. The LLM tab uses numeric
config IDs until a readable LLM-config listing endpoint is added.

App creation no longer accepts user-entered client IDs or API keys. The backend
generates GUID-format client IDs and high-entropy API keys, returns the API key
once, and stores only the hash.

User Management now mirrors the Apps screen: rows show name, email, role, and
enabled status. Create User is a button, and clicking a user opens a modal for
role/status changes, password reset, and app links.

The Settings dark-mode toggle now applies an app-wide Tailwind `dark` class.
Saving writes `gms:theme` to browser `localStorage`; `app/layout.tsx` restores
the class before rendering to reduce theme flashing.

The browser tab icon is `frontend/app/icon.svg`. Next.js discovers it through
the App Router icon convention; it mirrors the optically centered blue G used
in the top navigation.

The policy builder loads valid connector/action/resource choices from
`GET /policy-options`; the frontend filters this to GitHub for the current
demo. In the policy table, global assignments use a globe icon, app-specific
GitHub assignments use the GitHub connector mark, and unknown connector values
fall back to the folder icon.

The shared Create/Edit Policy modal now has an Input/Output rail selector.
Policy naming is unlocked immediately. Input mode keeps the cascading GitHub
fields and optional custom resource; output mode hides connector fields and
requires a free-text output rule. Output definitions use category `custom`,
while their app/global assignment display name remains independent.

The stored output rule lives in `policies.conditions.output_rule`; the
`description` column holds the policy name consistently with input policies.
Run `python scripts/migrate_output_policy_rules.py` after pulling this change
to backfill legacy output rows and regenerate active compiled rules. Runtime
loaders fall back to legacy `description` values until migration is run.
Compiled output rules must remain restriction statements; do not add `Answer
no otherwise` to each individual rule because multiple active policies would
produce contradictory classifier instructions. The outer output prompt owns
the single combined yes/no decision.

By default, the deployed/mock frontend still uses local mock policy data. To
switch local development to real FastAPI data, create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Then restart the frontend with `npm run dev:clean`. With the API base URL set,
`/policies` reads:

```text
GET /apps
GET /global-policy-assignments
GET /apps/by-client-id/{client_id}/effective-policy-assignments
```

Create is now backend-wired and duplicate-aware. In backend mode it performs:

```text
POST /global-policy-assignments/resolve
or POST /apps/by-client-id/{client_id}/policy-assignments/resolve
-> create a new definition or reuse an equivalent definition
-> return created, reused, or already_assigned
-> reload DB-backed policy assignments
```

The modal closes only after resolution succeeds and shows a visible result
notice. Delete removes only the app/global assignment; it does not delete the
reusable policy definition. Edit is now assignment-safe through:

```text
PUT /apps/by-client-id/{client_id}/policy-assignments/{assignment_id}/resolve
or PUT /global-policy-assignments/{assignment_id}/resolve
-> reuse an existing equivalent policy or create a new definition
-> switch only the selected assignment
-> leave every other app assignment unchanged
```

Assignments now have optional `display_name` values. Run
`python scripts/migrate_policy_assignment_display_names.py` after pulling this
schema change. Legacy duplicate definitions can be previewed with
`python scripts/deduplicate_policies.py` and applied with `--apply`.

Clicking a policy row now opens
`frontend/components/policies/policy-summary-modal.tsx`. The shared modal is
used by both `/policies` and `/apps/[clientId]` Policies, loads
`GET /policies/{policy_id}`, and shows connector/action/resource/custom-resource
metadata plus effect and status. Row Edit/Delete buttons stop propagation.

Direct `POST /policies` and `PUT /policies/{policy_id}` now return `409` when
the requested enforcement behavior is equivalent to another enabled policy.
Equivalence ignores description/name and compares normalized policy structure,
effect, priority, conditions, and enabled state.

FastAPI now enables local frontend CORS through `NEMO_CORS_ORIGINS`. The
committed default allows ports used by the local frontend:

```env
NEMO_CORS_ORIGINS=http://127.0.0.1:3000,http://localhost:3000
```

The modal stores optional custom resource text in
`conditions.custom_resource`. The compiler includes it in the NeMo input rule,
and `tool_guard.py` checks reviewed authoritative MCP fields/methods before execution.
Blank custom resources continue to apply to the whole action/resource class.
009c1 now validates new input selectors and stores canonical field equality text
with `resource_condition_version: 1`. Title/name case folds; path/branch case is
preserved. Legacy literal definitions are excluded from automatic reuse and
deduplication. 009c2c now uses field-bound execution rules from the same validated
snapshot as rails and attribution; indeterminate targets stop with controlled
evaluation errors. 009c3a backend assistant/options alignment is now applied;
009c3b frontend alignment is now applied; patch 010 is next.

`GET /policy-options` supplies the frontend policy builder from enabled
connector tool mappings. Its dropdown sequence is connector -> action -> valid
resource; SharePoint remains absent until it has executable mappings.

## Important Current Files

- `src/nemo_mcp_guardrails/app_auth.py`: API-key hashing and app verification.
- `src/nemo_mcp_guardrails/api/auth.py`: `require_authenticated_app`.
- `src/nemo_mcp_guardrails/api/runtime.py`: protected auth-check and run endpoints.
- `src/nemo_mcp_guardrails/api/runtime_schemas.py`: runtime request/execution response models.
- `src/nemo_mcp_guardrails/database/conversation_store.py`: conversation history load/append helpers.
- `src/nemo_mcp_guardrails/database/models.py`: includes `conversation_messages`.
- `src/nemo_mcp_guardrails/runtime_factory.py`: Azure, NeMo, MCP, and agent construction. It uses the authenticated app's `guardrail_llm_config_id` for NeMo rails and `main_llm_config_id` for the LangChain agent, with `.env` Azure fallback when either ID is missing.
- `docs/llm-provider-guide.md`: developer workflow for selecting Azure
  deployments and the implementation checklist for local/non-Azure providers.
- `src/nemo_mcp_guardrails/guarded_execution.py`: reusable single-request guardrail workflow.
- `src/nemo_mcp_guardrails/output_guard.py`: deterministic app-scoped quoted
  output phrase extraction and matching.
- `src/nemo_mcp_guardrails/tool_guard.py`: app-scoped execution-level MCP tool guard.
- `tests/test_nemo_mcp.py`: full read-only integration runner and terminal display.
- `tests/test_app_auth_http.py`: protected HTTP boundary and runtime-execution reachability test.
- `tests/test_guardrails_run_http.py`: app-scoped allowed/blocked `/run` HTTP integration test with fake rails/agent and real DB scope.
- `tests/test_runtime_connector_access.py`: isolated runtime connector access check for linked, unlinked, and disabled-link apps.
- `tests/test_app_connector_api.py`: app connector CRUD API test for app ID
  and client ID routes.
- `tests/test_runtime_connector_credentials.py`: env-based GitHub PAT
  reference resolution test.
- `tests/test_app_policy_scope.py`: real temporary app-assignment scope test.
- `tests/test_output_guard.py`: isolated explicit output phrase parser and
  matcher regression test.

## Verified Current Results

```text
service app authentication: passed
HTTP app authentication: passed
authenticated runtime execution reachability: passed
runtime LLM selection: passed
conversation history storage/reload/truncation: passed
oversized latest-message rejection: passed
controlled connector tool-error responses: passed
controlled Azure output-filter responses: passed
authenticated /run allowed/blocked app-scope HTTP coverage: passed
runtime connector access enforcement: passed
Linux AMD64 frontend port-80 image build: passed
non-root uid=1001 Next.js port-80 /login probe: passed
Linux AMD64 backend image rebuild after output-guard fix: passed
backend container API/database/frontend-proxy health: passed
container-native GitHub MCP readOnly=false manual probe: passed
explicit output phrase parser regression test: passed
temporary authentication rows cleanup: passed
temporary app policy-scope rows cleanup: passed
App A issue_write blocked / App B issue_write allowed: passed
tool guard isolated checks: passed
full read-only NeMo + GitHub MCP test: passed
Python compilation: passed
git diff --check: passed
```

The full runner still displays:

```text
NEMO INPUT RAIL RESULT
REQUEST STOPPED BEFORE ACTION EXECUTION, when blocked
MCP TOOLS CALLED, when allowed
NEMO OUTPUT RAIL RESULT
FINAL RESPONSE
```

The output looks unchanged because only coordination moved from the test loop
into `execute_guarded_message()`.

## Exact Next Implementation Step

Read `docs/open-work-backlog.md` first. It is the source of truth for
unfinished plans and prevents half-completed ideas from being lost between
machines.

Immediate top priority: finish verifying and hand off the corrected ACI image
pair. The corrected backend image is local and verified but not yet pushed.
The frontend management MVP, management JWT/RBAC, named LLM selectors, connector
management, policy management, and Runtime Test are already implemented.

```text
guardrail.azurecr.io/guardrail-fe:<matching-tag> -> public port 80
guardrail.azurecr.io/guardrail-be:<matching-tag> -> private port 8000
```

Build both Linux AMD64 images from the repository root:

```powershell
docker build --platform linux/amd64 -t guardrail-be:latest .
docker build --platform linux/amd64 --build-arg NEXT_PUBLIC_API_BASE_URL=/api/gms -t guardrail-fe:latest .\frontend
```

Verify the containerized local stack:

```powershell
docker compose up -d
Invoke-RestMethod http://127.0.0.1/api/gms/health
Invoke-WebRequest -UseBasicParsing http://127.0.0.1/login
```

Then push one matching image pair and give the deployment owner this ACI
contract:

```text
one Linux multi-container ACI group
public group port: 80 only
frontend process: 0.0.0.0:80
backend process: 0.0.0.0:8000, not publicly exposed
frontend GMS_API_BASE_URL: http://127.0.0.1:8000
external persistent PostgreSQL
runtime-injected secrets
```

Actual ACI resource creation remains with the supervisor's deployment team.
After deployment, validate login, policy CRUD, proxy health, and one guarded
GitHub request without a port suffix in the browser URL. Keep
`GITHUB_MCP_READ_ONLY=1` for scripted tests.

## Boundaries Not Yet Implemented

- Connector credentials and LLM credentials are not managed through a secrets
  manager yet.
- Argument-level and workflow-state policies are not implemented.
- TLS/custom-domain ingress, audit screens, and CI/CD publishing are not
  implemented yet.

## Editing Rules

- Preview exact non-doc code diffs and wait for user approval.
- Docs-only updates can be applied directly.
- Add short docstrings to new Python functions/classes.
- Update relevant docs after every completed change.
- Never commit `.env`, real API keys, PATs, or plaintext connector credentials.
