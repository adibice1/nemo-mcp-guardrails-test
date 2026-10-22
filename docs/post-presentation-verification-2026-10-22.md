# Post-presentation verification - 22 October 2026

The user resumed testing after the presentation and selected **Test app 3**.
Work-environment automation is complete for the access supplied. The approved
Test App Two policy repair and work virtual-environment updates are applied.
Production rollout remains separate; use the [deployment checklist](deployment-checklist-2026-10-22.md)
for its remaining gates. Earlier presentation deferrals are historical.

## Environment and scope

- Source HEAD: `6a8b355` (presentation documentation); application source remains
  the previously CI-tested `5f84cffe`. No application source was edited here.
- Actual database identity verified directly, using read-only inspection:
  `guardrails-postgresql.postgres.database.azure.com` /
  `nemo_restore_check_20261016`. No production database was touched.
- Live HTTP requests used the running Next.js same-origin proxy at
  `http://localhost:3000/api/gms`, app 221, client ID
  `f496bd22-bdfc-417d-85ac-f25ec53bd599`.
- Both selected models remain the explicitly approved Azure environment defaults.
  Main/classifier selections and model grants were not changed. The user chose
  to **retain** Test app 3's unused Qwen classifier approval.
- GitHub MCP remained read-only. Only branch reads and a no-tool prompt ran;
  no GitHub write was attempted. A read-only repository check found no open PRs
  targeting production at inspection time.

## Complete verification map

Counts below describe diagnostic scripts/groups, not the number of individual
assertions. Previously accepted checks remain accepted; they were not all rerun
against the work database.

| Coverage | Result and evidence |
| --- | --- |
| Offline regression catalogue | **38 passed, 0 failed** in the work Windows venv after the approved dependency installation. Covers authorization, credentials/endpoints, policies/compiler/snapshots, branch routing, tool enforcement, fail-closed classifiers, authoring, cache/grant handling, privacy, logging and timing. Exact scripts are listed below. |
| PostgreSQL integration catalogue | **16 passed, 0 failed**, plus schema/idempotency/constraint/cascade checks, already accepted from home and hosted CI. Preserved that acceptance; did not run disposable fixtures inside the shared Azure rehearsal. |
| Frontend and Linux images | Prior locked frontend install/lint/TypeScript/build and pinned backend image verification remain accepted from home/CI. No frontend source changed here; no registry publication or deployment ran. |
| Live health and authentication boundary | Six checks passed through the work proxy: API health, database health, management request without JWT, runtime auth without key, runtime run with invalid key, Traffic endpoint without JWT. Expected 200/401 responses and request-ID/timing headers verified. Valid app-key auth also passed. |
| Actual work schema | Both owned-model columns, both expected constraints and owner index confirmed. No migration repeated. |
| Effective policy consistency | Exact stored compiled content validated, not merely artifact counts. Test app 3 policies 26/192/193/212 have current matching artifacts. All six authorized rehearsal apps' policy snapshots now validate after the approved repair. |
| Selected-model approvals | Test app 3's default main/classifier grants validate. Inventory checked every authorized app; exceptions for apps 208/222 are below. |
| Real safe reads | Three fixed-model requests before package alignment and one after it all passed Input/Tool guard/Output. Persisted `list_branches` start/return events prove actual tool execution. Expected branch names were present; no write-tool calls were recorded. The response's `tool_names` lists calls, not the advertised catalogue; read-only configuration was checked separately. |
| No-tool status | Real plain answer passed; Tool guard correctly reports `not run`, with zero tool starts. |
| Existing blocked requests | Stored input-block events for app 221 verified, with zero tool starts. User had already confirmed the block and Traffic visibility; no duplicate block request was needed. |
| Management audit persistence | Existing successful app creation/update, connector setup, policy assignment, model approval, API-key regeneration, user creation/link and password-change audit records verified using metadata only. |
| Repaired exact-title rule | User-approved assignment reuse committed and verified; six real-policy matcher cases pass. Full app 214 HTTP/input-classifier acceptance is not claimed without that app's API key. |
| Work encryption key | Six in-memory synthetic checks passed: correct-key roundtrip, missing/wrong-key rejection, restored-key success, other-app rejection, classifier-scope rejection. No stored owned profiles exist in this rehearsal, so actual stored-profile decryption was not exercised. |
| Dependency alignment | Installed approved pins `aiohttp==3.14.5`, `certifi==2026.10.19`, `yarl==1.25.1` after the user stopped the backend. All **120** host constraints now match, no missing packages; `pip check` passes. Source constraints unchanged. |
| Recovery and live feature history | Home synthetic PostgreSQL dump/restore/key recovery and earlier browser/RBAC, model registration/switching, English edit/cancel, input-routing and controlled PR creation/closure acceptance remain accepted. No reason to repeat them here. |

