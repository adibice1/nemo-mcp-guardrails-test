# Deployment checklist - 22 October 2026

Testing resumed after the presentation. Read the
[post-presentation results and complete test map](post-presentation-verification-2026-10-22.md)
first. Work timing/tool events, audit persistence, the approved app 214 repair,
Test app 3's grant decision and work dependency alignment are now complete.
Earlier five-group lists are superseded by the three production groups below,
plus the narrow work decisions/optional checks explicitly listed here.

Status: **home and supplied-access work verification complete; production
readiness remains open**. Passing tests do not constitute security clearance.

## Accepted baseline

- Application source `5f84cffed834eb8c3d2bbd258e1b5b5e2f445a43` passed
  [Hosted Verification](https://github.com/adibice1/nemo-mcp-guardrails-test/actions/runs/39710898869):
  clean backend build, 38 offline checks, 16 PostgreSQL diagnostics, schema
  checks, frontend lint, TypeScript and production build. Current HEAD `6a8b355`
  adds presentation documentation; application source is unchanged.
- Home Linux image, real Azure/native-MCP proxy plain/read/blocked behavior and
  synthetic PostgreSQL backup/restore/key-recovery checks are accepted. See
  [the home image/results](home-readiness-results-2026-10-22.md).
- Developer main-model registration/use, model switching, classifier access
  controls, English edit/cancel, branch input routing, controlled PR creation/
  closure and browser request-count/filter/pagination checks remain accepted.
- Work schema, saved encryption key format, login, direct/proxy API/database
  health and valid/invalid app-auth boundaries pass on `nemo_restore_check_20261016`.
- Four real safe reads have actual persisted `list_branches` start/return events;
  a plain answer has zero tool starts and Tool guard `not run`. Existing blocked
  requests have input-block evidence and zero tool starts. Management audit
  actions are persisted. HTTP timings and one complete matching backend stage
  record are captured; literal browser timings were not captured.
- User-approved app 214 assignment 190 now reuses existing policy 212. The
  assignment label/enabled state and definitions/artifacts are preserved; exact
  snapshot validation and six matcher cases pass. Test app 3's unused Qwen
  classifier grant is retained by explicit user choice; selections unchanged.
- Work venv now matches all 120 constraints after installing the three approved
  pins; `pip check`, all 38 offline checks and a subsequent real read pass.
- The temporary private access file was removed. Backend is restored running
  against the rehearsal with GitHub read-only; see the results for process/logs.

## Narrow work follow-up

These are not a request to rerun the whole accepted feature suite.

| Item | Remaining action |
| --- | --- |
| Browser rendering, optional if presentation covered it | Inspect the recorded last request in Traffic and an existing Audit action if not already seen during the presentation. Backend events/persistence are verified. A browser DevTools capture is only needed for a literal browser-duration benchmark; automated proxy HTTP measurements already exist. Browser automation is unavailable. |
| App 214 full HTTP acceptance, if in release scope | Supply its existing key privately or run the two exact-title/nonmatching input cases in its Runtime Test, read-only. Snapshot/artifact/matcher validation is complete; app 221's key cannot authenticate app 214. Do not regenerate keys or create an issue for this check. |
| App 208 release intent | Finance bot lacks usable grants for both selected default models. Decide whether this is intentional or approve its intended models before treating it as runnable. No grants were silently enabled. |
| App 222 classifier intent | App `adsf` actively selects Qwen profile 21 as classifier. Earlier Qwen classifier matrices did not pass acceptance. Decide its intended release scope/classifier; Test app 3's retained approval does not certify this selected classifier. No selection was changed automatically. |
| Work key custody | Back up the saved work-rehearsal key privately. Synthetic validation is complete; provisioning alone is not backup/recovery acceptance. No stored owned models currently exist in this rehearsal. |

The Azure-specific follow-ups need a connected work backend. The home laptop
can use accepted synthetic/local PostgreSQL tests and inspect docs/source, but
cannot complete actual work/production checks without access to those targets.

## Three production verification groups

| # | Group | Target and completion evidence |
| --- | --- | --- |
| 1 | **Target schema/configuration compatibility** | Identify the intended production database and release scope. Inventory its differences and rehearse only required migrations on a controlled restored copy. Verify security fields/indexes, model grants, owned-model schema, exact policy/compiled content, selected-model approvals and approved endpoint/credential references. Validate management authentication and both model roles against the target configuration. Preserve helpers' target restrictions; do not bypass rehearsal-only guards. |
| 2 | **Production backup, key recovery and rollback** | Verify actual backup storage/process and separately protected matching encryption-key custody. In an authorized recovery environment, restore an appropriate target backup, verify applicable owned-model decryption/relationships and rehearse the reviewed rollback procedure. Synthetic recovery has passed; actual custodians, target restore access and deployment rollback still require evidence. |
| 3 | **Deployed image-pair acceptance** | After authorized publication/deployment, record exact frontend/backend image identities. Verify public frontend 80, private backend 8000, same-origin `/api/gms`, health, login, invalid app credentials rejected, one safe real tool read, one applicable block and corresponding logs. Confirm enabled in-scope apps resolve their selected models/connectors, with normal read-only GitHub mode. |

This is an exact target-difference review, not an instruction to run every old
migration, restore over production, provision blanket grants or regenerate
existing keys. Production needs controlled provisioning/recovery consistent
with any encrypted data being restored.

## Release decisions and actions

1. Resolve or explicitly record the release disposition of the known
   Pillow/FastEmbed compatibility and development-only braces findings. Review
   [the dependency evidence](python-dependency-review-2026-10-22.md) and
   [security rollout requirements](security-run-2026-10-16.md) with the release owner.
2. Agree runtime configuration and recovery ownership: external PostgreSQL,
   JWT secret, model encryption key, provider/GitHub credentials, endpoint
   approvals and selected-model grants. The production secrets-manager choice
   remains deferred. Supply actual values privately, never in docs/images/Git.
3. Agree source revision, immutable image pair, exact migration plan, deployment
   owner and rollback plan; publish and perform the authorized rollout. Green
   CI/local images are not registry publication. Automated CD is a separate
   future choice, not a missing test to implement now.

Preserve [the ACI contract](containerisation.md): frontend 80, backend private
8000 and the existing same-origin proxy. Backend scaling beyond one process
requires the separately recorded shared-limit design. The port contract alone
does not establish TLS/domain/ingress configuration.

## Conditional provider acceptance

If adding a new provider/gateway, verify its provisioned approved endpoint and
credentials, actual tool calls/results for main agents, input/output and invalid
classifier decisions, authoring if used, and timeout/error behavior for its
intended role. Existing Azure/Ollama evidence does not certify a new provider.
No new provider project is required when deploying already accepted models.
Selective branch merging remains unavailable and fails closed.

## Handoff

Use [the current results](post-presentation-verification-2026-10-22.md) and
[work/home handoff](work-computer-handoff.md), or the
[concise home continuation guide](home-handoff-2026-10-22.md). Transfer these updated docs through
the normal Git workflow before continuing elsewhere; no commit/push was made
by this testing session. The [presentation runbook](live-demo-2026-10-22.txt)
remains available as a historical/demo aid, not the current pending-test list.
