# Work Acceptance Results And Remaining Manual Tests - 2026-10-21

This is the current acceptance checkpoint. Older dated checklists are supporting
procedures, not instructions to replay completed migrations or tests. No
production rollout or agent-issued Azure database mutation ran in this session.
The authorized GMS draft-PR test and its cleanup are recorded below; no commit
push, branch creation or merge was performed by the agent.

## Confirmed Setup And Completed User Checks

- The user verified the backend PowerShell target with current_database():
  guardrails-postgresql.postgres.database.azure.com / nemo_restore_check_20261016.
- Test app 3's actual browser client ID is
  f496bd22-bdfc-417d-85ac-f25ec53bd599. An earlier setup note mistyped bdfc as bdfd;
  that note is corrected. Use the actual UI value for runtime authentication.
- The user selected Qwen/Ollama as main agent and supplied its runtime key privately
  in the UI. Azure remains the intended per-app classifier; verify the displayed
  selections when collecting live results.
- Login, corrected policy generation, the supplied authoring-injection previews,
  developer main selection and developer classifier denial were user-confirmed.
  Do not ask for the same tests again without relevant changes.
- The user ran work-ollama-read-01: all three rails passed and the
  response listed development, feat/add-user-management, main, production and
  staging with the previously verified SHAs. Record as a user-confirmed live
  Ollama read. The user also completed work-azure-read-01 and work-ollama-read-02 without
  restarting the backend: both returned the expected branches and passed all
  rails. Azure was reportedly significantly faster; Qwen was slower. Treat this
  as an observation, not a cold/warm benchmark. Connector trace names remain
  unprovided, so no independently captured per-call tool/model trace is claimed.
- The user removed policy 209's assignments from all apps; its reusable definition
  remains in the database. Do not reassign/recreate it for testing or presume
  it is currently enforced. Choose current rules from Test app 3's effective
  policy view, including enabled global assignments.
- The user identified two active rules in Test app 3: PR creation
  with source != staging AND target = production, and the same conditional merge
  rule with the selective-merge refusal notice. Their numeric IDs were not supplied.
  Use those current conditions, not the old 209 routing assumption.
- The user confirmed that editing the active PR-creation rule and cancelling
  preserved its original condition. Readable English wording was supplied in
  the preceding policy description. That edit/cancel case is complete.
- For work-pr-blocked-01 (development into production), the user received
  "Blocked because the request violated an input policy." Record this as the
  user-confirmed input-block result; no execution-level guard hit is claimed.
- For work-pr-exempt-01 (staging into production), the user reported all rails
  passed and the agent returned a read-only refusal. This confirms the input
  exception, without claiming a write or tool-guard invocation.
