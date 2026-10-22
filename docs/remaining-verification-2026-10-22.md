# Remaining verification - 22 October 2026

## Final deployment view

[The work/deployment checklist](deployment-checklist-2026-10-22.md) is the concise
current deployment view: five remaining verification groups, plus separate
release decisions/actions and conditional new-provider acceptance. It expands
the production-readiness group below into target compatibility, recovery and
deployed acceptance. These are the same outstanding areas, not five additional
home test groups. It also lists the short final presentation walkthrough.

## Latest home follow-up completed

The [requested home readiness follow-up](home-readiness-results-2026-10-22.md)
is complete: new backend image with 38 checks, real frontend-proxy no-tool/read/
blocked statuses, synthetic database/key recovery, and the first hosted CI run
all pass. Both hosted jobs pass for the user's pushed commit 5f84cffe. These
additional checks do not complete the actual work-network or production-specific
groups below. No original home acceptance needs replaying.

## Automation follow-up applied

[The approved automation patch](automated-verification-preview-2026-10-22.md)
is applied with all candidate hashes verified. It adds three offline catalogue
checks (38 total), a repeatable disposable PostgreSQL runner and a published CI
workflow. The no-tool status issue is fixed in saved source. The synthetic policy 210
rehearsal does not complete group 6 against the actual work database. The later
hosted run is now successful, as linked above. The previously
completed home groups below retain their accepted status.

## Completion update

All four home groups below are now completed. The final image passed 35 offline
checks; 16 PostgreSQL diagnostics, migration/idempotency/constraints and the
real image-pair guarded read passed. The block-explanation diagnostic is fixed
and green. See [the final results](home-verification-results-2026-10-22.md).
Four work-network/conditional/release groups remain deferred. Open findings
listed separately are not additional unperformed home tests. The numbered home
steps below are retained as the completed verification record.

This is a reconciled checklist for the current home/handover milestone, not a
list of every historical test or future feature in the backlog. Count verification
groups rather than individual commands: four completed current-home groups and four
additional work-network/conditional/release groups. Some groups require a source
fix first. Most current checks can be agent-run when Docker access is available;
these are not 34 new manual user tests.

## Completed home verification: four groups

1. **Clean pinned backend environment/image.** Install from current requirements
   and constraints in a fresh Linux AMD64 backend build. Confirm exact package
   versions, dependency consistency and runtime imports (including cryptography
   50.0.0), run the 34-check offline catalogue in that clean environment and scan
   the resulting dependency set. Keep the documented Pillow finding visible.
2. **PostgreSQL schema/integration.** Use a disposable/restored rehearsal database
   to verify the app-owned model migration, then rerun it to prove idempotency.
   Check real PostgreSQL behavior for the new owner/key constraints and run the
   relevant database integration diagnostics against the current clean build. The
   user already applied the migration once and created/used a profile at home; do
   not label those completed steps pending or rerun against production.
3. **Current frontend image and matching image-pair smoke check.** Build the
   frontend image from the final UI source, connect it to the new backend and
   rehearsal database, verify frontend port 80/non-root behavior, backend health
   and database connectivity, same-origin proxy, management/app authentication
   and one read-only GitHub request using the registered model and selected
   classifier. This read is justified by the changed backend dependencies and
   image execution path; do not repeat the entire earlier browser test bundle.
4. **Previously failing block-explanation diagnostic.** Review intended behavior
   and prepare an exact source diff before any correction, then rerun
   tests/test_guardrails_run_http.py and affected checks against PostgreSQL.
   Enforcement passed before the recorded reason/name assertion mismatch; this
   entire diagnostic is still not green. Do not weaken an assertion merely to pass.

## Additional deferred verification: four groups

5. **Work-network Azure timing/log evidence.** With fixed model selections,
   capture one cold and two warm reads with browser and Server-Timing stage
   details against the actual Azure rehearsal. Verify matching Traffic/Audit
   evidence there. Completed home request-count/filter/pagination checks remain
   accepted; missing historical timing details alone do not require replaying them.
6. **Work rehearsal policy/grant follow-up.** After an approved policy 210 repair
   preserving intent and assignments, verify app 214 policy loading, compilation
   and relevant allowed/blocked behavior. Review whether app 221 should retain
   its unused Qwen classifier grant; verify the resulting intended state if changed.
   Existing inventory capture is complete and must not be repeated unnecessarily.
7. **External provider/gateway acceptance, conditional on provisioning.** For each
   actually selected new provider/model role, verify real tool-call/result handling,
   input/output and invalid classifier decisions, structured authoring when used,
   timeout/error behavior and latency/accuracy as applicable. This requires a
   provisioned endpoint and credentials; existing Azure/Ollama results do not
   verify an unprovisioned gateway or every provider in the setup guide.
8. **Production readiness and post-deployment verification, deferred.** Review
   backup/restore and encryption-key recovery, approved schema/policy rollout,
   matching published image identity and ACI port/private-backend behavior. After
   an authorized deployment, verify health, authentication and a safe guarded
   read. Image publication, migration and deployment are actions requiring their
   own authorized rollout scope; none has occurred in this continuation.

## Already completed

- All 34 offline checks passed on applied feature source and with the three
  updated dependency versions in the documented home preview runs.
- TypeScript, ESLint and the current production frontend build passed.
- Home proxy health, authenticated real branch read, policy-options request reuse,
  selected-policy GET, Traffic/Audit filtering and pagination were user-confirmed.
- Developer model registration, selection and live expected-name read were
  user-confirmed. Fresh conversation IDs fixed the observed retry behavior; the
  original raw tool result was unavailable, so history remains a leading rather
  than independently proven root cause.
- Azure/Qwen switching, English edit/cancel and the controlled PR/input cases
  were previously completed; the PR is closed/unmerged and read-only restored.

## Open work is separate from the test count

Pillow/FastEmbed compatibility remediation and the development-only braces
advisory remain open. The legacy explanation fix is complete. Policy 210 repair remains a
prerequisite for group 6. The misleading Tool guard passed badge when no tool
is called is fixed by the approved follow-up linked above. The unused Qwen classifier grant needs an
intent decision. Selective branch merging remains unsupported and fails closed;
implementing it is future feature work, not a request to execute an allowed merge.
The initial wrong branch answer is not independently root-caused; general model
quality is not established by a single successful read.

Sources: [current backlog](open-work-backlog.md),
[dependency review](python-dependency-review-2026-10-22.md),
[developer model review](developer-main-model-registration-review.md),
[home evidence](home-handoff-2026-10-21.md),
[work acceptance](work-acceptance-2026-10-21.md), and
[container contract](containerisation.md).
