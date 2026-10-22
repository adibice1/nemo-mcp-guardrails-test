# Final deployment checklist - 22 October 2026

Status: **home verification complete; production readiness remains open**.
There are **five remaining verification groups**, with several checks in each.
Some are conditional on the apps/providers being deployed; the final group runs
after an authorized deployment. Publication, migration and deployment are rollout
actions, not additional passing tests.

## Accepted baseline

- Source commit `5f84cffed834eb8c3d2bbd258e1b5b5e2f445a43` is user-pushed.
- [Hosted Verification](https://github.com/adibice1/nemo-mcp-guardrails-test/actions/runs/39710898869)
  passes both jobs: backend build, 38 offline checks, 16 PostgreSQL diagnostics,
  schema checks, frontend lint, TypeScript and production build.
- The new local backend image passes all 38 checks and matches the current source.
- Real frontend-proxy Azure/native-MCP plain/read/blocked status checks pass.
- Synthetic database backup/restore and missing/wrong/correct-key checks pass.
- Developer model registration, selection/use, model switching and the earlier
  browser/RBAC/policy workflows are accepted. Do not repeat that whole checklist.

See [the complete home results and image ID](home-readiness-results-2026-10-22.md).
Those results cover the tested local/CI environments. Actual Azure deployment
and production backup/key-custody checks still need their own evidence.

## Five remaining verification groups

| # | Group | Target and completion evidence |
| --- | --- | --- |
| 1 | **Work/Azure environment smoke and logs** | On the actual work rehearsal, verify proxy/API/database health, login, one safe branch read and one applicable blocked request with fresh conversation IDs. Confirm actual tool events and matching Traffic/Audit evidence. For the outstanding timing record, keep models fixed and record one cold plus two warm safe reads with browser/Server-Timing details. |
| 2 | **Affected policy and grant validation** | Before enabling affected apps, review/repair policy 210 on app 214 while preserving its ID, intent and assignments; verify loading, current compiled artifact and matching/nonmatching behavior. Review app 221's unused Qwen classifier grant and verify the intended state if changed. The synthetic repair test is already green; the actual database repair has not run. |
| 3 | **Target schema/configuration compatibility** | Inventory the intended deployment database and rehearse only its required migrations on a controlled restored copy. Verify security-foundation fields/indexes, model-grant schema, owned-model schema, existing policies/compiled versions, explicit selected-model grants and approved endpoint/credential references. Validate management authentication and both model roles against that target configuration. Preserve migration helpers' target restrictions; do not bypass them to run rehearsal-only helpers in production. |
| 4 | **Production backup, key recovery and rollback** | Verify the intended backup storage/process and separately protected encryption-key custody. In an authorized recovery environment, restore an appropriate target backup, supply its matching key privately, verify applicable owned-model decryption/state and rehearse the reviewed rollback procedure. Synthetic recovery is complete; actual key availability, restore access and deployment rollback still need verification. |
| 5 | **Deployed image-pair acceptance** | After authorized publication/deployment, record the exact frontend/backend image identities; verify frontend public 80, backend private 8000, same-origin `/api/gms`, database health, valid login, invalid app credentials rejected, one safe real tool read, one applicable blocked request and corresponding logs. Confirm enabled apps can resolve their selected models/connectors. Use the normal read-only GitHub setting. |

Group 2's policy 210 repair is relevant to app 214, not to the previously captured
app 221 effective policy set. It must be resolved before treating app 214 as
working. Do not disable/delete/recreate the legacy definition as a shortcut.
Its current assignments and intended exact-title meaning require review at work;
the earlier inventory capture itself is complete.

Group 3 is an exact target-difference review. It is not an instruction to apply
every historical migration, restore over production, provision automatic grants
or create a new schema design. The home encryption key has already been configured;
do not regenerate it. Production needs its own controlled provisioning/recovery
plan consistent with any encrypted data being restored.

## Rollout decisions and actions outside the test count

1. **Resolve or explicitly record the release disposition of known findings.**
   The recorded Pillow/FastEmbed compatibility finding and development-only
   braces finding remain open. Passing tests does not remediate them. Review
   [the dependency evidence](python-dependency-review-2026-10-22.md) and the
   [security rollout requirements](security-run-2026-10-16.md) with the release
   owner; this checklist does not grant security clearance.
2. **Prepare the actual runtime configuration and recovery ownership.**
   External persistent PostgreSQL, JWT secret, app-owned-model encryption key,
   provider/GitHub credentials, endpoint/reference approvals and selected-model
   grants must be available in the intended environment. The production secrets
   manager choice/ownership is still deferred. Inject actual values privately;
   do not place them in docs, images, client-side variables or Git.
3. **Publish and deploy the reviewed release pair.**
   Agree the source revision, immutable image identities, exact migration plan,
   deployment owner and rollback plan; publish to the agreed registry and execute
   the authorized rollout. Home images and green CI are not registry publication.
   CI exists and passes; automated CD is a separate future choice, not a missing
   requirement to rerun CI or implement another pipeline for this presentation.

The current ACI contract and variables are in
[containerisation.md](containerisation.md). Preserve its single-process backend
assumption; scaling to multiple workers/replicas needs the separate shared-limit
design already recorded in the security review. The public-port contract alone
does not establish an additional TLS/domain/ingress setup.

## Conditional provider acceptance

If deployment introduces a new provider or external gateway, add its role-specific
live acceptance before enabling it: actual tool-call/results for main agents,
input/output and invalid classifier decisions, structured authoring when used,
and timeout/error behavior. This needs the provisioned endpoint and credentials.
Existing Azure/Ollama results do not certify an unprovisioned provider. It is not
an extra mandatory provider project when deploying only the already tested models.

## Presentation checkpoint

For the presentation, do one short walkthrough on the actual presentation setup:
sign in, use the intended existing app/model, show a safe read, show the relevant
block and its logs. Include model registration/output blocking only if showing
those features. This rehearses the sequence; the completed feature suite stays
accepted. Record cold/warm numbers before making performance comparisons.

App 214 needs its real policy repair if it is part of that demonstration. A
presentation using the verified app/setup does not require production publication,
production cutover or a new gateway. Keep those milestones distinct.

## Work-machine entry point

Transfer the updated docs through the normal Git workflow before leaving home;
the readiness/checklist documentation added after commit 5f84cffe is currently
local until committed/pushed. At work, read this file and
[the handoff](work-computer-handoff.md), confirm the selected database/model/app
identity without sharing secrets, and begin with group 1. Do not rerun completed
PR creation, restore a rehearsal over production, or change read-only mode merely
to reproduce an earlier acceptance result.
