# Home continuation - 21 October 2026

This is the current home entry point. It supersedes older home instructions
that require connecting to Azure. The home laptop cannot reach the online
database; continue with its local database or isolated offline tests.
The [single backlog](open-work-backlog.md) owns implementation scope, and the
[acceptance record](work-acceptance-2026-10-21.md) contains detailed evidence.

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
