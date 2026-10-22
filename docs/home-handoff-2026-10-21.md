# Home continuation - 21 October 2026

## Superseded by the post-presentation handover

Start with [the 22 October home handover](home-handoff-2026-10-22.md).
Actual work timing/tool/audit verification, the approved app 214 assignment reuse,
app 221's retain-Qwen decision and work dependency alignment are complete.
The pending descriptions below are historical, not instructions to repeat those
actions. Current remaining work and environment boundaries are in the new handover.

## Latest readiness follow-up - 22 October 2026

All requested unconditional home checks are complete. The user's pushed source
passes hosted CI (both jobs, 38 offline and 16 PostgreSQL checks); the rebuilt
local image, real proxy status smoke and synthetic backup/key-recovery rehearsal
also pass. See [the latest results and remaining boundaries](home-readiness-results-2026-10-22.md).
Actual work policy/grant/timing and conditional provider/production checks remain
separate. Older pending home instructions below are historical.

## Home verification complete - 22 October 2026

All four current home verification groups are completed under the user's
explicit autonomous authority. The final Linux backend image passed 35 offline
checks; 16 PostgreSQL diagnostics, migration/idempotency/constraint checks and
real model registration/RBAC/native-MCP image-pair reads passed. The explanation
assertion failure is fixed. The final frontend image builds on pinned Node 24
and serves the loopback proxy on non-root port 80. Model guides now describe the
shared API Type-first form, Provider API key main registration and admin-only
Advanced credentials. See [the final results](home-verification-results-2026-10-22.md).

The original home PostgreSQL container remains healthy on 5433; the home app
selections, private .env/key, host venv and running servers were preserved.
Restart only the Windows backend in its same verified terminal to load saved
source (reload=False). Test containers/networks were removed; images stay local.
Older pending profile/schema/key/browser descriptions below are historical;
work-network findings and production/gateway acceptance remain separate.


## API-type-first UI applied - 22 October 2026

The user approved the exact one-file form correction with "ok". The applied
modal matches its reviewed hash. API Type is the first field for both roles;
default endpoint/API-key fields match. Admin backend-credential selection is
inside collapsed Advanced credentials, with developer main-only access retained.
Applied TypeScript and full ESLint passed. Earlier synthetic rendering verified
matching default forms and hidden/collapsed role-specific controls. No backend,
database, private environment or model selection operation ran for this change.
The user previously reported saving the developer Ollama profile; its live
guarded runtime test remains the next acceptance step. The preview-only section
below is historical.


## Unified model-profile UI applied - 22 October 2026

User approval "ok" applied the reviewed three-file UI correction. Models uses
one Add model profile button, aligned to the far right of Save model selections.
Developers enter their own endpoint/key and receive main-only access; admins
have the backend-credential path in the same form for main/classifier profiles.
TypeScript, full ESLint and both targeted registration/grant checks passed on
applied source. User refresh/layout and live developer registration acceptance
remain pending. Existing home schema/key setup was user-completed; no new
database or private environment operation ran for this UI change.


## Model-profile UI follow-up - 22 October 2026

The user confirmed the encryption key was saved privately and the model button
was visible after the restart/refresh. Do not regenerate or request that key.
They requested replacing the two add buttons/forms with one right-aligned
Add model profile action. A three-file frontend preview is prepared and checked,
but awaits exact-diff approval. Developers get main-only endpoint/key
registration; admins retain backend-credential classifier provisioning in the
same form. New model creation/live provider acceptance remains pending. See
[the current review](developer-main-model-registration-review.md).


## Home schema applied by user - 22 October 2026

The user ran scripts/migrate_app_main_models.py --apply with expected database
nemo_restore_check_ollama_20261020_153213 and supplied the successful verified-
rehearsal completion message. Record the home PostgreSQL schema application as
user-confirmed. This does not establish a second-run idempotency test or a
production migration. The next step is private encryption-key provisioning;
the backend is to remain stopped until setup is complete. Older no-migration
statements below describe the preceding source-only application checkpoint.


## Approved source application - 22 October 2026

The user approved the developer main-model registration patch with "ok". All 17
source/config/test files are applied and match the reviewed hashes. Existing
backend/frontend processes were not restarted. The schema helper ran only in
no-connection preview mode; the home database and private .env are unchanged.
Before restarting the backend, continue with reviewed home schema/key setup;
see [the applied feature record](developer-main-model-registration-review.md).
The older preview-only checkpoints below are historical.

This is the current home entry point. It supersedes older home instructions
that require connecting to Azure. The home laptop cannot reach the online
database; continue with its local database or isolated offline tests.
The [single backlog](open-work-backlog.md) owns implementation scope, and the
[acceptance record](work-acceptance-2026-10-21.md) contains detailed evidence.