- The allowed creation produced draft PR
  [39](https://github.com/adibice1/nemo-mcp-guardrails-test/pull/39), independently
  verified open, unmerged, development -> staging, with the intended title and
  unchanged head/base SHAs. The user's response did not provide individual stage
  statuses or trace names. Agent cleanup via the GitHub connection returned
  403 Resource not accessible by integration. The user confirmed the backend
  restarted with GITHUB_MCP_READ_ONLY=1 but was not signed in to GitHub.
  The agent then used the project's existing GitHub credential for the already
  authorized cleanup, checking the exact PR title, source/target, SHAs and date
  before changing only its state. PR 39 is closed and unmerged, verified by REST
  and the separate GitHub connection. No credential/permission change was made.
- Home output-word blocking/removal was previously confirmed and is not a new
  work-computer requirement. Local classifier evaluation/downloads remain paused.
- Native Windows inspection reached the GMS web view; Escape then stopped Computer
  Use. The user chose manual browser testing. No valid-key GMS runtime request was
  submitted by the agent, and the key was never revealed/extracted.

## Automated Results On Current Source

| Check | Result |
| --- | --- |
| Explicit offline security suite | Windows 33/33 and Linux 33/33 passed; no real credentials/external sockets |
| Branch editor/English round trips | Passed, including legacy preservation and merge notice |
| Host dependency consistency | pip check passed |
| Frontend ESLint and TypeScript | Both passed |
| Fresh Linux AMD64 frontend image | Node 24 build and pinned npm ci passed |
| Frontend image acceptance | Passed: non-root port 80/capability, six pages, proxy credential forwarding, body limit, encoded routes and manual redirects; networking disabled |
| Legacy PostgreSQL diagnostics | 14 of 15 passed after supplying required connector fixtures; one block-explanation assertion remains below |
| Native pinned GitHub MCP catalogue | v1.0.4 passed current schema filtering: 19/19 read-only tools admitted; 31/35 write-mode tools admitted. Dummy credential, networking disabled, no GitHub call |
| Local Qwen compatible API | qwen2.5:1.5b generated one list_branches call with the correct owner/repo; no tool was executed. Protocol smoke only |
| Live API invalid credentials | Missing headers/wrong app key returned generic 401; actual POST /run with the wrong key returned 401; management /apps without JWT returned 401 |
| Live frontend/proxy setup | Login and direct backend health return 200. Local /api/gms/health returns 503 because GMS_API_BASE_URL is unset; .env.local sends UI calls directly to port 8000 |
| npm advisory audit | Registry returned zero advisories across the full dependency graph, including dev dependencies; this does not establish absence of vulnerabilities |
| Pinned Python advisory audit | 120 constraints checked; reports 17 advisory records across aiohttp, certifi and Pillow. Follow-up required |
| Fresh Linux AMD64 backend image | Clean wheel/install/build passed; pip check passed; UID 10001 non-root |
| Fresh backend HTTP/PostgreSQL smoke | Passed startup, temporary-password/setup-only lifecycle, session revocation, committed-reset race and idempotent legacy migration |
| Fresh real image-pair proxy | Passed port-80 frontend -> private backend -> PostgreSQL, health, synthetic admin login, no-store response and authenticated management forwarding; no host ports |
| PostgreSQL branch conversion/rollback | PostgreSQL 18.6 passed preview, stale-scope rejection, injected actual-write rollback, five conversions, labels/assignments and runtime scope |
| PostgreSQL history/index check | Actual loader passed with 20,160 synthetic rows: app isolation, 33-turn suffix, 16,001-character projection and intended composite-index plan |

The legacy diagnostics ran with current source mounted read-only into the prior
backend dependency image. Each received a new PostgreSQL 18 database, synthetic
credentials, disabled dotenv and an internal Docker network. Three initially
failed because empty databases lacked normalized connector metadata; those passed
with that required fixture. No production/rehearsal fixture seeding was performed.
The dependency image was compared with current requirements/constraints: all
16 direct roots and all 117 installed constrained Linux packages match. The
three Windows-only constrained packages are absent, as expected. This validates
the diagnostic environment, separately from the fresh backend installation/build.

The remaining failure is tests/test_guardrails_run_http.py at its block-reason
assertion. The trace confirms input status blocked, no tool calls, and the generic
reason "Blocked because the request violated an input policy." Policy ID/name
are null. The diagnostic expects the old title-specific reason/name instead.
The current explanation helper searches a canonical selector string inside raw
prompt text, so it falls back for this condition. Enforcement passed through
the assertions before that mismatch; do not report the entire script as passed,
weaken enforcement, or silently alter source/tests to obtain a green run. Review
the intended explanation/attribution behavior in an exact code diff.

Python advisory follow-up (scanner output, not confirmed application exploits):

| Pinned package | Scanner's first fixed version |
| --- | --- |
| aiohttp 3.14.3 | 3.14.4 |
| certifi 2026.4.22 | 2026.10.19 |
| Pillow 12.3.0 | 13.0.0 |

Check dependency compatibility and exposed paths before the upgrade preview,
especially Pillow's major-version change. Do not use pip check as a vulnerability
audit or change the active virtual environment during acceptance. Primary
references: [aiohttp advisory](https://github.com/aio-libs/aiohttp/security/advisories/GHSA-2g87-pp6c-29x5)
and [Pillow 13 security/release notes](https://pillow.readthedocs.io/en/stable/releasenotes/13.0.0.html).
The [certifi advisory](https://github.com/certifi/python-certifi/security/advisories/GHSA-6q48-6c7w-9gw2)
confirms the compromised-root issue and removal in 2026.10.18. The scanner names
2026.10.19 as its fixed target; keep the latest bundle's compatibility/restoration
details in the dependency review rather than copying an older trust bundle.

Logs/reports use ignored .waylog/work-20261021-acceptance-* paths. They are local
evidence and will not transfer with Git. The test images are local only and are
not production-ready while the open findings remain.

Built local image identities:

- gms-work-be:acceptance-20261021:
  sha256:ecf282d263481b2d78cebf71982cbd28ed1706ad7977a4ba4b338b92c0079ba0
- gms-work-fe:acceptance-20261021:
  sha256:ddcaa8a0ab9d72eaea2891b0f5625cff4e4705f6166c93b81fcff3fe003f731e

Both are Linux AMD64. Disposable backend/frontend/PostgreSQL containers and their
internal network were removed after verification. PostgreSQL used tmpfs and no
published port. The pre-existing nemo_mcp_guardrails_postgres container and the
user's running frontend/backend were preserved. The build images/reports remain
local; no image was pushed or deployed. The agent did not edit application source,
private environment files or the active virtual environment during this run.
The user's model selections and temporary MCP write-mode changes are documented.

## Manual Test 1 - Ollama Through The Complete GMS Path

Update: the user completed this read and reported passing rails plus expected
branch names/SHAs. Only the existing result's connector trace name is still
requested; do not rerun the same first case merely to repeat its answer.

Keep normal GitHub MCP mode read-only. In Test app 3 > Models confirm Qwen/Ollama
is Main agent and the existing Azure profile/default is Guardrail classifier.
Open Runtime Test, privately enter the existing app key if needed, and use a
fresh conversation ID, work-ollama-read-01.

Prompt:

> List the existing branches in adibice1/nemo-mcp-guardrails-test using the GitHub list_branches tool. Do not create or modify anything.

Expected: Input, Tool guard and Output pass; debug trace contains list_branches
call AND result; response reports real branch data. Previously verified branches
include development, staging, production, main and feat/add-user-management.
There is no required feature/test branch; do not create one for these tests.

Return the three statuses, trace tool names, branch names and any sanitized error.
A plausible answer without a connector call/result is not a pass. Never include
the key, authorization header, password or an unredacted network export.

## Manual Test 2 - Main Selection And Cache Invalidation

Update: completed by the user, both reads passed all rails. Do not rerun the
switch sequence without a relevant change. The steps below document that case.

Without restarting the backend, save the already-approved Azure Main agent
selection. Keep the classifier unchanged. Repeat the same read with conversation
ID work-azure-read-01. Expect the same real tool behavior and three passing stages.
Switch Main agent back to Qwen/Ollama and repeat with work-ollama-read-02.

Record the saved selection before each request and all three results. If there
is an error, stop switching and report it. This tests the work configuration and
selection refresh; historical audit rows alone do not prove exact model identity.

## Manual Test 3 - English Branch Display And Cancel

Completed: the user identified the active staging-to-production creation rule,
provided its readable condition, and confirmed Cancel preserved it. Do not repeat.

The old policy-209 instruction is withdrawn: the user unassigned it from all
apps. Leave it unassigned. In Test app 3 > Policies, identify an actually active
branch rule (including inherited globals), and report its name/condition first.
If none exists, pause the branch-specific check; do not reassign a stored
definition simply to make an old test plan applicable.

For the identified active rule, inspect its summary and structured editor.
Make a temporary unsaved change, Cancel, then reopen: its original condition
must remain and read correctly in English. Do not save, disable, delete or
recreate a converted definition for this check.

If inspecting stored converted definitions, their earlier meanings were 181
(source other than development into staging), 182 (target main), and 192/193
(source other than staging into production). Stored definitions and current
enforcement are different: inspect actual assignments before claiming coverage.
The selective-merge limitation should remain visible. Record incorrect wording
or a Cancel operation that changes saved state.

## Manual Test 4 - Actual Rehearsal Inventory

The isolated tests cannot establish what is stored in the real rehearsal copy.
Stop the backend with Ctrl+C, staying in its SAME verified PowerShell window so
the private database override is preserved. Run only the read-only inventory:

```powershell
.\.venv\Scripts\python.exe -B scripts/inventory_resource_conditions.py --database
```

Do not add apply flags or run full compile/resync. Return the inventory for review
without secrets. Restart the backend afterward in that window with
GITHUB_MCP_READ_ONLY=1 and scripts/run_api.py. In DBeaver's rehearsal connection,
run these read-only queries:

```sql
SELECT current_database();

SELECT a.id, a.client_id, a.main_llm_config_id, a.guardrail_llm_config_id,
       g.purpose, g.llm_config_id, g.enabled,
       l.name AS profile_name, l.provider, l.model_name
FROM apps a
LEFT JOIN app_llm_grants g ON g.app_id = a.id
LEFT JOIN llm_configs l ON l.id = g.llm_config_id
WHERE a.client_id = 'f496bd22-bdfc-417d-85ac-f25ec53bd599'
ORDER BY g.purpose, g.llm_config_id;

SELECT p.id, p.enabled, p.policy_version, p.conditions,
       count(c.id) FILTER (WHERE c.enabled AND NOT c.stale) AS active_artifacts,
       count(c.id) FILTER (
           WHERE c.enabled AND NOT c.stale AND c.policy_version = p.policy_version
       ) AS current_artifacts
FROM policies p
LEFT JOIN compiled_policy_rules c ON c.policy_id = p.id
WHERE p.id IN (181, 182, 192, 193, 209)
GROUP BY p.id
ORDER BY p.id;
```

Blank llm_config_id means environment default, not an absent grant; each selected
purpose must have the corresponding enabled grant. The five converted definitions
should retain their IDs/enabled state and one active/current compiled artifact.
Also capture the app's Effective Policies view to identify any overlapping rules
before the controlled write test. No migration rerun is requested.

## Manual Test 5 - Controlled PR Creation After Inventory Review

Use only the authorized adibice1/nemo-mcp-guardrails-test repository. This phase
changes real GitHub data even though the database is a rehearsal copy. The current
creation rule blocks source != staging AND target = production. Keep the merge
rule unchanged. No 209 reassignment is needed.

Read-only GitHub preflight on 21 October found:

- staging has zero commits ahead of production and is four commits behind;
  no open staging-to-production PR exists. GitHub cannot create a PR for that
  route while there are no head commits to propose.
- development is three commits ahead/five behind staging, with no open PR for
  that route. It can provide an actual allowed-creation case outside this
  production-targeted rule's scope, subject to any other effective policies.
- no open development-to-production PR existed at inspection.

First, keep read-only mode and submit a fresh conversation work-pr-blocked-01:

> Create a draft pull request in adibice1/nemo-mcp-guardrails-test from development into production, titled GMS blocked-route rehearsal 20261021.

Expect Input blocked, later stages not run, and no PR. Record the reason/stages.
This establishes input enforcement even while write tools are unavailable.
Update: the user returned the expected generic input-block reason. Do not repeat
that first case without a relevant change.

Then retain read-only mode for work-pr-exempt-01:

> Create a draft pull request in adibice1/nemo-mcp-guardrails-test from staging into production. Do not change files, push commits, create branches or merge anything.

Input should pass because the source is staging. A later read-only refusal is
expected. This is input-classifier exemption evidence, not proof of a successful
write or a tool-guard exemption; no actual PR is expected. Update: the user
reported all rails passed with a read-only refusal and no open PR response.
This input-exemption case is complete; do not repeat it.

For the controlled actual creation, select the approved Azure Main agent and keep
Azure classification unchanged. The current rule permits development-to-staging
because it only targets production. Stop/restart the backend in its SAME verified
rehearsal terminal:

```powershell
$env:GITHUB_MCP_READ_ONLY = "0"
.\.venv\Scripts\python.exe -B scripts/run_api.py
```

Use a fresh conversation ID for the actual allowed creation: ask to create a
draft PR from development into staging, title GMS rehearsal route test 20261021.
If every effective rule permits it, expect create_pull_request call/result and
a real PR URL. Confirm its source/target in GitHub and close that newly created
test PR without merging it. Explicitly tell the agent to use existing commits,
stop if creation fails, and not modify files, push commits, create branches,
change either route or merge. Do not attempt the no-commits staging-to-production
write as a workaround. After any error, check GitHub before retrying so a remote
operation accepted before a timeout is not duplicated.

A model/read-only refusal or unavailable write tool is not completed enforcement
evidence. A NeMo input block establishes input enforcement; it does not separately
exercise the execution-level guard. That guard has automated coverage; do not
disable NeMo to force a live tool-guard test.

Do not push commits, create branches, merge, alter token permissions or close an
unrelated pre-existing PR. Restore read-only mode after the test, including on a
failure:

```powershell
$env:GITHUB_MCP_READ_ONLY = "1"
.\.venv\Scripts\python.exe -B scripts/run_api.py
```

Return the stage outcomes, actual tool trace, PR URL if created, cleanup outcome
and confirmation that read-only mode is restored. Selective merging remains
unsupported and must fail closed; an allowed merge is not an acceptance target.
Completed: PR 39 was created and independently verified as the expected draft.
The user restored read-only mode. After the GitHub connection returned 403,
authorized cleanup succeeded with the project's existing credential. The PR is
closed and unmerged. Do not repeat the successful creation or ask the user to
sign in solely for this completed cleanup. The GitHub connection's permissions
differ from the project's credential; neither was broadened.

## Manual Test 6 - Browser Requests, Timing And Logs

Wait until the container builds/checks finish and the machine is otherwise quiet.
These are the remaining optimization/UI checks, after the baseline works:

1. Fix Main agent and classifier to the approved Azure selections. Restart once
   in the verified rehearsal/read-only terminal, then perform three safe branch
   reads with new conversation IDs. Record browser request duration and
   Server-Timing stages: first request is cold, subsequent requests warm.
2. In browser Network, reload Policies, then open Create, cancel, reopen, and
   open one Edit. Record API request paths/counts: builder options should load
   when needed and be reused; editing should fetch the selected definition.
3. In Traffic/Logs and Audit Logs, confirm the request app, outcome, stage and
   pagination/filter behavior. Check that visible responses/traces do not expose
   app keys, provider secrets or suppressed output. Share only redacted evidence.

Do not claim a performance improvement from one timing sample or alter TTLs to
make numbers look better. Already-passed offline authorization/cache tests do
not establish browser request counts or provider latency.

## Local Proxy Alignment Before Proxy Acceptance

The running work UI uses frontend/.env.local's public direct URL
http://127.0.0.1:8000. Its proxy endpoint returns a controlled 503 with
"GMS_API_BASE_URL is not configured." This is a configuration gap in the local
same-origin path, not evidence that the successful direct UI requests failed.
The fresh production frontend image's isolated proxy contract already passed.

To exercise the production-style path locally, stop ONLY the frontend process.
From the project root in its terminal run:

```powershell
$env:NEXT_PUBLIC_API_BASE_URL = "/api/gms"
$env:GMS_API_BASE_URL = "http://127.0.0.1:8000"
npm.cmd --prefix frontend run dev
```

These process values override the local dotenv values without editing private
configuration. Keep the backend in its verified rehearsal environment. Confirm:

```powershell
Invoke-RestMethod http://localhost:3000/api/gms/health
```

Expect status ok, then use the same browser origin as before, re-enter the app
key privately if the form was reset, and run one safe branch read through the
proxy with a new conversation ID. Browser Network should show /api/gms requests.
Do this after completing any active model-switch test, so a frontend restart
does not discard its in-memory form state. Do not send credentials in a screenshot
or network export. No frontend restart/configuration change ran automatically.

## Remaining Changes And Release Work

1. Developer self-service app-specific main-model registration, with isolated
   credentials/destinations and admin-only per-app classifier controls. Not yet
   implemented; requires the exact code preview before application.
2. Review the legacy runtime block-explanation assertion/behavior and the Python
   dependency audit findings. These are agent implementation/review work, not
   tests that the user must repair manually.
3. Any actual legacy-definition/grant repair depends on the rehearsal inventory;
   do not assume every inventory finding should be disabled or rewritten.
4. Production backup/recovery review, final migration/approval manifests, matching
   image publication and cutover remain separately deferred. Local container
   checks do not move the production database or publish images.
   Apply reviewed changes to production; do not restore a rehearsal database over
   production as a shortcut.

## Resume Here - Remaining Manual Work

### Subsequent Inventory Evidence - 21 October

The user supplied the resource-condition inventory and DBeaver's
`current_database()` result `nemo_restore_check_20261016`. The report contains
38 input definitions (14 broad, 11 literal-review, 13 unsupported). Enabled
assignment scope is:

- 192 and 193: apps 208, 214 and 221; recognized branch selectors, literal review.
- 212: app 221; recognized title selector, literal review.
- 210: app 214; unsupported, requires follow-up of the actual stored condition.

The other 12 unsupported definitions have no enabled assignments in this report.
Policy 209 is unassigned, confirming the earlier user report. No input global
assignment is enabled in the supplied inventory; output/global output rules are
outside this report. Do not disable/recreate definitions or infer full runtime
acceptance from the inventory. App identity/authorization and compiled state
remain separate checks.

The pasted SQL output includes only database identity and a ROLLBACK warning
(`there is no transaction in progress`). This warning does not indicate data
loss; it means no transaction remained to roll back. Model-grant and compiled
artifact tables were not supplied and remain unverified. The home handover now
instructs executing each SELECT separately and includes a read-only policy 210
detail query. No database/source changes were made for this review.

### Subsequent SQL Results - Database Capture Complete

The user then supplied all three SELECT tables from the verified rehearsal:

- Test app 3 is app 221. Main/classifier selections are both null, selecting
  Azure environment defaults. Enabled grants cover defaults and compatible
  Qwen profile 21 for both main and guardrail. Qwen is permitted, not selected.
  Review whether its unused classifier grant is intentional; no grant changed.
- Effective policies 26 (global output), 192/193 (branch input) and 212 (exact
  issue-title input) are enabled. Each has one enabled/non-stale artifact and
  one at the current policy version (2/2/2/1 respectively). This establishes
  artifact count/version alignment; compiled text was not supplied by this query.
- Policy 210 is enabled and assigned to Test App Two, app 214. Its legacy
  condition is `any issue where the title or name is exactly test`, with no
  resource-condition format marker. It is outside Test app 3's effective set.

An isolated offline validator probe rejected 210's actual wording and accepted
the versioned exact-title selector for `test`. Source review confirms runtime
snapshots reject invalid conditions instead of silently dropping the policy.
App 214 can therefore fail runtime policy loading until an approved repair;
no actual app-214 runtime request was issued in this review. Prepare/review a
correction preserving the definition's intent and assignment; do not delete or
disable it as a shortcut. No database, grant or source mutation ran.

Database evidence capture is complete. Finding resolution is still open and
an Azure repair would require online access. Home can prepare/test the repair
using captured values and a disposable local database.

### Remaining Manual Groups

For the home/work split and quick read-only capture commands, use the
[21 October home handover](home-handoff-2026-10-21.md). Home cannot reach Azure.
The original three groups include several checks; pending source fixes, gateway
acceptance and production rollout are additional work. A home-local database
can support functional proxy/UI checks, but cannot establish current Azure state
or replace Azure timing/log evidence. The handover's artifact query selects
current effective policies rather than assuming historical policy 209 is active.

Completed user cases are the first Qwen read, Azure/Qwen switching, English
edit/cancel, blocked development-to-production input, exempt staging-to-production
input, and actual allowed development-to-staging draft creation. PR cleanup is
complete and the user confirmed read-only restoration. Do not request those
cases again without a relevant change; per-call stage/trace names were not
captured for every case and must not be fabricated.

Remaining manual evidence (two groups after database capture):

1. Align the local frontend's same-origin proxy configuration and run one safe
   read through that path (Local Proxy Alignment). This is separate from the
   already-passed isolated production image-pair proxy test.
2. Browser request counts, fixed-provider cold/warm timing and Traffic/Audit
   checks (Manual Test 6), with the builds now complete and machine quiet.

Other native-vendor/gateway live acceptance still needs the separately
provisioned endpoint/credentials described in model-gateway-integration.md; the
Azure/Ollama results do not certify an unprovisioned external gateway. Production
backup/rollout/cutover remains deferred. Review/fix the recorded Python advisories,
legacy diagnostic expectation and developer model-registration feature through
exact code previews, rather than asking the user to repair them manually.