The [home readiness report](home-readiness-results-2026-10-22.md) records the
image identities and hosted CI evidence. These passing tests do not resolve
the recorded Pillow/FastEmbed compatibility finding or development-only braces
finding; see the [dependency review](python-dependency-review-2026-10-22.md).

## Measured work reads

Same safe `list_branches` prompt, fresh conversations, Azure main/classifier
fixed. These are agent HTTP measurements through the real frontend proxy,
not browser rendering/DevTools timings and not a cross-provider benchmark.

| Request | Client HTTP duration | Server-Timing total | Request ID |
| --- | --- | --- | --- |
| First read after earlier user restart, before package update | 48.552 s | 48.481 s | `9b42a7e525344810879a77bd480fa472` |
| Following read 1, before update | 13.064 s | 13.011 s | `d80efc507cf14a7589232faf537a75b9` |
| Following read 2, before update | 12.665 s | 12.627 s | `6cd44f632f9c4854828df138ecd69b7d` |
| First read after package update and agent restart | 27.015 s | 26.930 s | `9ec6ccd9859f4f989f607b01310eaa55` |

The last request's matching backend timing record supplies stage attribution:
history load 0.260 s; runtime setup 17.555 s; input rail 1.651 s; agent/tools
3.877 s; deterministic output phrase check below 0.001 s; output rail 1.279 s;
history store 0.593 s. Actual GitHub tool return duration was 1.259 s, contained
within agent/tools. Runtime setup dominates this particular first-read sample;
these few observations do not establish a performance improvement or regression.

`Server-Timing` records the response-start duration; the matching backend log's
later total was 28.791 s. Post-response persistence/cleanup contributes to the
later total, so do not treat these different measurement boundaries as identical
or sum nested tool/agent durations. The three earlier requests retain their
persisted stage events; their original terminal timing lines were not captured.
Stored event persistence was polled after responses instead of replaying calls.

## Applied rehearsal policy repair

The user explicitly approved reusing existing supported policy **212**. In one
transaction, app 214 assignment **190** was changed from policy **210** to **212**.
Its ID, display name `Block creation of issues named 'test'`, enabled state and
creation timestamp were preserved. The update timestamp changed normally.

Definitions 210/212 and compiled artifacts were unchanged; no duplicate policy
was created. Policy 210 remains stored with no enabled assignments. App 214 now
loads policies **26, 192, 193, 203, 212**, including exact validated compiled text;
its selected default-model grants resolve. App 221 remained valid.

The actual repaired snapshot's matcher restricts create-title `test` and `TEST`,
but not create-title `testing`, `contest`, or `other`, nor update-title `test`
under this rule. Other effective policies can still restrict requests.
This was an explicitly authorized direct rehearsal repair, not a management API
operation: no artificial management identity or audit event was fabricated.
The local sanitized repair receipt records the before/after assignment.

## Remaining manual input and conditional tests

There are **three production verification groups**, plus narrow optional work
checks/decisions. This is not three remaining individual commands.