## Home verification update - 22 October 2026

Home proxy health, authenticated safe runtime read with actual list_branches
events, lazy/reused policy options, selected-policy GET and Audit filtering are
now recorded in the home startup checkpoint below. User supplied three Azure-
selected timing samples (10.13 s, 6.71 s, 5.90 s). Timing detail, warm stage
confirmation and timing attribution remain narrow evidence gaps; Qwen restoration
and final pagination acceptance were subsequently user-confirmed. The original checklist below predates these home results. Implementation
findings, Azure-specific verification and release work remain open.

## Developer model registration preview - 22 October 2026

The user chose entering an endpoint and API key for app-specific main models.
An isolated 17-file source preview is ready, with encrypted app-owned keys,
main-only registration, app/purpose isolation and a rehearsal-only schema helper.
All 34 preview offline checks, TypeScript, full ESLint and patch applicability
passed. Active source, private .env and databases are unchanged. See the
[review and verification limits](developer-main-model-registration-review.md).
Exact code approval is still required before applying the preview.

## What remains

The original manual checklist had **three groups**, not three individual tests.
The database capture/review is now complete, with a policy 210 repair finding
and an unused Qwen classifier grant to review. Two other manual groups remain;
implementation, finding resolution and release work are additional tasks.

| Remaining group | Database needed? | What can be done at home? |
| --- | --- | --- |
| Azure rehearsal inventory, model grants and compiled versions: captured/reviewed; findings below | Capture used Azure; applying any approved repair there will also require Azure | Prepare/review a repair offline from the captured data. Do not repeat completed capture. |
| Local same-origin proxy configuration and one authenticated safe runtime read | Proxy health alone needs no database; login/runtime needs a database | Complete against the home local database and its own app/key/provider configuration. The isolated production image-pair proxy test already passed. |
| Browser request counts, cold/warm timings, Traffic/Audit filters and pagination | Yes for authenticated workflows and logs | Local functional checks can run at home. Actual Azure timings and online rehearsal log evidence must be captured at work. These are several checks within one group. |

Separate implementation work remains: developer-added app-specific main models,
Python dependency advisory remediation, and review of one legacy PostgreSQL
diagnostic's block-explanation expectation. These can be developed/tested at
home without Azure, using offline tests and disposable local PostgreSQL where
needed. Preview exact non-doc diffs in chat and wait for approval before editing.
Do not weaken a failing assertion without reviewing the intended behavior.

External vendor/gateway acceptance needs a separately provisioned endpoint.
Production backup/recovery review, target-specific rollout and image publication
remain deferred; production has not been migrated or deployed.

## Quick checks before leaving work

Update: the user supplied all three SELECT result tables as well as the
inventory and correct database identity. Required database capture is complete;
the commands below are retained for reference, not a request to repeat it.

### Reviewed results

- Test app 3 is app **221**. Both selected model IDs are null: current runtime
  selection is the Azure environment default for main and classifier, consistent
  with the last controlled write test selecting Azure main.
- Enabled grants exist for both purposes for the default and profile **21**
  (`qwen2.5:1.5b`, `openai_compatible`). The Qwen classifier grant permits that
  choice but does not select it. Admin-only selection remains the intended
  boundary. Review whether that unused classifier grant is intentional; no
  grant was revoked and no Qwen classifier acceptance is implied.
- Effective policies **26, 192, 193 and 212** are enabled and each has exactly
  one enabled/non-stale compiled artifact at its current policy version. Policy
  26 is globally assigned output protection (version 2); 192/193 are the
  non-staging-to-production branch restrictions (version 2); 212 is the exact
  issue-title `test` restriction (version 1). These counts establish version
  alignment, not independently verified compiled text or all runtime behavior.
- Policy **210** belongs to **Test App Two, app 214**, with its definition and
  assignment enabled. Its stored wording is `any issue where the title or name
  is exactly test`, version 1 without a resource-condition format marker. The
  current validator rejects it. It is not among Test app 3's effective policies.
  Review a correction preserving its exact-title intent and assignment; do not
  delete it or silently disable enforcement.
- An offline validator probe reproduced rejection of 210's stored wording and
  accepted an explicitly versioned exact-title selector for `test`. The runtime
  snapshot loader rejects unsupported conditions instead of ignoring them, so
  app 214 can fail policy loading until repaired. No live app-214 request was
  issued. No database, grant or source change was made.

