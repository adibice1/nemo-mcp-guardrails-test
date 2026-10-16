# Work/Home Computer Handoff

## Patch 019 Source And Rehearsal - 2026-10-16

Read [019 behavior and conversion](branch-routing-patch-019.md) before continuing.
Branch creation routing is implemented with configurable equality/inequality and
AND. Selective branch merges remain unavailable: matching metadata blocks, while
other conditional merges refuse safely. Do not execute the earlier proposed
disable SQL. The five branch definitions can be previewed/converted on the
restored database without deleting policies or changing assignments.

The user confirmed the work .env targets local 127.0.0.1:5432 while DBeaver targets
Azure PostgreSQL 18.6. The rehearsal uses a temporary PowerShell DATABASE_URL
override for nemo_restore_check_20261016. Never assume that override exists in a
new terminal or print its credential-bearing value. No Azure mutation was made
by the implementation agent. Existing unsupported non-branch policies and model
grant approvals remain independent rollout steps.

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