| Item | What the user needs to provide/do | Database access |
| --- | --- | --- |
| Optional final browser inspection | If not already covered in the presentation, open Traffic for the last request ID and confirm its stages/tool trace; open Audit Logs and confirm existing actions render. Literal browser duration needs a DevTools capture only if desired. Browser automation exposes no tabs and its native helper is unavailable; backend persistence was independently verified. Do not repeat the accepted browser suite. | Current Azure rehearsal through the running backend; unavailable from home unless access changes. |
| Optional app 214 end-to-end acceptance | If Test App Two is in release scope, privately enter its existing key in its Runtime Test. With fresh conversations, an issue-create request titled exactly `test` should input-block; a nonmatching title should not be blocked by this exact-title rule. Keep MCP read-only, so no actual issue is created. A later refusal from read-only mode or another policy is separate. The agent could automate this with its existing key supplied privately; do not regenerate it just for testing. | Azure rehearsal. Local fixtures already cover the matcher/repair. |
| Release-scope decisions: apps 208 and 222 | Decide whether finance bot (208) is intended to run: both selected default-model grants are unavailable, possibly intentional. App `adsf` (222) actively selects profile 21/Qwen for both roles; classifier quality is not accepted by the earlier local matrices. Decide its intended classifier/release scope before treating it as accepted. No grants/selections were changed automatically. | Azure rehearsal to inspect/change these actual apps. |
| Target schema/configuration compatibility | Identify the intended production target, owner and approved configuration privately. Compare schema, exact policies/artifacts, selected grants, credentials and endpoint approvals; rehearse required changes on an authorized restored copy. Validate both model roles/auth against that configuration. Do not bypass rehearsal-only migration restrictions. | Intended target and controlled restored copy; later rollout work. |
| Production backup/key recovery/rollback | Back up the saved work key privately now. For production acceptance, identify backup/key custodians and recovery access, restore an appropriate backup with its matching key, and verify applicable encrypted-profile decryption plus the reviewed rollback procedure. Synthetic recovery already passed. | Authorized recovery environment with target backup. |
| Deployed image-pair acceptance | After authorized publication/deployment, provide exact image identities and deployed URL/access. Verify public frontend 80/private backend 8000, proxy, health/login/auth rejection, safe read, applicable block and logs on the actual release pair. | Deployed target through its backend. |
| New provider/gateway, only if added | Supply provisioned approved endpoint/model credentials privately; test actual main tool calls and/or classifier decisions, invalid decisions, authoring if used, and timeout/errors for the intended role. No mandatory new provider project is introduced. | Provider access; app-specific runtime acceptance needs its configured database. |

No new passwords, PATs, keys or database URLs need to be pasted into chat.
Test app 3's Qwen approval decision is complete. Selective branch merging remains
unavailable and fails closed; there is no pending test that should make it merge.

## Cleanup and current running backend

The user-authorized temporary private access file was removed after testing:
`.waylog/post-presentation-20261022/private-access.env`. Root `.env`, its work
encryption key and the user's data were preserved. Sanitized result/repair logs
remain in that Git-ignored folder; do not commit the folder or raw backend logs.
Only normal test conversation/Traffic rows and the approved assignment repair
were written to the rehearsal database.

After the approved package update, the agent restarted the backend hidden on
`127.0.0.1:8000`, PID **31988**, using the verified rehearsal URL and
`GITHUB_MCP_READ_ONLY=1`. Frontend remained running. Output goes to
`.waylog/post-presentation-20261022/backend-after-update.log`; this server is
not attached to the user's former terminal. Health and database health pass.
To take terminal control back, verify that PID still belongs to this backend,
stop that process, and restart `scripts/run_api.py` from the verified rehearsal
PowerShell environment. Do not start a second server on the same port.

## Exact automated catalogues

The commands below classify existing suites; they are not instructions to run
all live/manual diagnostic scripts against the shared rehearsal database.
`python scripts/run_security_checks.py` executes the 38 offline diagnostics
with external sockets and inherited credentials excluded. The opt-in
`python scripts/run_postgres_checks.py --run --backend-image <verified-image>`
creates and cleans its own isolated Docker PostgreSQL resources. It is not a
production migration command. Both catalogues have accepted passing evidence.

### 38 offline diagnostics

```text
test_app_main_models
test_model_gateway
test_branch_routing
test_security_controls
test_management_password_change
test_management_audit_http
test_app_authorization_http
test_app_llm_grant_migration
test_app_llm_grants_http
test_connector_credential_security
test_llm_endpoint_security
test_output_classifier_fail_closed
test_policy_fail_closed
test_prompt_rule_literals
test_resource_conditions
test_github_resource_bindings
test_resource_condition_inventory
test_input_condition_storage
test_runtime_policy_snapshot
test_github_tool_contract
test_runtime_policy_integration
test_policy_assistant_http
test_policy_options_capabilities
test_tool_guard
test_output_guard
test_runtime_cache
test_runtime_llm_grants
test_runtime_connector_credentials
test_runtime_mcp_launch
test_runtime_llm_selection
test_runtime_tool_status
test_policy_210_rehearsal
test_postgres_check_runner
test_runtime_block_explanations
test_runtime_debug_privacy
test_runtime_events
test_runtime_logs_http
test_request_timing
```

### 16 isolated PostgreSQL diagnostics (accepted home/CI evidence)

```text
test_policy_loader
test_app_policy_scope
test_app_auth
test_app_auth_http
test_policy_assignment_api
test_policy_auto_compile
test_policy_metadata_api
test_guardrails_run_http
test_runtime_connector_access
test_app_connector_api
test_policy_resolution_api
test_policy_deduplication
test_management_auth_http
test_management_rbac_http
test_management_users_http
test_llm_config_api
```