The inventory contains 38 input definitions: 14 broad, 11 literal-review and
13 unsupported. Only four definitions have enabled assignments: 192/193 to
apps 208/214/221, 210 to app 214, and 212 to app 221. Policy 210 is unsupported
and needs review before that app's acceptance/rollout; the other 12 unsupported
definitions are unassigned. Policies 192/193 are recognized branch selectors;
`literal_review` alone does not indicate an enforcement failure. Policy 209 is
unassigned as intended. This input-only report does not inventory output rules,
prove app authorization, validate model grants or establish compiled freshness.

No further database capture is required to continue source work at home. The
remaining browser/proxy checks below are optional before leaving. An approved
repair applied to the online rehearsal remains a future work-network task.

### 1. Capture the read-only inventory

Use the **same verified PowerShell window that runs the backend**, from the
project root. Its process environment targets:

- Host: `guardrails-postgresql.postgres.database.azure.com`
- Database: `nemo_restore_check_20261016`

Stop the backend with Ctrl+C, then run:

```powershell
New-Item -ItemType Directory -Force .waylog | Out-Null
.\.venv\Scripts\python.exe -B scripts/inventory_resource_conditions.py --database |
    Out-File -Encoding utf8 .waylog/work-20261021-rehearsal-inventory.json
if ($LASTEXITCODE -ne 0) { throw "Inventory failed; do not treat the output as evidence." }
notepad.exe .waylog/work-20261021-rehearsal-inventory.json
```

The script explicitly uses a read-only transaction. Run it in the existing
verified window: another terminal may fall back to root `.env` and inspect the
wrong local database. Restore the backend even if capture fails:

```powershell
$env:GITHUB_MCP_READ_ONLY = "1"
.\.venv\Scripts\python.exe -B scripts/run_api.py
```

The JSON intentionally includes unassigned definitions. A `literal_review` or
`unsupported` flag needs interpretation alongside enabled assignment scope; it
does not by itself mean an active policy failed. Policy 209 remains unassigned;
do not reattach, disable or recreate it to make an inventory look clean.

### 2. Capture selected grants and current effective artifacts

In DBeaver, use a SQL editor connected to the Azure rehearsal database. Run the
first query and confirm its result before running the rest:

```sql
SELECT current_database();
-- Expected: nemo_restore_check_20261016
```

Run each following SELECT separately: select the full query through its final
semicolon, execute it, and copy that result table. If DBeaver already ran the
whole script, check its separate result tabs. Seeing only `current_database()`
and `ROLLBACK` output does not establish that these result tables were captured.
These SELECTs need no explicit BEGIN/ROLLBACK; a previous warning that there is
no transaction in progress means there was nothing for ROLLBACK to undo.

The first two queries target Test app 3 by its work client ID rather than
assuming a numeric app ID or an old policy ID:

```sql
SELECT a.id, a.client_id, a.main_llm_config_id, a.guardrail_llm_config_id,
       g.purpose, g.llm_config_id, g.enabled,
       l.name AS profile_name, l.provider, l.model_name
FROM apps a
LEFT JOIN app_llm_grants g ON g.app_id = a.id
LEFT JOIN llm_configs l ON l.id = g.llm_config_id
WHERE a.client_id = 'f496bd22-bdfc-417d-85ac-f25ec53bd599'
ORDER BY g.purpose, g.llm_config_id;

SELECT p.id, p.description, p.policy_type, p.enabled, p.policy_version, p.conditions,
       EXISTS (
           SELECT 1 FROM global_policy_assignments g
           WHERE g.policy_id = p.id AND g.enabled
       ) AS globally_assigned,
       count(c.id) FILTER (WHERE c.enabled AND NOT c.stale) AS active_artifacts,
       count(c.id) FILTER (
           WHERE c.enabled AND NOT c.stale AND c.policy_version = p.policy_version
       ) AS current_artifacts
FROM policies p
LEFT JOIN compiled_policy_rules c ON c.policy_id = p.id
WHERE EXISTS (
    SELECT 1 FROM global_policy_assignments g
    WHERE g.policy_id = p.id AND g.enabled
) OR EXISTS (
    SELECT 1 FROM app_policy_assignments ap
    JOIN apps a ON a.id = ap.app_id
    WHERE ap.policy_id = p.id AND ap.enabled
      AND a.client_id = 'f496bd22-bdfc-417d-85ac-f25ec53bd599'
)
GROUP BY p.id
ORDER BY p.id;

-- Inspect the one unsupported input definition with an enabled assignment.
SELECT a.id AS app_id, a.name AS app_name, a.client_id,
       ap.enabled AS assignment_enabled,
       p.id AS policy_id, p.description, p.enabled AS policy_enabled,
       p.connector, p.action, p.resource, p.conditions, p.policy_version
FROM app_policy_assignments ap
JOIN apps a ON a.id = ap.app_id
JOIN policies p ON p.id = ap.policy_id
WHERE ap.app_id = 214 AND ap.policy_id = 210;
```

