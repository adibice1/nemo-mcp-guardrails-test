# Work Computer Security And Optimization Test Handoff — 22 October 2026

This resumes the online-database testing checkpoint from 16 October, alongside
the later model-switch work. The home machine could not reach Azure PostgreSQL
on port 5432, so home offline and separate local-database tests do not close
the remaining Azure rehearsal checks.

Use this checklist first, then the [model-test checklist](work-computer-model-test-checklist.md).
The dated sections deeper in the backlog/handoff are history, not instructions
to reimplement already-completed patches.

## Verified Checkpoint Versus Outstanding Evidence

| Area | Already recorded | Resume at work |
| --- | --- | --- |
| Security/optimization source | Patches 010–018 implemented; patch 019 and English branch UI applied | Verify the current combined source, not the old patch sequence |
| Automated verification | Earlier Windows/Linux, image and disposable PostgreSQL checks passed; applied provider integration later passed 33 offline checks | Repeat on the work checkout with its pinned dependencies; earlier images predate later source |
| Azure rehearsal schema | Security password-state fields/index and model-grant table applied to nemo_restore_check_20261016 | Confirm target/schema; do not apply again automatically |
| Azure branch conversion | Policies 181, 182, 192, 193 and 209 converted; enabled with one enabled/current artifact each | Inspect preserved definitions/scopes and English UI; do not replay the old manifest |
| Azure baseline | Login and real read-only GitHub search succeeded | Re-establish after transfer, retaining the actual work app identity |
| Invalid app credentials | Offline coverage exists | Manual hosted-database rejection result still outstanding |
| Branch routing | Earlier screenshots showed an input block and a read-only refusal | Controlled PR-creation/tool evidence still outstanding |
| Optimization | Lazy builder loading and per-app runtime caching implemented | Browser request and cold/warm Azure measurements still outstanding |
| Home model switching | Ollama main agent and GitHub reads demonstrated; local classifiers failed acceptance | Reproduce at work after the security baseline; keep Azure classifier |
| Next.js 13 | Isolated compatibility draft saved, not applied | Wait for supervisor decision, then refresh/review the exact diff if needed |
| Production | No cutover, production migration or image publication recorded in this work | Separate reviewed release activity |

Primary records: [security completion report](security-run-2026-10-16.md),
[019 behavior/limitations](branch-routing-patch-019.md), and
[the previous rehearsal checkpoint](open-work-backlog.md#resume-from-home---rehearsal-checkpoint-2026-10-16).

## 1. Transfer, Establish The Version, And Run Safe Checks

Use steps 1–3 of the [model checklist](work-computer-model-test-checklist.md)
for transfer, dependency setup and the verified Azure rehearsal connection.
Bring uncommitted result/handoff documents too. Do not copy the home .env
wholesale or assume its app 33 and local policy IDs exist at work.

From the work repository root:

~~~powershell
git status --short
git log -1 --oneline
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -B scripts/run_security_checks.py
node scripts/check_branch_editor.cjs
~~~

Expect 33 offline checks and the branch-editor check to pass. After installing
the current lockfile under the chosen runtime, verify the frontend:

~~~powershell
Set-Location frontend
npm.cmd run lint
npm.cmd exec -- tsc --noEmit --incremental false
npm.cmd run build
~~~

The current applied source is Next 16 / React 19; Node 24 is the image baseline.
Home installed packages were older and 19 Python packages differed from pins,
so a passing home pip check did not verify the clean security dependency baseline.
Do not adopt old installed packages as the intended source configuration.

## 2. Restore The Verified Azure Rehearsal Session

Use the credential-prompt and read-only verification commands in
[the existing connection instructions](work-computer-handoff.md#reconnect-the-home-backend-to-the-rehearsal-copy).
Run the backend later in that SAME terminal.

Target: guardrails-postgresql.postgres.database.azure.com:5432 /
nemo_restore_check_20261016. The production database nemo_mcp_guardrails is not
the test target. Home localhost:5433 databases are separate.

In DBeaver, these read-only queries provide an additional check:

~~~sql
SELECT current_database();

SELECT column_name
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'users'
  AND column_name IN ('must_change_password', 'temporary_password_expires_at');

SELECT indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename = 'conversation_messages'
  AND indexname = 'ix_conversation_messages_scope_tail';

SELECT app_id, purpose, llm_config_id, enabled
FROM app_llm_grants
ORDER BY app_id, purpose, llm_config_id;
~~~

Expected database: nemo_restore_check_20261016; both password columns and the
tail index should exist. Compare actual enabled grants with the chosen work
app's two purposes. The earlier successful Test App runtime supports working
access, but the grant-manifest apply output was not supplied as a complete audit.

If anything differs, diagnose before continuing. A health/db SELECT 1 result
does not validate schema. Do not rerun schema helpers or grant seeding blindly.
Keep terminal DATABASE_URL set to the verified rehearsal; do not clear it using
the home-local restart instructions.

## 3. Finish The Pending Browser And App-Authentication Checks

Start backend/frontend using steps 5–6 of the [model checklist](work-computer-model-test-checklist.md).
Begin with approved Azure main and guardrail profiles so the provider change
does not complicate the existing security checks.

- Sign in again and confirm normal navigation to Apps, Policies, Traffic and Audit Logs.
- Inspect global policy 209. Its summary should say source is not development AND target is staging.
- Open its structured branch editor, inspect the comparisons, make a temporary unsaved change, then cancel. Reopen and confirm the original definition/scopes remain.
- Inspect the other converted policies without rewriting them: 181 has the same route as 209; 182 restricts target main; 192/193 restrict source not staging AND target production.
- Confirm the merge limitation notice remains visible.
- In Runtime Test, use a deliberately wrong app API key with the actual client app ID. Expect HTTP 401 before model/tool work; inspect the browser Network response and runtime events where available.
- Restore the existing valid key and confirm a read succeeds. Do not regenerate the app key to perform this check.
- Use a fresh conversation ID for each independent case and keep GITHUB_MCP_READ_ONLY=1 for this phase.

For broader security acceptance, record role-based access with existing test
admin/developer identities and verify Traffic/Audit access restrictions. If
checking the temporary-password lifecycle, use a dedicated rehearsal account;
do not reset a colleague's account or deliberately exhaust login limits.
Expiry/rate-limit boundaries already have isolated automated coverage.

## 4. Review The Remaining Legacy Definitions And Actual Grants

Only after verifying the configured rehearsal target, in its terminal:

~~~powershell
.\.venv\Scripts\python.exe -B scripts/inventory_resource_conditions.py --database
.\.venv\Scripts\python.exe -B scripts/migrate_app_llm_grants.py
~~~

The first command performs a read-only condition inventory. The second, without
apply flags or a manifest, prints the grant-table plan and selection inventory;
it does not apply grants. Its candidate enabled flags are approval defaults,
not a substitute for reading the actual grant rows shown in step 2.

Identify enabled unsupported conditions, scope/assignment conflicts and stale
compiled artifacts. Review each against its intended meaning. The five converted
branch definitions must retain their IDs, enabled flags and assignments. The home
policy repairs apply only to the home rehearsal copy.

Do not run a full compile/resync while enabled unsupported definitions remain.
Do not disable/recreate mandatory definitions, replay an old conversion manifest,
or copy home policy IDs into the work database as a workaround. Any required
repair should have a fresh target-specific preview before application.

## 5. Resume The Controlled PR-Creation Tests

This is the outstanding write-capable manual test from the work checkpoint,
not the read-only Ollama feasibility test. It creates a pull request BETWEEN
branches; the route comparison does not mean creating a Git branch.

Prepare a dedicated repository the user owns, an appropriately scoped existing
test credential, and existing development, staging and feature/test branches.
The allowed creation case also needs actual differing commits so GitHub can
create a PR. Confirm the app's effective policies before testing; other global
or app restrictions can legitimately block a nonmatching route.

Keep this phase separate from normal reads. Only when deliberately resuming
that controlled test, stop the backend and restart in the verified rehearsal
terminal:

~~~powershell
$env:GITHUB_MCP_READ_ONLY = '0'
.\.venv\Scripts\python.exe -B scripts/run_api.py
~~~

For the confirmed global 209 condition:

| PR route | Expected evidence |
| --- | --- |
| feature/test → staging | Policy 209 matches; block before PR creation |
| development → staging | Policy 209 does not match; if all other rules permit, actual PR creation and repository verification |

Use fresh conversation IDs and the owned repository in each prompt. Record input
decision, tool-guard decision, policy identity where available, actual tool
invocation and repository result. An input block does not independently exercise
the execution-level tool guard; a read-only/model refusal is not a completed
write test. If the intended tool is not attempted, record that gap rather than
claiming execution enforcement passed.

The rehearsal database does not sandbox GitHub. Do not use octocat/Hello-World
for writes, broaden token permissions automatically, push commits or merge PRs
as part of these cases. Handle any created test PR through the repository
owner's agreed cleanup process.

After this phase, stop the backend and restore read-only mode:

~~~powershell
$env:GITHUB_MCP_READ_ONLY = '1'
.\.venv\Scripts\python.exe -B scripts/run_api.py
~~~

Selective branch merging remains unavailable and fails closed, including a
nonmatching conditional route. Do not expect an allowed merge or bypass this
limitation. Keep exact branch conditions checked in NeMo AND the tool guard.

## 6. Measure The Implemented Optimizations

Do these with a fixed Azure main/classifier selection first; record the source
revision and configuration so model latency is not confused with cache behavior.

| Check | Procedure | What to record |
| --- | --- | --- |
| Policies initial loading | Open browser Network, filter API requests, reload Policies | Initial list/scope calls; full builder options should load only when needed |
| Lazy Create/Edit data | Open Create, cancel, reopen; open Edit for one definition | Builder-options reuse in the current page session; selected-definition fetch rather than a whole catalogue fetch |
| Cold versus warm runtime | Restart backend in read-only mode, run a safe branch read, then repeat twice for the same app with fresh conversation IDs | Server-Timing runtime_setup plus rail/tool/total durations; cold first call versus warm calls |
| Cache invalidation | Use the approved Azure/Ollama main-profile switch comparison | Next request uses the saved profile without backend restart; record selections and timing |
| Logs and history | Open Traffic request details and Audit Logs against the rehearsal backend | Correct app/outcome/stage, pagination/filters and absence of credentials/suppressed output in shared evidence |

Use multiple samples before describing a speed improvement. Backend restart
makes a cold process; a fresh conversation ID alone does not clear the app runtime
cache. Warm requests still check database state; they do not bypass authorization
or policy/grant checks. Do not tune TTL/capacity until baseline measurements exist.

The older before/after claim of four versus two initial page calls was a
historical implementation measurement. Current auth/scope requests may add calls;
inspect actual request purposes rather than enforcing an obsolete total count.

PostgreSQL retention cutoff/rollback/batching tests remain a separate disposable
fixture task. Do not run cleanup --apply on the Azure rehearsal or production
database simply to exercise logging. Management-audit retention and multi-replica
coordination are longer-term work, not implemented by these checks.

## 7. Next.js 13 — Wait For The Supervisor Decision

Current state: the compatibility draft is saved under ignored .waylog as
next13-compatibility.patch plus next13-compatibility-manifest.json. It is NOT
applied. Git does not transfer ignored review artifacts; retain them privately
if needed as reference material.

If the supervisor keeps the current version, continue with the current source.
If the supervisor confirms Next.js 13:

1. Re-read the saved draft and compare it with the latest source. Its manifest
   targets older commit c44f55d61c71ebb5803b8be0c232afeee575466e, before subsequent
   provider integration and handoff changes. Do not apply it blindly.
2. Refresh the exact review diff for package/lockfile, React/types/lint,
   proxy route params/dynamic behavior and related checks/docs. Preserve the
   body cap, credential forwarding, redirect handling, Node 24, non-root port 80,
   private backend 8000 and all backend security/policy/grant protections.
3. Check current support/advisory status and obtain the supervisor's production
   security disposition. The 20 October draft used Next 13.5.11/React 18.2.0;
   its recorded production audit contained a critical Next finding. That is a
   dated result, not a fresh audit or a claim every advisory is exploitable here.
4. Preview the refreshed exact diff and obtain approval before changing non-doc
   source, then apply the agreed patch.
5. Repeat clean npm ci, TypeScript, full lint, branch-editor checks, production
   build, authentication/core screens, proxy checks and Node 24 Linux image smoke.
   The isolated draft passed home Node 22 checks, not the final current-source
   Node 24 image acceptance.

This changes the frontend framework portion of patch 010. It does not undo the
remaining security/optimization work and requires no database migration merely
because the frontend version changes. Do not run an automatic audit fix that
silently overrides the supervisor's agreed version.

## 8. Finish Model Reproduction, Then Plan Release Separately

After the baseline security checks, follow the [Ollama work checklist](work-computer-model-test-checklist.md)
for main-agent switching. Azure remains the classifier; further local-classifier
experiments and the Llama download are on hold.

When ready for release, rebuild and test the matching CURRENT frontend/backend
Linux AMD64 images using [containerisation.md](containerisation.md). Preserve
frontend public port 80, backend private 8000 and the same-origin proxy.
The isolated frontend container checker uses a fake upstream with no external
network. The separate backend checker seeds only an explicitly empty disposable
reviewdb/review database; never point it at the Azure rehearsal.

Image publication, production schema/grant/policy rollout and Azure deployment
are separate reviewed steps. Earlier local image results do not certify a later
source revision or a possible Next.js 13 patch. Fresh backup/recovery review is
still required before production data changes.

## End-Of-Day Evidence

For each case, record: source revision, dependency baseline, verified database,
app/profile identities, expected and actual result, conversation/request ID,
block/tool stage, policy identity where available, elapsed time and any unresolved
gap. Never paste keys, passwords, credential-bearing URLs, private reasoning or
sensitive traffic content into the handoff.

Tomorrow's priority is the missing online rehearsal evidence in steps 2–6.
The Next.js decision can remain pending while those backend/security checks
continue. Mark results as passed, failed, blocked or not run; do not carry home
local-database outcomes forward as if they tested Azure.