Keep the result tables and inventory privately for review at home; do not export
credentials, API keys, password hashes or full connection settings. A null model
selection means the environment default, so compare purpose/default grants as
well as named profiles. No rows or unexpected artifact counts require review,
not automatic repair. Findings are now recorded in the acceptance record.

### 3. Optional if time permits

Allow roughly 2-5 minutes for proxy setup/health, plus a safe authenticated read.
Follow [local proxy alignment](work-acceptance-2026-10-21.md#local-proxy-alignment-before-proxy-acceptance).
Restart only the frontend; keep the backend in its verified rehearsal window.
Proxy health alone does not complete the valid-key/runtime check.

The browser/timing/log bundle may take 10-20 minutes or longer, depending on model
latency. See [Manual Test 6](work-acceptance-2026-10-21.md#manual-test-6---browser-requests-timing-and-logs).
If leaving soon, capture inventory first and defer this bundle. Mark Azure
measurements pending rather than substituting home-local timings for them.

## Home startup checkpoint - 21 October 2026

- User confirmed the home PostgreSQL container is healthy on host port 5433 and
  the restored `nemo_restore_check_ollama_20261020_153213` database exists.
  Backend startup was reported complete; application database identity has not
  been independently queried through that backend.
- Home Node is 22.15.0 and npm is 11.3.0. Existing frontend node_modules held
  Next.js 13.5.11 while package.json/lockfile specify 16.4.2. User completed
  `npm.cmd --prefix frontend ci`; local package inspection confirms Next 16.4.2.
  The earlier Next 13 startup reported changing tsconfig.json JSX to preserve;
  review generated/configuration differences before treating source as unchanged.
- User full npm audit now reports seven high-severity package entries rooted
  in braces advisory GHSA-vfj7-8cjw-p6xm. Locked affected packages are marked
  development-only through Tailwind and Next ESLint tooling. The advisory lists
  no patched braces version at review. No forced upgrade was performed.
- User `npm.cmd --prefix frontend audit --omit=dev` reports zero vulnerabilities.
  This is a production-dependency scanner result, not closure of the full
  development audit or proof about the contents of a newly built image.
  The earlier work zero-advisory report is historical evidence; retain this
  home finding as open alongside the Python advisory backlog.
- User restarted the frontend successfully with Next 16.4.2 and the process
  settings `NEXT_PUBLIC_API_BASE_URL=/api/gms` and
  `GMS_API_BASE_URL=http://127.0.0.1:8000`. Next reported JSX configuration
  changed to react-jsx. The user opened `/api/gms/health` and received
  `{"status":"ok"}`.
- With Qwen2.5 1.5B main and Azure environment-default classification displayed,
  the user reported the safe branch read passed all stages and returned
  development, feat/add-user-management, main, production and staging. Record
  the home authenticated read under the configured proxy as user-confirmed.
  Subsequent Traffic evidence below supplies the per-call execution events;
  model identity is still inferred only from the displayed selection, not logged
  independently per call.
- User checked Policies Network with the policy-options filter: zero requests
  on reload, one after first Create, still one after Cancel/reopen. This confirms
  lazy option loading/reuse for this home browser session.
- User opened Edit and captured GET `/api/gms/policies/5` with status 200 and
  Server-Timing `gms;dur=42.8`. Saved-field rendering was not separately confirmed;
  that management-request timing is not a runtime/model benchmark.
- After an authentication header was accidentally shared, user confirmed the
  instructed home-account password change and sign-in steps were complete.
  No credential or token is retained in these notes.
- User supplied Traffic details for app 33, conversation
  `home-proxy-read-20261021-01`, request
  `eeb8c322dafe4a959a312c2e2f9e3eae`: HTTP 200, passed, total 28447.5 ms.
  Input rail passed (1535.0 ms); list_branches tool guard passed (0.2 ms),
  tool started/returned (1421.7 ms); agent/tools returned (21338.7 ms); output
  phrase check returned and output rail passed (1289.1 ms). Tool duration is
  included in agent/tools duration, not an additional independent phase.
  This establishes actual tool execution, not merely a plausible response.
  User reported the Traffic check passed; exact pagination state was not supplied.
  One request does not establish cold/warm performance or a model benchmark.
- On 22 October (Singapore), user supplied Audit rows with actor/action/route,
  entity, UTC timestamps and succeeded outcomes. A subsequent filtered view
  showed two llm_config.created entries with entity llm config and succeeded
  outcome; the user reported it passed. Record Audit loading and the supplied
  entity/outcome filtering as user-confirmed. No new management operation was
  requested or executed for this log check.
- On 22 October (Singapore), user confirmed saving Azure environment-default
  main with Azure classification retained and restarting the read-only backend.
  For the same safe branch-list prompt with new conversation IDs, user reported
  10.13 s for the first request after restart (all stages passed), followed by
  6.71 s and 5.90 s for warm requests; warm mean 6.305 s. The two warm stage
  results were not separately restated. Timing source was not identified in
  the replies; no Server-Timing breakdown was supplied. These are three home
  samples under the reported fixed selections, not independently traced model
  identity, Azure rehearsal measurements or proof of general performance gains.
  User subsequently confirmed saving Qwen2.5 1.5B main again; Azure classifier
  remained the requested unchanged selection.
- User subsequently confirmed the final Traffic/Audit pagination check was all
  fine. Record user-confirmed pagination acceptance, without inventing which
  arrows were enabled or how many pages existed. Home browser functional checks
  are complete; detailed timing attribution and explicit warm stage results were
  not separately supplied. Do not repeat completed cases to fill those details.
- After the dependency refresh, agent ran current home frontend TypeScript
  (no emit/no incremental writes) and full ESLint; both passed on 22 October.
  Azure-specific timing/log evidence remains work-network-only.

## Resume on the home laptop

1. Transfer the actual source and docs changes. A Git pull does not include
   uncommitted or untracked files. Review `git status --short` on both machines;
   commit/push reviewed files yourself or transfer them through your private
   workspace process. No commit or push was performed for this handover.
2. Include the modified `src/nemo_mcp_guardrails/api/policy_assistant.py`,
   **new `src/nemo_mcp_guardrails/api/policy_assistant_branches.py`**, modified
   `tests/test_policy_assistant_http.py`, and all new/updated handover docs.
   Do not copy only a patch that omits the new helper. Do not replay historical
   conversion manifests or old review patches against the current source.
3. Keep private `.env`, database archives, credentials and `.waylog` reports out
   of Git. `.waylog` evidence and local Docker images do not transfer with Git;
   the acceptance record summarizes their results. Do not copy `.venv`,
   `node_modules` or `.next` between machines.
4. For home runtime/UI work, use home-local PostgreSQL on host port **5433**.
   The last recorded restored home database is
   `nemo_restore_check_ollama_20261020_153213`. Verify that it exists and confirm
   the actual host/port/database privately before starting the API. Clear a stale
   terminal Azure override only after checking home configuration. Do not copy
   the work terminal's `DATABASE_URL` into home setup.
5. The home snapshot is separate from Azure rehearsal
   `nemo_restore_check_20261016` and production `nemo_mcp_guardrails`. Work app IDs,
   keys, profiles, policies and recent logs are not automatically present at home.
   Inspect the local app and its effective assignments before choosing test data.
   No new database dump is needed for the next offline implementation work.
6. Keep `GITHUB_MCP_READ_ONLY=1`, with a local main model and the configured
   classifier as appropriate. Classifiers remain **per-app and admin-only**;
   developers must eventually be able to add/use their own app-scoped main models.
   Do not broaden global credential/destination access to implement that feature.
7. Continue the pending source work from the backlog, review exact diffs, and run
   relevant offline/disposable-database checks after changes. The full baseline
   has already been tested; avoid repeating completed live cases without a
   relevant source/configuration change.

## Completed evidence to preserve

- Login, corrected authoring, supplied injection previews and English edit/cancel
  passed user testing. Developer main selection/admin-only classifier behavior
  passed; developer model creation itself is still missing.
- Qwen -> Azure -> Qwen safe reads passed without a backend restart. Azure was
  faster in the user's observation; this was not a controlled timing benchmark.
- Development -> production input was blocked; staging -> production input passed
  with a later read-only refusal. These are input-policy checks.
- Actual development -> staging draft PR
  [39](https://github.com/adibice1/nemo-mcp-guardrails-test/pull/39) was created,
  independently verified, then closed without merging. Cleanup is complete and
  the user confirmed the backend was restarted read-only. Do not repeat the write.
- 33/33 offline checks passed on Windows and Linux, as did fresh frontend/backend
  image builds and isolated real PostgreSQL/image-pair proxy checks. Broader
  legacy PostgreSQL diagnostics were 14/15: one explanation-attribution mismatch
  remains. The Python audit recorded 17 advisory records across aiohttp, certifi
  and Pillow; dependency remediation remains open. See the acceptance record for
  versions, limitations and evidence. No production deployment ran.
