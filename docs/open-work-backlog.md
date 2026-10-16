# Open Work Backlog

This file tracks unfinished implementation work so active plans do not get lost
across machines or Codex sessions.

## Current Completion Status - 2026-10-16

Patches 010-018 are implemented under the user's autonomous authorization. Passed
cross-platform, image and disposable PostgreSQL checks are recorded in the
[completion report](security-run-2026-10-16.md). No additional implementation
subpatches are planned. Do not rerun historical "next patch" instructions below.
Remaining work includes selective branch-merge execution beyond the conservative
019 source implementation below, schema/grant/policy rollout and real-service/browser verification,
plus the documented unpatched development-tool dependency and lint compatibility
follow-up. No release image was published or production data changed.

## 019 Presentation Follow-up - Completed 2026-10-16

The user approved the exact five-file preview in chat. One shared frontend
formatter now presents branch conditions in plain English in policy summaries,
branch-editor previews and AI draft previews. The structured branch editor hides
the symbolic textarea for branch rules. Backend comparisons, case-sensitive names,
assignments and enforcement are unchanged; no database rewrite ran. The
selective-merge limitation notice is retained. The existing branch-editor check
(including English formatting, fallback and incomplete-input checks), whole-project
TypeScript and full lint all passed. No new backend or deployment slice was added.

## 019: Admin-Configured Branch Routing - Required Next Slice

Source implemented under "ok apply everything" authorization. Creation routing,
UI/AI authoring, canonical storage/reuse, conversion tooling and safe merge
refusals are implemented and tested. See [019 results](branch-routing-patch-019.md).
Selective merge execution remains incomplete because the pinned connector cannot
atomically enforce the branch decision. Do not mark that capability complete or
resume deployment based only on offline tests. No Azure data was changed.

During the Azure restore rehearsal the user confirmed that administrators must
be able to configure source/target branch restrictions through the management
system without editing backend code for each policy. The user then clarified
that retiring these policies is not the intended resolution. The earlier
suggestion to disable policies 181, 182, 192, 193 and 209 is withdrawn; do not
execute that SQL. Preserve definitions and assignments. No database change is
performed or implied by this documentation update. Global policy 209 remains a
runtime setup blocker under the current implementation.

The completed review patches deliberately support one literal equality. They do
not satisfy this compound-branch requirement. Implement it as one cohesive new
feature slice, rather than another historical 009 subpatch or a manual cleanup:

- Provide structured source/target predicates with conjunction and equality /
  inequality, with arbitrary configured branch names rather than hard-coded
  development/staging/production special cases. Do not guess branch aliases.
- Let administrators author, preview, save and edit these rules in the policy
  builder. AI drafting must produce the same validated structure. Do not require
  administrators to edit backend Python or raw JSON for ordinary policies.
- Bind PR-creation predicates to authoritative head/base arguments. For merging,
  establish trusted PR metadata and concurrency protections; missing or changed
  state must not silently permit a prohibited operation.
- Keep storage validation, equivalence/reuse, compiled prompts, immutable policy
  snapshots/cache invalidation, tool enforcement and generated tests aligned.
- Preserve and explicitly review the existing legacy definitions during
  conversion. Cover permitted/prohibited routes, source-owner qualification,
  branch case, unavailable metadata, alternate tool routes and changed PR state.

Required examples include source != staging AND target = production for PR
creation and merge, and source != development AND target = staging for PR
creation. Actual branch names and retained assignment scopes must be reviewed.
Deployment readiness remains incomplete until the required policy semantics are
implemented and validated; recreating the same free text cannot provide them.

Track this as one follow-up to completed patch 009. Extend its existing compiler,
validation and execution modules instead of introducing a parallel branch-policy
engine. Prefer versioned structured data in existing conditions JSON, with one
normalized predicate representation shared by validation, compilation, reuse and
execution. Preserve existing single-field policies. No new table or schema
migration is approved or assumed by this plan.

Start by verifying the pinned MCP revision's read/merge schemas and the remote
merge API's concurrency guarantees. A head-SHA precondition alone must not be
claimed to protect target-branch changes. Resolve this enforcement boundary
before promising merge support or showing it as executable in the UI. Primary
reference: [GitHub pull-request API](https://docs.github.com/en/rest/pulls/pulls).

Completion requires all of the following in the same feature delivery:

1. An administrator can create, preview, save, edit and reuse the required branch
   policies through the UI; AI drafts use the same validated representation.
2. PR creation checks actual source/target arguments. Merge checks use trusted
   remote metadata and verified concurrency protections, with controlled refusal
   when the decision cannot be established.
3. Generated prompt rules, tool decisions, policy attribution and exact-content
   cache invalidation agree, retaining mandatory global/app assignment scope.
4. Tests cover all source/target match combinations, branch case and qualified
   heads, metadata/lookup errors, concurrent state changes, alternate write routes,
   existing equality policies, API reuse/edit isolation and frontend round trips.
5. Conversion of the existing branch definitions is explicitly previewed and
   rehearsed on the restored database, preserving definitions and assignments.
   No automatic production data rewrite or broad disable is part of the patch.

Prefix matching, arbitrary Boolean expressions, ordered workflows and read-action
restrictions are separate capabilities; do not fold them into this slice. The
other incompatible legacy definitions remain rollout work after branch support.

## Security Review Patch Sequence

Updated 2026-10-16. The user authorized autonomous implementation of patches
010-018, including non-doc edits without per-diff approval. This supersedes the
earlier preview/wait workflow for this run. Existing changes must be preserved;
live migrations, publishing and deployment remain separate.

Updated 2026-10-15. This is the ordered remaining security/cleanup work from the
project review. Follow this sequence for the current patch series; the older
feature and deployment plans below remain context, not competing next steps.
Patches 001-008 are applied to source; see the
[patch history](security-patch-history.md). All three 008 slices are applied
and offline checks passed, including runtime grant enforcement and selector
adaptation. PostgreSQL/browser verification and reviewed grant rollout remain
open. Patch 009a's literal-condition grammar is approved and applied; its offline
checks passed. 009b's bindings/inventory are approved and applied; saved-source
checks passed. 009c1's storage/API validation is approved and applied unchanged;
saved-source offline checks passed.
009c2a's single-statement snapshot reader is approved and applied unchanged;
saved-source offline checks passed. 009c2b's seven-file contract/compiler/launcher
diff is approved and applied unchanged; saved-source offline checks passed.
009c2c's fourteen-file runtime/cache integration diff is approved and applied
unchanged; all nineteen saved-source offline diagnostics passed. Assistant/UI alignment remains
009c3 below. Its 009c3a five-file backend diff is approved and applied unchanged;
all seven saved-source offline diagnostics passed. 009c3b's final four-file
frontend diff is approved and applied unchanged; saved-source checks passed.
Patch 009 source implementation/offline verification is complete. Its live
compatibility, browser and reviewed legacy repair/resync remain rollout checks.
The later 2026-10-16 authorization and completion table supersede this historical
sequence's earlier approval checkpoints.

Keep scope and status here as work progresses. If evidence changes the order or
scope, explain the change in chat and update this list before proceeding. Show
every complete proposed non-documentation diff in chat and wait for approval
when that review workflow is in effect; the autonomous 010-018 run was explicitly
exempted by the user. Do not store code previews or code diffs in `docs/`; docs
contain plans, summaries, outcomes, checks, and operational instructions only.
Listing a patch here does not authorize its code changes or a deployment.

| Order | Patch | Status | Completion check |
| --- | --- | --- | --- |
| 004 | Block output when Azure refuses classification | Applied; offline checks passed | Unclassified output cannot reach responses, stored assistant turns, or response logs |
| 005 | Fail closed on database policy-loading errors | Applied; offline checks passed | Failed policy reads stop runtime construction instead of dropping rules or using defaults |
| 006 | Restrict app authorization changes to system admins | Applied; offline checks passed | Linked developers cannot reauthorize an app disabled by an admin |
| 007 | Restrict connector credential-reference provisioning | Applied; offline checks passed | Developers cannot select arbitrary server environment secrets for connector use |
| 008 | Scope model and credential choices to approved apps | 008a/008b/008c applied; offline checks passed; rollout checks open | App A cannot use App B's model/credential configuration without an explicit grant |
| 009 | Define enforceable custom-resource conditions | All 009 slices applied; source/offline verification complete; rollout checks open | Unsupported conditions cannot silently become ineffective tool restrictions |
| 010 | Refresh the frontend framework and related packages | Implemented: Next 16.4.2/React 19.3.1; production audit clear; dev upstream follow-up open | Reviewed target versions pass type, build, proxy, and authentication checks |
| 011 | Refresh the frontend Node image/runtime | Implemented: digest-pinned Node 24.21.0; non-root port-80 smoke passed | All image stages use a reviewed supported runtime and retain the port-80/non-root contract |
| 012 | Add management authentication throttling | Implemented: bounded per-peer/actor throttling; single-process deployment contract | Repeated login attempts are bounded without permanent account lockout or credential disclosure |
| 013 | Complete temporary-password lifecycle | Implemented: expiring setup-only sessions and atomic replacement; explicit schema rollout required | Temporary passwords expire and require replacement before normal management access |
| 014 | Bound runtime requests and conversation reads | Implemented: byte/schema/history bounds, indexed tail, execution timeout | Oversized requests are rejected early and history reads have predictable bounds |
| 015 | Make legacy access backfills explicit and safe | Implemented: explicit-target preview and opt-in membership helper | Running a helper cannot silently grant every user access to every app |
| 016 | Review and trim unused dependency/provider packages | Implemented: direct/constraint split, eight unused extras removed, published advisory fixes; clean install verified | Removed packages are proven unnecessary and a clean install still supports the runtime |
| 017 | Remove generated files and proven dead code | Implemented: generated/dead files removed; standalone diagnostics retained | Generated artifacts stay untracked and retained diagnostics remain runnable |
| 018 | Establish a safe regression entry point and close the review | Implemented: 31-check safe runner; final container results in completion report | Offline checks run explicitly; DB/live-service tests require deliberate opt-in |

### 004: Fail-Closed Output Classification

Completed: `guarded_execution.py` now blocks unclassified responses after Azure
rejects an output self-check. The secret-pattern fallback is removed, Azure
category metadata is retained, and wrapped/raw Azure and LangChain filtered-
completion error forms are recognized. Normal rail results and propagation of
unrelated errors are preserved. The older fallback-pass assertion is updated.

The regression reproduced the bypass, then passed against saved source: 12 HTTP
cases exercise response serialization, disposable SQLite conversation history,
and log values at the persistence boundary, plus normal/error controls.
Earlier privacy, literal-rendering, and LLM endpoint regressions also passed.
Harmless responses may also block when classification cannot complete. No
migration or new setting is required. No service was restarted or deployed.

### 005: Database Policy-Loading Failures

Completed: database policy and compiled-rule read failures raise a controlled
policy-loading error rather than substitute defaults or empty rules. Runtime
setup maps that failure to a generic HTTP 503 before model/MCP construction.
Legitimate empty assignment sets remain distinct from failed queries. Malformed
selected rows stop setup instead of being skipped. Explicit offline default
fixtures remain available without becoming a production fallback.

Verified input, output, and compiled-rule read failures, legitimate empty results,
global/app scope, recovery, and cached-runtime refresh behavior with isolated
fixtures; no real database was interrupted.

The approved patch reads/compiles policies before constructing models or MCP
tools. It eliminates the tool-guard import-time
database read; its compatibility constant describes static diagnostic defaults,
while wrappers load current rules unless explicit rules/tool sets are supplied.
Database-backed empty results stay empty in both scoped and unscoped loaders.

Explicit default mode generates static prompt rules for offline diagnostics,
but authenticated runtime construction rejects that mode, including on cache
hits. Failed revision checks and failed refreshes cannot return an older cached
runtime for that request; recovery can build a fresh bundle. No schema migration
is required. Existing malformed policy rows must be repaired instead of skipped.

The regression reproduced the old fallback before application, then passed
against saved source. It covers disposable SQLite scope queries,
loader failures, malformed/empty rows, offline defaults, import behavior,
construction ordering, cache failure/recovery, and generic HTTP errors. Seven
existing offline diagnostics also passed against saved source. Python AST and
diff checks passed. No service was restarted or deployed. Its full code diff
was previewed in chat only.
This patch does not add transaction-wide policy snapshots or prove every enabled
policy has a matching active compiled row; compilation consistency remains a
separate concern. The generic 503 mapping covers runtime setup; authentication,
history loading, and startup database checks retain their existing error handling.

### 006: Administrator-Controlled App Authorization

Completed: only system administrators can submit `authorized` in app updates.
Ordinary linked-app edits remain available. Existing frontend controls already
hide authorization and show Client ID as read-only, so no UI change was needed.
The isolated diagnostic verifies developer rejection, administrator disable/enable,
mixed-request atomicity, and runtime authentication after revocation and rename.

The approved patch rejects any developer update containing `authorized`, including
unchanged values and null, before validating model references or assigning any
fields. Existing app membership and guardrail-model restrictions remain active.
Only `PUT /apps/{app_id}` updates app metadata; the client-ID alias provides
read access but no general metadata PUT route. No new alias endpoint was added.

The frontend already hides authorization controls and shows Client ID as read-only;
no UI change is needed. Existing API-only developer name/client-ID edits are
preserved. Renaming a disabled app does not restore runtime authentication.

Before application, the regression reproduced developer reauthorization against
the old code; it now passes against the approved saved-source patch.
It covers real management JWT/RBAC, 24 protected-field requests, unchanged stored
fields after mixed-request rejection, administrator disable/enable without app
membership, and real runtime authentication before/after revocation and rename.
Disabled runtime requests are rejected before the mocked runtime builder runs.
Existing password-change, management-audit, and policy-loading diagnostics also
passed against saved source. Python AST and diff checks passed. Full code
previews stay in chat only. No migration, service restart, or deployment ran.
This patch does not cancel
requests that authenticated before revocation or change API-key rotation rules.

### 007: Connector Credential References

Completed: connector provisioning uses administrator permissions and executable
GitHub references must match backend-approved environment names. Both app-ID and
client-ID routes enforce the boundary across create/upsert/update, omitted
fields, and existing records. Unapproved references fail before model/MCP startup
without revealing secret values. GitHub read-only defaults remain unchanged.

The approved patch requires system administrators to provision new connector links and
submit credential-reference fields, including null/blank/unchanged values.
Linked developers retain existing-link enable/disable and unlink operations.
Credential-free POST upserts preserve the stored reference for both roles.
New links require an admin even when the reference is omitted, so a developer
cannot unlink and recreate a connector to acquire the shared default PAT.
Both app-ID/client-ID routes and connector name/ID updates enforce the same rules.
Frontend provisioning controls are admin-only; existing management controls
remain available to linked developers.

For GitHub, the default PAT variable is approved automatically. Extra exact
environment names require backend setting
`GMS_ALLOWED_GITHUB_CREDENTIAL_ENV_VARS`. Syntax, scheme, and backend approval are
checked before reading a referenced value. Admin API writes reject invalid or
unapproved GitHub references with 400. Runtime construction also validates
existing records; unapproved/missing credentials produce a generic 503 before
model/MCP startup. A malformed backend list fails closed. Other connector types
remain metadata-only; this does not add runtime support or credential resolvers.

The old resolver's ability to read a JWT secret as a GitHub PAT was reproduced
using fake values only. After application, the saved-source regression passed:
60 protected-field cases plus new-link/upsert, omitted-field preservation,
delete/relink, scope, legacy-record, and runtime failure checks. Credential and
launch diagnostics, app authorization, policy loading, LLM endpoint security,
and management audit also passed against saved source. Frontend TypeScript,
scoped ESLint, Python AST, and diff checks passed. The live-Postgres connector API
diagnostic was updated but not run. Full code previews stay in chat only.

Patch 007 is applied to source. No migration is required. Existing custom
GitHub references require backend name approval and a restart after deployment;
no real `.env` edit, service restart, or deployment was performed here. Backend
operators remain trusted to approve appropriate GitHub credential variables.
Already-allowlisted legacy references retain execution access; this patch does
not establish their historical administrator approval or app-specific ownership.
Review existing links during rollout. Changes to backend environment approval
require restart because constructed MCP clients are cached.

### 008: App-Specific Model/Credential Grants

Status: **design and slices 008a/008b/008c approved and applied on 2026-10-15**.
Management and runtime grant checks are implemented in source. PostgreSQL/browser
verification and reviewed migration/backfill/deployment remain open; no rollout
was performed.
The complete `target-architecture.md` was read before preparing this proposal.
Preview every implementation diff in chat and obtain approval before applying
non-documentation changes. This section is the
single plan for 008; implementation slices below do not add competing patches.

#### Evidence And Boundary

Patch 003 restricts endpoint destinations and config creation, but
`GET /llm-configs` returns the shared readable catalogue to every management
user. `api/apps.py` checks only that selected configuration IDs exist.
`load_runtime_llm_selection()` loads them without an app grant check. Null
selections use the shared Azure environment settings without app approval.

An isolated current-source reproduction used real JWT authentication and
disposable SQLite: an App A developer with no App B membership listed and
selected the configuration assigned to App B. The runtime selection loader
then returned that configuration's fake credential reference. Clearing App A's
selection also chose the environment default without a grant. A fake JWT secret
was used for authentication; no real secret, model/connector credential lookup,
live database, model client, MCP process, or external service was used.

The proposed boundary covers app-selected main and guardrail models for
authenticated runtime requests. A configuration grant includes its endpoint,
deployment and credential reference as one administrator-provisioned bundle.
It does not let developers supply or substitute a credential. GitHub connector
provisioning remains governed by patch 007's existing per-app links and backend
approval; no second connector credential catalogue is proposed here.

#### Proposed Grant Storage

Add one table, `app_llm_grants`, leaving existing app selection columns intact:

| Field | Proposed meaning |
| --- | --- |
| `id` | Primary key |
| `app_id` | Required app foreign key; deleting the app deletes its grants |
| `purpose` | Required constrained value: `main` or `guardrail` |
| `llm_config_id` | Named configuration foreign key; null explicitly means the Azure environment default |
| `enabled` | Required boolean; default false |
| `created_at`, `updated_at` | Management metadata |

Use separate unique indexes for named configuration grants and null/default
grants so an app/purpose cannot have duplicate grants for the same subject.
Deleting a configuration removes its grants. A grant for one purpose does not
authorize the other purpose. Missing or disabled grants deny use, including when
the app's selection is null. No wildcard, all-app, or implicit default grants.
Constraint and null-uniqueness behavior must be checked on disposable PostgreSQL
as well as SQLite before deployment; SQLite alone is insufficient evidence.

Configurations remain create-only through the management API in this patch.
Their credential references stay server-side. Add an exact backend environment
name allowlist, `GMS_ALLOWED_LLM_CREDENTIAL_ENV_VARS`, with
`AZURE_OPENAI_API_KEY` automatically approved. Validate references before lookup,
including legacy rows; malformed approval configuration fails closed. Backend
operators remain trusted to approve appropriate LLM secret names. Approving a
name globally does not grant any app a model. Existing endpoint approval and
redirect refusal remain required independently.

A named configuration that omits endpoint or credential reference continues
using the corresponding backend default; granting that configuration explicitly
approves that bundled fallback. It does not grant the separate null selection.
Changing backend defaults or secret approvals requires a backend restart and
operator review of affected grants. Direct privileged database edits remain a
trusted administration path; this table does not protect against a database
administrator rewriting configurations. A future configuration-edit API must
define whether changed endpoints/credentials require renewed grants.

#### Proposed Management Behavior

- System admins create, enable, disable or delete grants. Linked developers
  cannot grant themselves models, including through app-role admin/owner links.
  System admins can administer grants without app membership, but selections
  and runtime use still require an explicit enabled grant. Selecting a model
  does not silently create or reactivate a grant.
- Expose grant management and purpose-specific readable options beneath both
  `/apps/{app_id}` and `/apps/by-client-id/{client_id}`. Proposed routes are
  `GET /llm-grants`, `PUT /llm-grants/{purpose}/{config_ref}` and
  `DELETE /llm-grants/{purpose}/{config_ref}` under either app prefix.
  `config_ref` is a numeric configuration ID or the literal `default`;
  PUT accepts an explicit enabled flag. Keys are immutable; replacing a subject
  means managing its separate grant. Reads require existing app-route access.
- Add `GET /llm-options?purpose=main|guardrail` under either app prefix. Return
  only that app/purpose's enabled grants for enabled configurations and an
  explicit `environment_default_allowed` flag, without credential references.
  Disabled configurations or grants cannot be newly selected. Grant listings
  may show disabled entries for administration, without secret references.
- Restrict the global `GET /llm-configs` catalogue to system admins. Developers
  use the app-scoped options; guessing another configuration ID does not bypass
  selection checks. Preserve current main-selection access for linked developers
  and guardrail-selection access for system admins only.
- Validate every explicitly supplied selection, including null and unchanged
  values, before any app mutation. An unavailable or ungranted selection gets a
  generic 403, without revealing whether an inaccessible configuration exists.
  Omitted selections remain untouched. Metadata-only edits remain possible
  while stored selections need repair after grant revocation.
- New apps start without model grants. The current frontend already creates
  apps with null selections. Reject non-null initial selections with a clear
  400 instructing admins to create the app, grant models and then select them;
  the app/grants/selection workflow must not silently authorize catalogue use.
  App creation with null selections does not authorize environment-default use.
- Grant removal does not silently clear or replace the app's selection. An admin
  can grant an approved replacement, then select it. Implement DELETE as
  revocation that retains a disabled row, so an old bootstrap manifest cannot
  recreate a removed grant. Physical removal is reserved for app/configuration
  cascades or trusted database administration. Update management audit
  classification for grant writes and test accepted/rejected actions without
  logging request bodies or credential references.
- Adapt the existing, currently unmounted `AppLlmSettings` component and API
  client to purpose-specific options. Represent an unavailable stored selection
  visibly; do not let the select control silently choose another value. Disable
  unapproved environment-default choices. Do not mount the component or redesign
  the app screen as part of this security patch. Initial grant administration
  uses the authenticated management API/Swagger rather than a new UI.

#### Runtime And Cache Revocation

Check both selected purposes against live grants before secret resolution or
model/MCP construction. Validate configuration availability and credential-name
approval as well. Invalid legacy selections or unavailable grants yield a
controlled generic runtime 503; never fall back to another model or default.
Keep `/v1/guardrails/auth-check` as an identity-only endpoint.

Run the grant check for every runtime request, including warm cache hits and
cache-disabled operation. Do not rely solely on count/latest-timestamp cache
fingerprints for revocation. Include the exact selected grant identity and
state in the app's runtime revision, and recheck after waiting for a build lock
and before returning a newly built bundle. A grant-read failure denies runtime
use rather than returning the cached bundle. The implementation must use one
shared validation helper so management writes, cold builds and warm requests
cannot drift in their interpretation of defaults or model purposes.

Requests already admitted may finish if a grant is revoked concurrently; this
patch does not cancel in-flight provider calls. Changes committed before a new
request's grant check must take effect on that request, without waiting for TTL
expiry. Backend environment/secret changes continue requiring restart.

The policy-authoring assistant is separately management-authenticated and uses
the backend default deployment without an app context. It does not consume
app grants; an authoring-model approval policy is outside this runtime grant
design. Local diagnostic model builders also do not establish app authorization;
tests must exercise the authenticated runtime boundary.

#### Migration, Backfill And Rollback

1. Prepare an explicit additive migration helper that previews its schema and
   current selection inventory by default. Creating the grant table requires
   an apply option. Never read secret values or change app selections while
   inventorying them. Avoid unrelated full-schema creation/backfills.
2. Produce an administrator-reviewable manifest with app identity, purpose,
   configuration ID or default, and enabled decision. Inventory includes both
   purposes of every app, including null/default and disabled selections. An
   inventory entry is a candidate, not proof of historical administrator consent.
3. Seed only explicitly reviewed manifest entries using a separate apply action.
   Reject unknown/duplicate entries or changed selection/configuration metadata
   instead of guessing. Apply each manifest atomically and idempotently; no
   all-app grants, implicit defaults, or automatic re-enabling of revoked grants
   on a rerun. Re-enabling requires an explicit admin grant operation. Unreviewed
   selections stay ungranted.
4. For rollout, pause incoming runtime requests, apply schema and reviewed grants,
   approve any required custom LLM credential environment names, deploy/restart
   the enforcing backend, verify each app and then resume traffic. Mixed older
   backends would bypass grants. The existing startup `create_all` may create a
   missing additive table but must never seed grants. Missing/empty grants must
   deny use, with a deployment diagnostic rather than an unrestricted fallback.
5. Existing selections remain stored for review and recovery. Apps lacking a
   grant for either purpose intentionally lose runtime availability until an
   administrator approves or replaces their selection. Do not automatically
   turn off `apps.authorized` or change app API keys.
6. Leave the additive table in place on rollback. Rolling back to pre-008 backend
   code restores unrestricted model selection and is not a security-preserving
   rollback: keep runtime traffic stopped if that rollback is necessary. Prefer
   fixing grants/configuration or rolling forward. Do not drop grants or rewrite
   selections as an automatic rollback step.

No migration, manifest application, real `.env` edit, service restart, or
deployment is authorized by this design review. PostgreSQL verification will
need explicitly disposable infrastructure, separate from the live database.

#### Implementation Slices And Completion Checks

After design approval, show each complete non-documentation diff in chat for
approval before applying it. Apply 008 incrementally:

1. **008a: applied.** Add the constrained grant model and dry-run
   migration/manifest tooling with isolated schema/backfill tests. This slice
   alone is not enforcement.
2. **008b: applied; offline checks passed.** Add admin grant management,
   scoped catalogue/options, exact LLM credential name approval, app selection
   validation, grant audit classification and generic error handling.
3. **008c: applied; offline checks passed.** Add shared cold/warm runtime enforcement, revocation/cache
   handling, component/API-client adaptation and remaining regression coverage.

Slice 008a is approved and applied to source. Its exact three-file diff added
`AppLlmGrantRecord` to `database/models.py`, the standalone
`scripts/migrate_app_llm_grants.py`, and
`tests/test_app_llm_grant_migration.py`. The script previews DDL on stderr and
an unapproved JSON inventory on stdout by default. Schema creation uses
`--apply-schema`; reviewed JSON uses `--manifest` and previews changes until
`--apply-manifest` is also supplied. These are separate actions. No grants are
seeded by schema creation, and existing grants are never changed by the helper.
False manifest entries create no grants. A decision conflicting with an existing
grant is rejected and requires an explicit management operation through 008b.

The approved saved-source diagnostic passed. Disposable SQLite covered write-free previews, exact schema
scope, default-deny fields, purpose/named/default uniqueness, foreign keys and
cascades, strict manifest input, credential-lookup exclusion, stale metadata,
disabled configurations, full-manifest validation, rollback after an actual
insert, repeat-run idempotence, and disabled-grant preservation. Existing app
authorization and connector security diagnostics also passed against saved
source. PostgreSQL DDL compiled; PostgreSQL behavior remains unverified.
AST parsing, reverse-patch verification of the approved diff, and whitespace
checks passed. No real `.env`, live DB, model/MCP execution, live migration,
restart or deployment was used. Only disposable SQLite fixture schema/data was
changed during tests. Code previews remain in chat only.

008b's exact 13-file diff was approved in chat and applied to source. It adds
new shared credential-name and app-grant validation helpers, purpose-specific
options and grant GET/PUT/DELETE endpoints under both app-ID/client-ID prefixes,
admin-only access to the global model catalogue, and validation of every
explicit app selection before mutation. Null and unchanged selections need
grants too. Administrators must create an app, approve grants, then select named
models; app creation with null selections grants no model access. Unavailable
selections receive generic 403 responses; grant-store errors are mapped to 503.

Grant writes require a system administrator without relying on app membership.
DELETE retains a disabled row, and explicit admin PUT can re-enable it. Options
filter unsupported, disabled, unapproved-endpoint or unapproved-credential
configurations without returning credential references. Backend name approval
uses `GMS_ALLOWED_LLM_CREDENTIAL_ENV_VARS`; the default Azure key name is
automatically approved, while malformed approval settings fail closed.
API provisioning validates references without resolving credential values.
Runtime validation of legacy references was subsequently added by 008c below. Grant mutation audit
classification is included now so the new route family is covered from its first
implementation, rather than waiting for 008c.

The saved-source HTTP diagnostic passed with real JWT/RBAC and disposable
SQLite. It covers app/purpose isolation (including a developer linked to both
apps), both route forms, query-alias bypass attempts, explicit null/unchanged
choices, administrator grant requirements, default grants per purpose,
revocation-row preservation and bootstrap replay denial, invalid legacy grant
choices, atomic rejected edits, generic DB failures, credential-name approval,
and audit privacy. Five related offline diagnostics passed: LLM endpoint
security, 008a migration, management audit, app authorization and connector
credential security. AST parsing for all 12 changed/new Python files, approved-
diff reverse verification, and whitespace checks passed. Two existing live-
PostgreSQL diagnostic expectations/fixtures were updated but were not run.
No frontend files changed in 008b; the unmounted selector is adapted in 008c below. No real
`.env`, live DB, model/MCP execution, live migration, restart or deployment was
used. PostgreSQL constraints/concurrency remain unverified. 008b alone did not
enforce legacy runtime selections or warm caches; 008c adds those checks below.

All source slices are applied. Keep the PostgreSQL/browser and reviewed rollout
checks open; do not treat offline checks as production deployment verification.

008c's exact 12-file diff was approved in chat and applied to source. It adds
live validation of both selected purposes through 008b's shared grant helper
before secret resolution or model/MCP construction, including on every warm
cache hit and when caching is disabled. Missing, disabled, unapproved or unreadable
grants stop setup with a generic LLM-configuration 503. App authorization is
rechecked too. Existing named/default selections receive no implicit grants.

The cache comparison includes exact selected grant IDs and detached model
metadata. Construction uses that same validated snapshot; the loader runs again
after waiting for a build lock and after construction. Changed or revoked
selections prevent return/caching of the new bundle. Requests already admitted
may finish if revocation happens after their check; in-flight provider calls are
not cancelled. Environment/credential-value changes still require restart.

The patch replaces arbitrary LLM environment resolution with the approved-name
resolver and validates default approval before reading Azure settings. Missing
default settings or approved named keys produce controlled LLM errors. Endpoint
approval and redirect refusal remain intact. The unmounted selector switches to
separate per-app main/guardrail options, preserves unavailable saved choices,
marks unapproved defaults, and prevents saving unavailable choices. Creating a
configuration does not insert an ungranted option. The component remains
unmounted; mounting it or adding a grant-management UI is outside this slice.

The new saved-source diagnostic passed with real app-key/JWT authentication
and disposable SQLite. It covers app/purpose/default isolation, warm-cache
revocation, unchanged revision fingerprints, metadata changes, grant-store
failures, cache-disabled requests, lock-wait revocation, construction changes,
missing default credentials through the real coordinator, denied execution/
history writes, and approved credential lookups. Eight related offline
diagnostics passed: runtime cache, policy fail-closed loading, connector security,
LLM endpoint security, model selection, grant management, connector credential
resolution and MCP launch configuration. Existing isolated cache/policy/connector
fixtures now supply an explicit approved model snapshot so their original
boundaries remain independently tested.

Full frontend TypeScript and scoped ESLint passed against saved files. All ten
changed/new Python files parsed, reverse-patch verification matched the approved
diff, and whitespace checks passed. No real
`.env`, live DB, Azure/GitHub request, live migration, restart or deployment ran.
Browser verification and actual PostgreSQL constraints/locking/concurrency remain
unverified. Rollout still requires the
reviewed grant inventory/backfill and deployment sequence above. Full code
previews stay in chat, never in docs.

Required verification: App A/B isolation with real JWT/RBAC, a developer linked
to both apps, system admins without app membership, both app route forms, main
and guardrail grants independently, explicit null/unchanged/omitted selections,
disabled models, missing/revoked/default grants, no partial app mutations,
credential lookup spies, legacy database rows, warm-cache revocation and grant
query failures, build-lock changes, cache-disabled operation, audit privacy,
manifest staleness/rollback/idempotence, PostgreSQL constraints, and frontend
TypeScript/scoped lint. Use fake secrets and model/MCP boundaries. Do not add
another provider or secrets-manager integration in this patch.

### 009: Custom-Resource Enforcement Boundaries

Status: **all planned 009 source slices approved and applied unchanged on
2026-10-15; saved-source offline verification complete**. Patch 010 is next.
Real PostgreSQL/concurrency, binary/catalogue compatibility, model quality, browser
interaction/layout and reviewed legacy repair/resync remain explicit rollout
checks. No live database or deployed policy changed.

The pre-009 runtime reproduction showed that `tool_guard.py` matched an
issue-title restriction against an unrelated body value, missed the saved
assistant example for target production/source not staging, and treated paths
that differ in case as equal. It extracted candidates and compared flattened
argument values. 009c2c replaces that matcher below; arbitrary branch logic and
ordered workflows remain unsupported.
Reviewed repository examples include `test_tool_guard.py`, policy-resolution and
runtime HTTP fixtures, the assistant HTTP fixture, and the frontend's saved PR
creation/merge samples. Actual database policies have not been inventoried.

Scope and sequence:

1. **009a: strict grammar foundation, applied; offline checks passed.** Adds a
   pure parser and standalone offline diagnostic. Non-empty conditions represent one field and
   one literal equality. Text literals must be quoted in explicit field syntax;
   issue/PR numbers are positive decimal integers. Resource-specific fields are
   issue title/number; PR title/number/source branch/target branch; file path;
   branch name; repository name. This grammar does not assert that every field
   is observable for every action/tool. That capability gate belongs to 009b.
   Preserve literal case, punctuation and internal whitespace for subsequent
   field-specific matching. This slice has no management/runtime imports and
   does not fix or change the existing guard by itself.
2. **009b: compatibility inventory helper and executable bindings, applied;
   offline checks passed.** Adds a read-only inventory of saved input conditions
   and bindings reviewed against the pinned MCP source. Live database inventory
   remains outstanding. Bind only
   to authoritative target fields, including nested file paths where supported;
   unrelated title/body/owner/repository values cannot satisfy another field's
   restriction. Account for shared-tool action discriminators. Title/branch
   restrictions on operations exposing only an identifier need an explicit
   unsupported result unless a separately reviewed trusted lookup is added.
   Define missing/malformed target handling so execution cannot silently bypass
   a restriction. No implicit lookups or workflow state are part of this scope.
3. **009c: management, runtime and assistant integration, split below.** Validate
   before storage and equivalence canonicalization; reject unsupported new or
   edited input conditions with a readable client error. Validate loaded legacy
   policies too, failing runtime setup closed for enabled scoped policies that
   cannot be enforced. Do not silently disable, broaden, rewrite or delete them.
   Update prompt compilation, generated test prompts, AI draft validation and
   saved UI examples together so unsupported conditions are not offered as
   executable policies. Cover the actual HTTP save/load/execution path offline.
   Verify cross-tool routes and indirect side effects for broad restrictions
   too; a tool's declared name alone is insufficient. Resolve the local Docker
   launcher's unpinned image and verify the supported tool/version contract
   before enabling bindings in runtime.

009c implementation slices, in order:

- **009c1: versioned selector storage and management validation, applied;
  saved-source offline checks passed.** Reject unsupported input conditions before
  canonicalization/storage and introduce format version 1 in the existing JSONB
  conditions object. Preserve path/branch case, punctuation and Unicode; fold
  title/repository-name case only. Canonical field equality text retains quoting
  and obeys the 1,000-character bound. Reusable-definition lookup and manual
  deduplication must keep unreviewed legacy literals separate. Explicit condition
  submission can create/review a definition; metadata-only edits cannot silently
  promote an unversioned or noncanonical selector. Exact disable-only updates
  remain available without repairing the old condition. Adapt the read-only
  inventory to recognize valid canonical versioned rows. No schema migration,
  live backfill, existing-row rewrite or runtime change belongs to this slice.
- **009c2: runtime/cache enforcement and compiler artifacts, applied; offline checks passed.** Validate
  loaded selectors and their format, fail setup closed for unsupported selected
  policies, and compile immutable rules bound to authoritative MCP fields.
  Refuse missing/malformed arguments before execution, preserving generic errors
  and private-value-free events. Ensure the same scoped policy snapshot governs
  cold builds, warm cache reuse, lock waits and completed builds; aggregate
  revision metadata alone must not hide condition changes. Update NeMo rule
  text and generated blocked prompts to reflect actual supported selectors.
  Review stale compiled rows, mandatory globals, app isolation, direct/indirect
  tool routes and the supported MCP contract, including the unpinned local
  launcher. Read containerisation/handoff docs before changing launch images.
  Prove allowed/blocked HTTP requests and pre-execution failures with fake
  external boundaries. No live model/MCP or write-mode harness is implied.
- **009c3: assistant and management UI alignment plus source closure, applied; offline checks passed.** Validate
  primary and related AI drafts against the executable capability subset. Retire
  unsupported source/target compound samples as executable drafts and return an
  explicit unsupported/clarification outcome instead. Preserve user scope; never
  substitute a broader ban. Align field help, draft application, saved-policy
  display/edit round trips and illustrative prompts with the canonical format.
  Do not offer unsupported read-block definitions merely because read tools are
  present in connector metadata.
  Finish runtime/assistant/HTTP and scoped frontend regressions, record remaining
  deployment checks and require reviewed legacy-policy repair before rollout.

009c3 review order (2026-10-15): split backend capability validation from the
frontend changes so each exact diff remains reviewable. 009c3a is approved and
applied, as is 009c3b below. Every later non-doc patch requires its own complete
chat preview and approval.

1. **009c3a: backend assistant/options alignment, applied unchanged; saved-source checks passed.** Validate
   primary and related input drafts through the storage/runtime capability gate;
   canonicalize accepted selectors and return clarification with no drafts for
   unsupported conditions. Replace compound/negation drafting instructions with
   the supported field-equality contract. Filter policy options to enabled,
   supported write combinations and expose their conditional field names.
   Prove authenticated HTTP behavior, invalid-related handling, output isolation,
   option enable flags and read/unsupported exclusions using disposable SQLite
   and a fake provider. No live AI or database writes are implied.
2. **009c3b: frontend examples, field help and source closure, applied unchanged; saved-source checks passed.** Consume the
   backend field information, retire unsupported executable samples, display an
   explicit clarification instead of substituting a broader restriction, and
   preserve canonical selectors through draft application, create/edit and
   summary views. Check mock preview options as well as real API options. Run
   scoped frontend and backend round-trip regressions; document outstanding live
   PostgreSQL/catalogue/model-quality and legacy repair/resync checks before
   closing the source review. Patch 010 follows only after these slices.

009c3b is the final planned source slice of patch 009. Keep this change limited to
frontend API types, supported mock options, executable/unsupported examples and
resource-field guidance. Existing canonical selector payload/edit/summary paths
should be preserved rather than refactored. Verify them with focused checks and
reuse the existing backend regression coverage. Do not add another 009 slice for
optional UI polish or test infrastructure. After approval/application and checks,
move to 010; live PostgreSQL, binary/catalogue, model quality, browser and reviewed
legacy repair/resync remain explicit rollout checks in the deployment backlog.
Patches 010-018 keep their listed scopes and order; dependency removal and dead
file cleanup remain 016/017 rather than being absorbed into this UI patch.

009c3b's approved four-file frontend diff is applied unchanged: 60 insertions/61 deletions. It
replaces executable compound samples with supported PR-number/target-branch
samples and an explicit unsupported-condition example with no draft or substitute.
Independent samples no longer suggest each other as equivalent related scopes.
The modal uses backend `condition_fields` for equality help/placeholders, preserves
existing text, blocks unavailable combinations and nonempty conditions on
broad-only combinations, and keeps backend validation authoritative. Preview
options match all fourteen supported write combinations/fields; unsupported read
options are removed from authoring mocks. No payload/edit/summary refactor or new
test framework is proposed.

Saved-source TypeScript checks across the project and scoped Next core-web-vitals
ESLint passed. A focused harness executes extracted saved handlers and existing payload/
edit helpers: supported/unsupported/output samples, six exact selector submit/edit
round trips and unavailable/broad-only submission gates passed. Both sample
selectors passed the actual backend storage/execution contract and case/number
checks; all fourteen mock combinations/field lists match backend capability data.
Existing assistant HTTP, policy-options HTTP and input-storage HTTP diagnostics
passed with real JWT/disposable SQLite and fake provider boundaries. All four
saved frontend files match the approved drafts exactly; unchanged patch SHA256,
reverse-patch and whitespace checks passed. Browser inventory is empty; real browser interaction
and visual layout remain unverified. No real environment, live database/model/MCP,
server restart, package installation, migration, resync or deployment ran. Active
frontend code matches the approved diff; the complete preview remains in chat
only. This completes the planned 009 source work; 010 is next. Deployment/legacy compatibility checks remain explicitly open.

009c3a's approved five-file diff is applied unchanged: 240 insertions/18 deletions. It uses the same
condition preparation as storage to canonicalize primary/related input drafts;
unsupported conditions or changed related-policy scope return clarification and
no drafts. Unsupported tuple, mismatched rail and malformed schema failures
retain controlled errors. Input
instructions list executable selector fields and explicitly refuse compound,
negated, workflow and unobservable merge-branch restrictions. Output drafting
remains separate. Policy options require enabled, connector-consistent metadata
and the supported write gate; resources gain additive `condition_fields` lists
(an empty list means broad scope only). These fields describe the supported
selector subset, not every possible argument or remote state.

The revised assistant HTTP diagnostic, new policy-options HTTP diagnostic and
five existing offline diagnostics passed against saved source: input storage, runtime policy integration, GitHub execution contract,
resource bindings and grammar. Real JWT and disposable SQLite cover authentication,
primary/related validation, canonical case/Unicode/quotes, scope changes, output
isolation, all metadata enable flags and cross-connector mismatches. All five
saved Python files parsed and matched the approved drafts exactly. Approved-patch
reverse verification, unchanged patch SHA256 and whitespace checks passed. No real environment, live database/AI/MCP, migration, resync, restart
or deployment ran. Contract validation cannot prove that an AI draft faithfully
interprets natural-language intent; users must review before saving, and model
quality is unverified. Frontend examples/help and edit/display checks are now
completed in 009c3b above. The complete approved non-doc diff remains in chat only.

009c2 review order (2026-10-15): the earlier runtime loaded policies and compiled
rules separately and its aggregate revision could miss condition changes. The
following slices were applied in dependency order to avoid mixed policy state:

1. **009c2a: immutable scoped policy snapshot, applied unchanged;
   saved-source offline checks passed.** Adds a single-statement reader for the
   authorized app, enabled global/app input/output
   definitions, normalized connector metadata and active compiled rows. Reject
   legacy/noncanonical/unsupported selectors and missing, duplicate, stale or
   mismatched compiled artifacts. Snapshot values must be detached and immutable;
   no autoflush, writes, environment loading or implicit default fallback. Test
   scope, malformed rows, exact-content changes and legitimate empty scope with
   disposable SQLite. Do not connect this reader to runtime yet.
2. **009c2b: executable tool/compiler/MCP contract, applied unchanged;
   saved-source offline checks passed.** Implements field-
   specific matching, shared-method discrimination and broad cross-tool/indirect
   effect coverage; align prompt text and generated tests. Pin the local launcher
   to the reviewed image and validate the executable tool contract. Keep runtime
   integration dependent on the completed snapshot/contract checks.
3. **009c2c: runtime/cache integration and HTTP proof, applied unchanged;
   saved-source offline checks passed.** Use the same
   immutable snapshot for rails, input attribution, output rules and guarded
   tools. Re-read exact contents on cold/warm paths, after locks and after builds;
   fail closed instead of reusing stale parts. Cover scoped HTTP allow/block,
   malformed arguments, unavailable state, stale compiled rows and in-flight
   changes with fake model/MCP boundaries. Distinguish a matching restriction from
   a failed target evaluation instead of attributing an unknown target as a match.
   Retain existing model-grant checks.

These are subdivisions of 009c2, not additional feature work. 009c3 and patches
010-018 retain their order. No schema migration or live data action is implied.

009c2a's approved two-file diff is applied unchanged: 425 added lines for the
snapshot reader and its offline diagnostic.
The reader accepts a caller-supplied SQLAlchemy session; imports neither the
database connection module nor policy loaders and never consults environment
settings or default fixtures. One SELECT projects scalar/JSON columns instead
of ORM entities, avoiding lazy queries and stale identity-map values. Enabled
global/app assignments select enabled definitions once, even with dual assignment;
an authorized app with no selected policies has a legitimate empty snapshot.
Normalized input metadata must be enabled and internally consistent. Nonempty
input selectors must already be supported canonical version-1 values. Unsupported
broad combinations fail too. Each selected input/output definition must have one
enabled, nonstale artifact with exact rail, policy version and current compiler
text. Disabled historical artifacts are ignored; enabled stale history rejects.
Immutable values retain exact contents for later cache comparisons and omit
literal policy/rule text from their default representations.

Saved-source checks passed using in-memory SQLite: the new diagnostic, four
existing storage/inventory/binding/grammar diagnostics, both Python AST parses,
approved-patch reverse verification and workspace whitespace. The new test
forbids dotenv loading,
counts one SELECT with pending ORM changes, proves app/global scope and generic
failures, tests malformed/legacy metadata and compiled artifacts, and detects
content changes without version/timestamp changes. PostgreSQL SQL compiled only;
no actual PostgreSQL, HTTP runtime, cache wiring, concurrent database writer,
model/MCP execution, live inventory, migration, restart or deployment was tested.
At 009c2a the reader had no active runtime consumer. Its complete approved non-doc
preview remains in chat only. 009c2b and 009c2c are now applied below, including
runtime/cache integration. No live database or deployed policy was changed.

009c2b's approved seven-file diff is applied unchanged: 467 insertions and 15
deletions. It adds `github_tool_contract.py` and an offline diagnostic, updates
the compiler and input-condition capability gate, pins runtime and full-runner
Docker launch images to the Dockerfile's reviewed digest, and adapts the isolated
launch diagnostic. Broad input combinations must pass the same supported-write
gate as conditional ones. Read metadata stays available for connector discovery;
unsupported read-block definitions return a validation error instead of being
accepted as executable policies.

The immutable execution rules use authoritative field bindings and shared-method
discriminators. Reviewed extra routes include issue/PR updates through shared
endpoints, merges that change PR/issue state or file contents, file pushes/upserts
that initialize branches, repository initialization and forks that create files,
branches or repositories, and direct file commits. Broad restrictions deny
indivisible operations that may have the restricted effect. Conditional routes
match observable fields; missing/malformed targets and related writes whose
target cannot be observed raise an explicit evaluation error. They do not silently
return an allow result, invent remote state or replace the stored definition with
a broader ban. A conditional file policy can therefore refuse an otherwise valid
merge/fork because its affected paths are unavailable. No trusted remote lookup,
workflow state or external automation/webhook enforcement is introduced.

The catalogue helper admits reviewed names only, excludes extra tools such as
sub-issue/star/review-comment routes outside the current capability set, and
rejects duplicate names or drift in enforcement-relevant field/method/nested-file
schemas. It permits read-only catalogues. This validates compatibility, not binary
authenticity: provenance relies on the pinned Docker image or the bundled native
binary from that image. Native configuration now refuses alternate executable paths.

Conditional rail text names the actual field, literal and comparison semantics;
generated blocked prompts carry that literal instead of using unrelated broad
templates. The full runner retains hardcoded read-only mode. New conditional rail
text will differ from old persisted artifacts: before eventual rollout, explicitly
review/repair legacy conditions and resync compiled rules through the existing
admin path. No resync, rewrite or migration has been run here.

Saved-source checks passed: the new contract
diagnostic and twelve existing diagnostics covering launch settings, snapshots,
storage/JWT/RBAC, inventory, bindings, grammar, legacy wrappers, literal Jinja
rendering, policy failures, model grants/cache and connector credentials. The
standalone compiler CLI also completed offline and retains direct-file execution.
The earlier baseline reproduction confirmed broad branch rules omitted `push_files`
and conditional generated prompts omitted their target. No real `.env`, live database,
image pull, binary/container/MCP process, model call, migration, restart or
deployment ran. All seven saved Python files parsed and matched the approved
drafts exactly; approved-patch reverse verification and whitespace checks passed.
The full GitHub runner was parsed only, not executed.

At 009c2b the matcher/catalogue were not connected to active wrappers, snapshots
were not used for cache checks, and runtime did not validate persisted compiled
consistency. 009c2c now connects these below. Reporting-name changes alone do not
establish execution enforcement. Do not close 009 before 009c3 and rollout checks.
The complete approved code diff remains in chat only. 009c2c is applied below; each later
non-doc diff still needs complete preview and approval.

009c2c's approved fourteen-file diff is applied unchanged (559 insertions/156
deletions). It connects the validated single-statement snapshot to
authenticated runtime construction. Rails receive its compiled-rule tuple
explicitly (including an empty tuple), and input attribution, executable guard
rules and deterministic output phrases derive from the same immutable contents.
No separate policy/compiled-rule loader is used in that path. Exact snapshot
contents join model grants and the existing revision in cache comparisons. Fresh
reads occur before reuse, after build-lock waits and after construction, including
when caching is disabled. Invalid or changed state stops the request instead of
falling back to an older bundle. Existing model-grant checks remain in place.

The implementation replaces flattened scalar matching with the reviewed field/method
contract and filters MCP tools before wrapping them. The full read-only runner
uses the catalogue too. Standalone DB input loaders reject unversioned/noncanonical
conditions, and direct legacy conditional wrappers without an executable binding
are refused. An actual matched rule supplies its policy identity; indeterminate
targets return controlled `tool_error` results with a distinct evaluation source
and metadata-only event reason, without a false matched-policy identity. Existing
manual broad tool-name sets remain available for isolated diagnostics.

Saved-source checks passed: a new real-app-key HTTP diagnostic and eighteen
existing offline diagnostics (including the six runtime
event unit cases). The new test exercises the public builder, real snapshot,
rails-config injection, catalogue, wrappers, execution coordinator, API response
and conversation persistence with in-memory SQLite and fake external boundaries.
It covers global/app isolation, legitimate empty scope without reloads, exact
title/path matching, shared methods, correct tool attribution, output phrases,
warm-cache changes with constant aggregate revision, stale/legacy/global failures,
schema drift, cache-disabled operation, build-lock changes and in-flight policy
changes. Failed setup reaches neither agent execution nor history persistence;
guard denials never invoke the underlying tool. Older model/credential tests use
explicit empty snapshots so those independent boundaries remain isolated.
An installed LangGraph tool node inside a compiled graph also propagates both
guard error kinds without invoking the underlying connector.

All fourteen saved Python files parsed and matched the approved drafts exactly;
approved-patch reverse verification, unchanged patch SHA256 and whitespace checks
passed. The full GitHub runner was parsed only. No real `.env`, live database,
PostgreSQL concurrency, real binary/catalogue, model/MCP process, migration,
compiled-rule resync, restart or deployment was used. Tests simulate interleavings;
they do not establish actual concurrent PostgreSQL behavior or model quality.
Requests admitted before a concurrent policy change can still finish using their
validated snapshot. Before rollout, review/repair legacy input conditions and
resync changed compiled text through the existing admin path. Patch 009 remains
unfinished until 009c3 aligns assistant/UI authoring and closure checks. The
complete approved non-doc diff remains in chat only. 009c3a is now applied above;
009c3b is now applied above; patch 010 is next.

This split keeps storage identity review separate from runtime/cache and UI
changes. Format version 1 describes serialization; it is not an enforcement or
administrator-approval attestation. 009c1 alone leaves the old runtime guard in
place. Do not close patch 009 or treat stored versioned policies as proof of
deterministic enforcement before 009c2/009c3 are complete.

009c1's approved six-file diff is applied unchanged. It adds `input_conditions.py`,
updates management policy resolution/equivalence and safe deduplication, recognizes versioned inventory
rows, and adds an isolated real-JWT/RBAC SQLite HTTP diagnostic. Its existing
PostgreSQL resolution diagnostic changes only the expected stored format and
the unique test-prefix cleanup filter; it was not run. New canonical conditions
use `custom_resource` plus integer `resource_condition_version: 1`. Unknown
condition keys, invalid marker types/versions, unsupported state-dependent
conditions and oversized canonical text reject. Output policy storage remains
unchanged. Old unreviewed definitions and assignments are not automatically
reused, merged, rewritten, disabled or deleted.

Saved-source checks passed: the new HTTP diagnostic covers case/punctuation/Unicode
identity, duplicate rejection, supported storage, rejected creates/updates,
metadata-only legacy refusal, explicit disabling, assignment-safe App A edits
without changing App B, global resolution, retained legacy rows and safe
deduplication. The inventory, binding and grammar diagnostics also passed
against saved source; all six Python files parsed. Approved-patch reverse
verification and whitespace checks passed. These checks used
disposable in-memory SQLite with dotenv disabled. No real environment, live
database inventory, PostgreSQL check, migration, model/MCP call, restart or
deployment ran. Exact code previews remain in chat only. 009c1 itself did not
change runtime enforcement; 009c2 is now applied above, with 009c3 next.

009a's compatibility grammar accepts simple single-token legacy names, quoted
literal names, resource prefixes (including plurals), name/named/called/titled
qualifiers, and issue/PR number qualifiers. Unquoted multiword conditions,
comparisons other than equality, AND/OR, negation, wildcard operators and ordered workflows
are rejected. Words such as AND inside a quoted title remain literal title text.
Empty text retains the existing broad-resource meaning. Full input length is
bounded at 1,000 characters; empty literals, control characters in literals and
invalid Unicode surrogate values are rejected.

The legacy storage canonicalizer removes quotes, lowercases values and folds
Unicode. 009c1 routes new input selectors through versioned serialization and
isolates legacy literals from automatic reuse/deduplication; it cannot reconstruct
lost path/branch case. Before rollout, use 009b's inventory helper to review
canonicalized multiword values and case-sensitive names. Ambiguous legacy rows
may require explicit administrator repair. Preserve reusable-policy/assignment
isolation and avoid merging different literal targets. No schema migration or
live backfill ran.

Verification on 2026-10-15: the approved two-file diff was applied unchanged.
Saved-source `python -B tests/test_resource_conditions.py` passed 22 supported
selectors and 32 rejection cases; both Python files parsed. Approved-patch
reverse verification and whitespace checks passed. The earlier reproduction used
SQLite configuration with dotenv disabled, made no database queries and invoked
no external services. These are grammar checks, not runtime enforcement or
PostgreSQL evidence. No live database, migration, environment edit, service
restart or deployment ran. Exact code previews stay in chat only. 009b is
applied below; every later slice still requires its complete diff and approval.

009b's exact four-file diff was approved in chat and applied unchanged. It adds
isolated GitHub resource bindings, a read-only input
condition inventory and two offline diagnostics. At 009b, production modules did
not import these helpers; 009c1 now uses bindings for management validation.
009b itself did not change management validation,
stored rows, prompt compilation, runtime enforcement, tool launch or assignments.

Verified upstream contract: metadata-only inspection of the exact Dockerfile
digest identifies GitHub MCP 1.0.4 at revision
`c3dedbece0bf3834829f638a245fb3c51cd98d0b`. Public source files at that revision
were read in ignored scratch: [issues](https://github.com/github/github-mcp-server/blob/c3dedbece0bf3834829f638a245fb3c51cd98d0b/pkg/github/issues.go),
[pull requests](https://github.com/github/github-mcp-server/blob/c3dedbece0bf3834829f638a245fb3c51cd98d0b/pkg/github/pullrequests.go),
[repositories](https://github.com/github/github-mcp-server/blob/c3dedbece0bf3834829f638a245fb3c51cd98d0b/pkg/github/repositories.go)
and [repository helpers](https://github.com/github/github-mcp-server/blob/c3dedbece0bf3834829f638a245fb3c51cd98d0b/pkg/github/repositories_helper.go).
No container was started or image pulled. Direct local Docker runs currently
use an unpinned image, so this reviewed source contract cannot be assumed for
every local/custom executable until 009c addresses that boundary.

Implemented helper capabilities (runtime integration is now applied in 009c2c):

| Action/resource | Observable selector |
| --- | --- |
| Create issue | Title, with exact create method discriminator |
| Update/comment issue | Number; update requires the update method discriminator |
| Create PR | Title, source branch, or target branch as separate single equalities |
| Merge PR | Number, without source/target branch lookup |
| Review PR | Number for create/submit-pending/delete-pending methods; thread-only methods reject |
| Delete file | Canonical relative path |
| Push files | Each nested file path; exact `README.md` restriction rejects because empty-repo initialization creates it implicitly |
| Create/fork repository | Canonical name; fork refers to the source repository name |

Update PR selectors are excluded because some updates can also run through
`issue_write`; conditional branch creation is excluded because `push_files` can
create missing/default branches without exposing every resulting branch name.
Create/update file selectors are excluded because the shared upsert action
depends on remote state. Updates' replacement titles and merge calls' commit
titles are not authoritative existing-resource titles. Conditions requiring
those states need explicit rejection or a separately reviewed trusted lookup.

Bindings preserve path/branch case and punctuation. Titles and repository names
compare case-insensitively, retaining existing case-equivalence intent. Numeric
arguments must be positive 32-bit integral values, including integral JSON
floats, without boolean/text coercion. Qualified PR heads compare the branch
portion. Leading/trailing whitespace, ambiguous path/reference syntax and
noncanonical repository names reject. Every nested push path is validated;
unrelated body/message/content/owner values cannot satisfy a selector. This is
an intentionally conservative subset, not a full Git reference/path parser.

The inventory defaults to help without loading dotenv or creating an engine.
Explicit `--database` opts into configured PostgreSQL reads in a read-only,
repeatable-read transaction. SQLite CLI support is limited to disposable
in-memory diagnostics to avoid creating a file database during inspection.
The callable inventory suppresses autoflush, prefers normalized metadata,
includes disabled/unassigned definitions and reports enabled app/global
assignment scope. It labels broad definitions, literal candidates requiring
administrator review, and unsupported conditions/metadata. It omits literal
values, descriptions and credentials, and never rewrites or disables rows.
Broad means no custom selector; it is not an enforcement certification. All
literal candidates require review because earlier canonicalization may have
irreversibly removed quotes, case or Unicode distinctions.

Saved-source checks: both new diagnostics passed using disposable in-memory
SQLite; the saved 009a grammar diagnostic also passed.
They cover field look-alikes, shared methods, qualified heads, missing/malformed
targets, nested files, rejected state-dependent conditions, normalized metadata,
assignment scope, disabled rows, default no-connect behavior, no autoflush,
private-value omission and actual SQLite refusal of an attempted CLI write.
All four saved Python files parsed. Approved-diff reverse verification and
whitespace checks passed. No actual database inventory, PostgreSQL
transaction verification, real `.env`, migration, model/MCP execution, restart
or deployment ran. The exact non-doc diff remains in chat only. 009c1 is applied
above along with 009c2. Closing 009 still requires 009c3 assistant/UI regressions
and the recorded rollout checks.

Before closing 009, verify exact title/path/branch/number matching, look-alike
arguments, missing fields, shared-tool methods, unsupported combinations, stale
compiled rows, app/global assignment scope and warm-cache handling. Ordered
workflows such as A -> B -> C remain a separate future feature.

### 010: Frontend Framework Dependencies

The manifest pins Next.js and its ESLint config to 13.5.11. Recheck official
security advisories and supported upgrade paths when preparing this patch;
do not choose a target from stale audit notes. Upgrade related React/tooling
dependencies only as required by that reviewed target, with a reproducible
lockfile. Verify TypeScript, lint, production build, same-origin proxy behavior,
authentication, and core management screens. Keep this separate from UI redesign.

### 011: Frontend Node Runtime

All three frontend Dockerfile stages currently use `node:20-alpine`. Confirm
the supported runtime compatible with patch 010, update stages and relevant
tooling/types together as needed, and test the built image. Preserve non-root
execution, narrowly granted bind capability, direct port 80, and internal backend
port 8000. Read `containerisation.md` and `work-computer-handoff.md` first.
Building or publishing release images remains a separate explicit action.

### 012: Authentication Throttling

Management login currently performs password verification without a local
throttling boundary in the handler. Bound attempts using an approach appropriate
to the deployed process count, with generic rejection responses, bounded state,
and a clear trusted-proxy/client-IP contract. Include password-change/reset and
policy-assistant cost controls in the review, but split them into separately
reviewed follow-ups if needed. Verify burst limits, recovery, unrelated users,
unknown/disabled accounts, and metadata-only rejection logs using a fake clock.

### 013: Temporary Password Expiry And First Login

Admin-issued passwords are one-time disclosures, but expiry and forced
replacement are unfinished. Implement a bounded setup/reset state, restricted
first-login access, expiry, atomic password replacement, and session
invalidation. Preserve the existing current-password-verified self-service
change behavior. Read the architecture and historical handoff preview before
proposing the schema; that older preview was not applied.
Verify create/reset, expiry, restricted access, completed replacement, concurrent
changes, and invalidation. Migration execution is a separate deployment step.

### 014: Request And Conversation Bounds

Runtime trims context after loading conversation turns; supplied history and
stored reads still need bounds before expensive processing. Define compatible
message, turn-count, conversation-ID, and request-body limits and bounded history
queries. Keep newest-turn selection and app/conversation isolation intact.
Avoid treating a character limit as a network byte limit. Review agent/tool
execution limits too, and split that work if it changes behavior substantially.
Verify boundaries, Unicode, long histories, empty/new conversations, rejection
before runtime construction, and the database index/query plan where relevant.

### 015: Legacy Data Helpers

`scripts/backfill_existing_app_users.py` currently links every user to every
app and commits immediately. Replace broad implicit grants with explicit
targets, a dry-run preview, and opt-in application, or retire the helper with a
documented replacement. Review other seed/backfill helpers for equivalent
access-changing behavior without rewriting historical schema migrations blindly.
Use disposable data to verify no mutation by default, targeted application,
idempotency, and preservation of existing assignments.

### 016: Dependency Footprint

2026-10-16 execution finding: the retained pinned Python closure has advisories
in sixteen packages. Patch 016 includes compatible patched backend versions and
clean-install/regression verification, in addition to removing unused provider
extras. This evidence-based expansion addresses the same dependency boundary;
no new feature or extra review iteration is introduced.


The Python requirements include provider integrations that the runtime does
not execute, alongside many pinned transitive packages. Trace actual imports,
NeMo requirements, scripts, and intended support before removing anything.
Separate direct runtime requirements from optional diagnostics/provider work
where useful. Check current advisories during implementation. Verify a clean
environment install, compiler/guard checks, and both supported MCP launch modes
without enabling write operations. Package presence alone is not proof of a
security issue or redundancy.

### 017: Generated Artifacts And Dead Code

Confirmed tracked generated artifacts include `frontend/tsconfig.tsbuildinfo`
and `logs/error.log`. Remove generated content from version control and add
narrow ignore rules while preserving useful source/configuration files. Inspect
logs through secret-safe checks if necessary; do not copy log contents into docs.

Candidates requiring reference checks include the empty
`src/nemo_mcp_guardrails/helper/utility.py` and the unmounted
`frontend/components/apps/app-llm-settings.tsx` flow. Decide whether to remove or
deliberately reconnect the latter; do not reconnect privileged UI as incidental
cleanup. Do not remove tests merely because they have no importers: many are
standalone diagnostics explicitly documented in `AGENTS.md`. Record evidence
for each removal and verify imports/build plus affected diagnostic entry points.

### 018: Regression Entry Point And Final Verification

Classify retained checks as offline, disposable-database, or external-service
diagnostics. Provide a clear default command that cannot accidentally use real
dotenv credentials or mutate a live database. Require deliberate opt-in for
DB/Azure/GitHub checks and keep blocked write tests distinct from allowed reads.
Add only tests that cover meaningful boundaries; avoid duplicate wrappers.

Run the relevant security regression set, frontend validation, and diff checks;
record remaining limitations and follow-up findings in this backlog. Recheck
changed boundaries rather than claiming the project is security-certified.
Deployment smoke verification stays in the existing deployment plan and requires
its own authorized environment; this roadmap does not authorize migrations,
service restarts, live writes, image publication, or Azure deployment.

## Policy Authoring Assistant - 2026-10-09

- Implemented local UI prototype: labelled sample prompt responses, a condition
  flowchart, suggested custom-resource wording, illustrative input-rail cases,
  explicit draft application, and separate related-policy previews.
- `/policy-preview` provides a database-free, login-free UI sandbox using
  existing mock options. Created drafts are in-memory only. This page does not
  change access control on real management routes.
- Current saved examples cover PR 17 merges, PR creation targeting exact branch
  Production, an unsupported compound merge condition returning no draft, and the
  output word-ban example for "hello". 009c3b replaces the earlier executable
  non-staging-to-production samples.
- The drafting selector and Yes/No boxes are removed. One Generate policy
  button remains; example buttons load saved visualizations immediately and
  edited custom descriptions use live AI.
- Live AI generation and authenticated integration are implemented under
  `/policy-assistant/suggest`, using the existing backend Azure settings and
  enabled metadata. Typed JSON validation rejects unsupported primary/related
  combinations and assignment-scope fields. Ambiguous prompts can clarify.
- The normal logged-in Create Policy form renders dynamic flows, wording,
  examples and independent related drafts. Cancellation, stale-response
  protection and bounded timeouts are implemented. `/policy-preview` remains
  offline/sample-only. No hosted-database connection or enforcement change
  was made, and generation never saves policies or invokes GitHub tools.
- Output AI drafting uses tagged, connector-independent `output_rule` drafts,
  response examples and `Output -> Custom resource` previews. Existing output
  storage/compilation/enforcement is unchanged; no additional bans are suggested.
- Other-connector input authoring remains deferred until GMS implements those
  connectors. GitHub input drafting and related suggestions are preserved.
- Remaining: deployment verification, broader semantic evaluation of generated
  policies, durable browser regression coverage, and future authoring model
  configuration/rate-limiting administration if required. Example outcomes
  are predictions; actual runtime enforcement still needs separate evaluation.
- See `frontend-screen-plan.md` and `testing-notes.md` for behaviour and checks.

## Current Status

The GMS backend prototype now has these core runtime pieces:

- App authentication for runtime endpoints with `X-App-ID` and `X-API-Key`.
- Management login and `/management-auth/me` now use scrypt password hashes and
  signed JWT bearer tokens. Public signup is disabled; system admins create
  users from `/management-users` and issue temporary passwords displayed once.
- Existing users receive `name` and unique `username` values backfilled from
  email. Settings loads the authenticated profile, saves those fields through
  `PUT /management-auth/me`, and Logout returns to the real Login page.
- App-scoped global plus app-specific policy assignment loading.
- DB-backed compiled prompt rules injected into NeMo prompt templates.
- App-scoped blocked GitHub MCP tool names.
- Authenticated `POST /v1/guardrails/run`.
- Postgres-backed conversation history with request-size trimming.
- Separate app-selected LLM configs for guardrail rails and the main agent.
- `GET /llm-configs` exposes readable configuration metadata without credential
  references. The named-selector component currently has no application-route
  mount; management API selection remains available.
- System-admin-only `POST /llm-configs` creates Azure-compatible metadata with an
  optional `env:VARIABLE_NAME` credential reference. The runtime resolves that
  reference per selected main/guardrail model and otherwise uses the shared
  `AZURE_OPENAI_API_KEY` fallback.
- Controlled runtime responses for connector tool errors and Azure output
  content-filter failures.
- App-scoped deterministic checks cover explicit quoted output prohibitions
  such as `Cannot say 'hello'`, `Do not allow the word 'hello'`, and common
  `don't`/`dont` wording. Broad rules such as `No profanities` remain NeMo
  semantic classifications.
- Runtime responses expose `output_rail_source` and Azure-reported filtered
  categories. The frontend distinguishes `blocked (Azure: category)` from
  `blocked (GMS)`; generic Azure events fall back to `blocked (Azure)`.
- Azure filtering during NeMo input self-checks is converted from an unhandled
  `500` into a controlled runtime block. Responses expose `input_rail_source`
  and `input_rail_categories`, and Runtime Test renders labels such as
  `Input: blocked (Azure: hate)` while leaving output as `not run`.
- LangChain can convert an Azure-filtered agent completion into a category-less
  `ValueError`. The runtime recognizes that exact provider message and returns
  `Output: blocked (Azure)` instead of HTTP `500`.
- MCP policy matches now raise `ToolGuardViolation` before the connector call.
  `/run` reports `tool_guard_status` and `tool_guard_source`, skips output rails
  after a guard violation, and Runtime Test shows `Tool guard: blocked (GMS)`.
  The coverage count is labelled `Guarded tool types` rather than implying the
  current request invoked every covered tool.
- Centralized single/bulk policy assignment payloads for app and global
  assignments, with readable app and policy labels in API responses.
- Developer-friendly client-ID aliases for app lookup and app-specific policy
  assignment management.
- App connector management APIs now list, create/update, update, and delete
  app connector links by app ID or client ID.
- GitHub connector credentials can now be resolved from
  `app_connectors.credential_reference` when it uses `env:VAR_NAME`.
- Frontend planning docs now exist for the Next.js 13 build:
  `frontend-api-map.md`, `frontend-screen-plan.md`, and
  `frontend-demo-flow.md`.
- The first Next.js 13 frontend scaffold now exists under `frontend/`. It
  implements the uploaded Figma screens and current management pages:
  `/login`, `/signup` admin-managed notice, `/apps`, `/apps/[clientId]`,
  `/policies`, `/user-management`, and `/settings`.
- Production-style frontend and backend Docker images now build successfully.
  Local Compose runs them with Postgres and pgAdmin, and the frontend
  same-origin `/api/gms` proxy reaches FastAPI over the private Compose network.
  The backend image bundles the native GitHub MCP executable, so neither local
  Compose nor the Azure Container Instances target needs a Docker socket.
- The normal-developer Apps workflow is implemented: `/apps` lists and opens
  assigned client applications; `/apps/[clientId]` provides Overview,
  Connectors, LLM, Policies, and Runtime Test tabs backed by FastAPI. App
  creation is system-admin-only.
- The admin-only User Management workflow is implemented: `/user-management`
  lists users, creates accounts with temporary passwords displayed once, resets
  passwords, blocks/enables users, changes system role, and links users to apps
  as app developers.
- App API keys are now backend-generated. Create and regenerate responses show
  the plaintext key once, GMS stores only the hash, and regeneration invalidates
  the previous key.
- Settings now provides a class-based app-wide dark theme. It previews
  immediately, saves the selected theme in browser `localStorage`, and restores
  it before rendering on later visits.
- The `/policies` page now has a typed read/write API adapter. When
  `frontend/.env.local` sets
  `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000`, it loads real apps, global
  policy assignments, and app effective policy assignments from FastAPI. When
  the env var is absent, it stays in mock mode for static/Vercel design demos.
- The create-policy modal now writes through FastAPI when backend mode is
  enabled: it creates the reusable policy, assigns it globally or to the
  selected app, reloads DB-backed assignments, and closes only after success.
- The same Create/Edit modal now supports input and output policies. Policy
  naming is available immediately; input mode uses the cascading structured
  fields, while output mode replaces them with a required free-text output
  rule. Custom output categories compile through a general NeMo output
  classifier while the credential category keeps its specialized wording.
- Policy storage now keeps names in `policies.description` and output behavior
  in `conditions.output_rule`. Loaders retain a legacy-description fallback.
  `scripts/migrate_output_policy_rules.py` backfills existing output rows and
  refreshes their compiled rules. Runtime Test displays input and output policy
  counters separately.
- Output rules now compile as restriction statements rather than independent
  yes/no instructions. `self_check_output` performs one OR-style decision: a
  violation of any active output policy blocks the response.
- `output_guard.py` extracts quoted phrases from explicit `cannot`, `must not`,
  `do not`, and `never` rules. Matching is case-insensitive and reports debug
  source `deterministic_output_phrase`.
- Policy creation now resolves structural equivalence before inserting. The
  backend returns `created`, `reused`, or `already_assigned`; equivalent names
  do not create duplicate policy definitions, and app requests do not add a
  redundant assignment when the same policy is already active globally.
- Frontend Delete now removes only the selected app/global assignment. The
  reusable policy definition remains available for other apps.
- Direct reusable policy-definition deletion is admin-only and now refuses to
  delete policies that are still assigned globally or to any app. Assigned
  deletes return `409` with assignment references.
- Frontend Edit is assignment-safe. It resolves the edited behavior, switches
  only that app/global assignment to an existing or newly created reusable
  policy, and leaves other apps on their previous policy.
- Policy rows on the main Policies page and app-detail Policies tab now open a
  shared backend-backed summary modal without interfering with Edit/Delete.
- Optional `conditions.custom_resource` values now flow into compiled input
  rules and immutable MCP guard rules. 009c2c binds checks to reviewed MCP fields
  and methods, preserving literal/case semantics and refusing unobservable
  conditional targets before connector invocation.
- New input custom-resource phrases use the versioned literal format from
  009c1. Path/branch case is preserved; title/name case is folded. Unreviewed
  legacy literals are excluded from automatic reuse and consolidation.
- `GET /policy-options` exposes enabled normalized tool mappings. The policy
  form cascades connector -> action -> valid resources and omits connectors
  without mappings, including the current SharePoint placeholder.
- Policy mutation warnings render above open dialogs, policy naming/global
  controls appear first, and the Apps list omits redundant client-ID and
  authorization columns.
- App/global assignments now store optional `display_name` values, so each app
  can name a shared policy independently. The frontend prefers this name.
- `scripts/deduplicate_policies.py` consolidates legacy equivalent policy rows;
  `scripts/migrate_policy_assignment_display_names.py` adds/backfills the
  assignment display-name columns.
- FastAPI allows configured frontend origins through `NEMO_CORS_ORIGINS`; the
  committed local default covers `http://127.0.0.1:3000` and
  `http://localhost:3000`.
- Policy create/update now automatically refreshes `compiled_policy_rules`;
  old compiled rows are marked stale and disabled.
- HTTP runtime integration coverage now proves an authenticated app can pass an
  allowed read request and block an assigned GitHub write policy through
  `POST /v1/guardrails/run` without Docker or Azure.
- Runtime construction now checks `app_connectors` before GitHub MCP tools are
  built and rejects apps that are not linked to the enabled GitHub connector.

Current presentation/demo scope:

- GitHub MCP is the only connector that needs to be demonstrably supported for
  the upcoming presentation.
- The frontend currently exposes only GitHub and SharePoint in its connector
  selector. GitHub is executable; SharePoint remains a UI/metadata placeholder
  until backend mappings and runtime support are implemented.
- Policy-table icons distinguish scope and connector: global assignments use a
  globe, app-specific GitHub/SharePoint assignments use connector marks, and
  unknown legacy connectors use a folder fallback.
- SharePoint, Outlook, and other connectors remain target-architecture
  extensions and should not block the near-term backend/frontend milestone.

## Immediate Priority

### 1. Move Hardcoded Self-Check Behavior Out Of `config/prompts.yml`

Problem:

- `config/prompts.yml` still contains GitHub-specific and credential-specific
  examples.
- Active policy behavior should come from Postgres policy rows and
  `compiled_policy_rules`.
- The output rail can false-positive when the classifier reacts to restricted
  words in the policy text instead of only inspecting `{{ bot_response }}`.

Status:

- Implemented in `config/prompts.yml`: the templates are now generic and
  instruct NeMo to evaluate only the user message or assistant response against
  injected active DB rules.
- Implemented in `policy_compiler.py`: the default credential output rule now
  avoids listing specific sensitive categories in the compiled self-check
  prompt and instead checks for actual sensitive credential or secret
  configuration values.
- Local DB updated: existing credentials output policy and its
  `compiled_policy_rules` row were refreshed to the safer wording.

Follow-up verification:

- Confirm the harmless hello response passes output rails for an app with only
  the global credential output policy.
- Keep DB rules as the source of actual policy behavior.
- If the runtime still blocks unexpectedly, set `NEMO_RUNTIME_DEBUG=true` before
  starting `scripts/run_api.py` to inspect the output-rail source and tool-event
  metadata. Raw agent output, tool arguments/results/errors, and output rule
  text are excluded from client debug fields, including after blocks or
  output modifications.
- If Azure content-filters the output self-check, return a controlled block
  with source `azure_content_filter`, preserving reported categories. A short
  secret-pattern scan cannot substitute for classification of every active
  output policy, so unclassified output must not be released.
- This can also block harmless responses when Azure refuses the classification.
  Evaluate classifier prompt wording/provider configuration separately.
- Database policy-loader fallback paths remain a separate security follow-up:
  failed reads must not silently remove app/global enforcement rules.

Future extension:

- Store prompt templates or prompt-template versions in Postgres if admins need
  configurable classifier wrappers later.

### 2. Keep Real Allowed/Blocked HTTP Runtime Integration Coverage Green

Current state:

- `tests/test_app_auth_http.py` verifies authentication, runtime
  reachability, conversation history, truncation, and controlled error branches
  with fake runtime pieces.
- `tests/test_guardrails_run_http.py` creates a temporary authorized app,
  creates and assigns a GitHub issue-creation block policy, then calls
  `POST /v1/guardrails/run` with allowed and blocked prompts.
- The test uses real DB policy assignment, prompt-rule loading, and blocked-tool
  loading, but fake rails/agent so Docker, GitHub MCP, Azure, and write tools
  are not touched.

Needed:

- Keep `GITHUB_MCP_READ_ONLY=1` for scripted tests.
- Add real-Docker/Azure coverage only as an explicit opt-in harness later.

## Near-Term Backend Work

### 3. Broaden Automatic Compilation Coverage

Current state:

- `POST /policies` creates the compiled rule inside the same transaction.
- `PUT /policies/{policy_id}` stales/disables old compiled rows and creates a
  fresh active rule when the policy remains enabled.
- Disabling a policy leaves no active non-stale compiled rule.
- Invalid compiler input returns `400` without partially persisting the policy.
- `POST /policies/compile-rules` remains available as a manual full resync.

Needed:

- Decide whether assignment changes should trigger cached app-policy bundle
  invalidation once Redis or another cache is introduced.
- Keep `tests/test_policy_auto_compile.py` in the verification set whenever
  policy CRUD changes.

### 4. Finish Runtime LLM Provider Support

Current state:

- `main_llm_config_id` and `guardrail_llm_config_id` are respected.
- Azure OpenAI-compatible provider rows are executable.
- System administrators can create Azure metadata through `/llm-configs`;
  developers can list choices and select their linked app's main model. The
  reusable named-selector component is currently unmounted by application routes.
  Raw keys never pass through the browser or API.
- Selected LLM configurations can resolve distinct `env:VARIABLE_NAME` API
  keys at runtime.
- Creation and runtime construction require the default Azure origin or an
  exact HTTPS origin in backend `GMS_ALLOWED_LLM_ENDPOINTS`. Runtime clients
  refuse redirects, including for existing stored configurations.
- Non-Azure providers such as Gemini return a clear unsupported-provider error.

Needed:

- Add provider adapter functions for future providers.
- Resolve `credential_reference` through a secrets manager instead of `.env`
  for production deployments.
- Add app-specific model/credential grants; endpoint approval and admin-only
  provisioning do not restrict which existing catalogue choices an app can use.
- Keep guardrail-classification LLM and main-agent LLM independently
  configurable.

### 5. Add Connector Management APIs And Credential Resolution

Current state:

- `app_connectors` stores which connectors an app can use.
- Runtime checks enabled GitHub connector access before constructing GitHub MCP
  tools.
- App connector links can be managed through `/apps/{app_id}/connectors` and
  `/apps/by-client-id/{client_id}/connectors`.
- `tests/test_app_connector_api.py` verifies app connector CRUD, connector
  lookup by name or ID, upsert behavior, and missing-link errors.
- Runtime resolves GitHub MCP credentials from `credential_reference` when it
  uses `env:VAR_NAME`, and falls back to `GITHUB_PERSONAL_ACCESS_TOKEN` when
  no connector-specific reference is set.
- `tests/test_runtime_connector_credentials.py` verifies default PAT fallback,
  app-specific `env:VAR_NAME` references, missing env vars, and unsupported
  reference schemes.

Needed:

- Add a real secrets-manager resolver for references such as `vault:...`.

### 6. Protect Management/Admin APIs

Current state:

- Completed. Management CRUD requires JWT authentication.
- App reads/writes are filtered through active app-developer `app_users` links;
  legacy `owner` links are still accepted for compatibility, viewer links no
  longer grant app access, and system admins bypass app membership.
- App creation is system-admin-only and new apps atomically link the admin
  creator as an app developer.
- Global assignments, direct policy mutation/compilation, and allowed-test
  mutation are restricted to system admins.
- The frontend automatically sends its saved JWT and hides or disables
  admin-only global-policy and guardrail-LLM controls for developers.
- Admin creation/reset already returns a generated password for either role.
  Copy Password now handles denied/missing clipboard access and fallback errors.
- Settings supports voluntary password changes after current-password
  verification. Replacements are 15-256 characters; old sessions are rejected
  after a change or admin reset through an HMAC-derived JWT password version.
  No schema migration was needed. Legacy tokens require a fresh login.

Follow-up:

- Remaining password priority: required personal-password setup after admin
  creation/reset, temporary expiry, compromised-password screening and throttling.
- The older Stage 1 schema preview was NOT applied: it proposed
  `must_change_password`, `temporary_password_expires_at`, and `session_version`,
  an extended management-auth migration, and isolated schema-default tests.
  Revisit that preview before implementing forced setup: session invalidation
  now works without a session_version column. See `work-computer-handoff.md`.
- Then enforce restricted setup and credential expiry with frontend/backend
  coverage for both roles and direct-API bypass attempts. Voluntary changes,
  current-password verification and reset/change session invalidation are done.
- Confirm temporary expiry, secure delivery/identity verification, production
  HTTPS and MFA, and sole-admin recovery. Email recovery remains deferred.
- Expand audit coverage only when new management mutation route families are
  added; the current admin Traffic Logs and Audit Logs screens are implemented.

## Later Backend Work

### 7. Remove Legacy Policy String Columns

Current state:

- Normalized connector/action/resource IDs exist.
- Legacy flat policy columns remain as compatibility fallback.

Needed:

- Ensure every create/update/load path uses normalized IDs.
- Remove `policies.connector`, `policies.action`, and `policies.resource` only
  after stable verification.

### 8. Add Argument-Level And Workflow-State Policies

Needed for policies such as:

```text
allow merge A -> B -> C only
block merge B -> A -> C
```

Tool-name denylisting is not enough. These policies need:

- Tool argument checks.
- Workflow state storage.
- Ordered transition validation.

### 9. Add Optional Write-Capable MCP Test Harness

Normal tests must remain read-only.

Future write tests should be:

- Explicitly opt-in.
- Pointed at a throwaway repository.
- Run with a limited token.
- Kept separate from the standard test suite.

### 10. Frontend Management App

Target frontend:

- Next.js 13.
- Developer login.
- App list and app detail screens.
- Policy assignment management.
- Global policy management for admins.
- Later: visual policy builder.

Current implementation:

- `docs/frontend-api-map.md` maps backend endpoints to frontend screens.
- `docs/frontend-screen-plan.md` proposes the first app structure and
  component breakdown.
- `docs/frontend-demo-flow.md` defines the GitHub MCP presentation flow.
- `docs/figma-design-intake.md` records the uploaded Figma screens and
  interaction notes.
- `frontend/` contains the Figma-matched implementation, a read/write
  API-backed `/policies` adapter, and functional app list/detail routes.
- `/policies` now loads apps and assignment summaries first. Policy definitions
  and builder options are loaded lazily when Create or Edit is opened, reducing
  the initial backend request set from four requests to two.
- `/user-management` provides admin-only user creation, password reset,
  enable/block, role changes, and app-developer links.
- A reusable app LLM settings component uses a readable catalogue and named
  selectors; reconnecting it to an application route remains unfinished.

Next implementation slice:

- Add optional admin force-delete behavior only if supervisors want policy
  definition deletion to also remove assignment references.
- Add LLM configuration update/delete and ownership controls after the
  organization confirms its provider-administration workflow.
- Keep the audit route classifier synchronized with new management mutation
  route families.

### 11. Audit, Analytics, And Caching

Implemented foundation (2026-09-09):

- Added ORM models for runtime request metadata and ordered execution events.
- Request-level recording now saves HTTP status, runtime outcome, verified
  app identity, timestamps, duration, and two request lifecycle events.
- Execution-event collection records call boundaries, rail decisions, tool
  guard decisions, and skipped stages without raw content.
- Offline collector tests cover isolation, privacy, limits, and late callbacks.
- Admin-only runtime-log list/detail endpoints expose metadata and ordered
  events through management JWT authentication.
- Isolated HTTP endpoint tests cover authorization, filters, pagination,
  validation, and safe response fields.
- The admin Logs list/detail screens display metadata and execution events,
  with app/outcome filters, refresh, pagination, and dark-mode styling.
- Traffic detail also displays the captured user input and corresponding final
  response when content exists; this replaces the separate User Logs view.
- Central management audit middleware records sanitized metadata for app,
  policy, assignment, connector, user, LLM-config, allowed-test and profile
  mutations. Admin-only `/audit-logs` supports entity/outcome filtering and
  pagination, and the frontend exposes it as the Audit Logs tab.
- `tests/test_management_audit_http.py` covers successful/rejected/failed actions,
  actor attribution, excluded runtime/read requests, RBAC, filters,
  pagination, and request-body secret omission in isolated SQLite.
- Logs filters stack on narrow screens (2026-09-11); desktop filters remain
  side by side.
- Manual retention is implemented in `scripts/cleanup_runtime_logs.py`:
  dry-run by default, 30-day default retention, at most 500 completed requests
  per invocation, and atomic deletion of requests plus their events on `--apply`.
  SQLite checks passed; no live database cleanup was performed.

Remaining work:

- Verify authenticated Traffic/Audit navigation and mobile layout against the
  deployed backend. Captured traffic content is plain text and may contain
  sensitive user submissions.
- Keep suppressed output, private reasoning, and credentials out of log exports.
- Add an approved retention policy for `management_audit_logs`; runtime cleanup
  currently covers only runtime traffic records.
- Replace startup `create_all` schema evolution with a deployment migration
  step before running multiple backend replicas; simultaneous first startup can
  race while creating a brand-new table.
- Schedule and verify the manual retention command in Azure; add automated frontend regression coverage.
- PostgreSQL integration verification for the log-reading endpoints.
- PostgreSQL retention verification using disposable fixtures, including
  cutoff boundaries, event deletion, transaction rollback, and repeated batches.
- HTTP recorder regression tests for request isolation, error paths, and
  exclusion of secrets. Record observed events, not private model reasoning.
- Verify lazy policy-builder loading against an authenticated deployed backend
  and compare browser request timings before and after the change.
- Per-app runtime bundle caching is implemented with database-revision
  invalidation, a five-minute default TTL, concurrent-build deduplication, and
  a 32-app default in-process LRU limit.
- Verify cold-versus-warm Azure timings and tune runtime cache TTL/capacity.
- Consider shared Redis revision coordination only when multiple backend
  replicas need cache invalidation beyond the database fingerprint.
- Redis cache for compiled app policy bundles.
- Background workers for compilation and invalidation.

### 12. Registry And CI/CD

Current local milestone:

- Backend and frontend images build successfully.
- Compose health checks pass for frontend, backend and Postgres.
- Backend database health and frontend-to-backend proxy health are verified.
- Backend image bundles the pinned native GitHub MCP executable and does not
  require a Docker socket or root runtime user.
- Direct source runs retain the Docker-based GitHub MCP launcher by default.
- Backend and frontend image contracts use private backend port `8000` and
  public frontend port `80`. The non-root Node process receives only
  `NET_BIND_SERVICE` so it can bind the HTTP port.
- The Linux AMD64 frontend port-80 image build and non-root `/login` runtime
  probe passed on 2026-08-21.
- The corrected Linux AMD64 backend image rebuild, API/database/proxy health,
  and native GitHub MCP manual write-mode capability probe passed on
  2026-08-28. That backend image is still local and has not been pushed to ACR.
- The target hosting service is Azure Container Instances, not OpenShift.

Next deployment work:

- Rebuild and locally test the matching `guardrail-fe` release image, then
  reconfirm the already-corrected `guardrail-be` image.
- Push a matching image pair to `guardrail.azurecr.io`.
- Let the deployment team create a two-container ACI group with frontend
  public port `80`, private backend port `8000`, frontend
  `GMS_API_BASE_URL=http://127.0.0.1:8000`, and external PostgreSQL.
- Validate the deployed proxy, management login, policy CRUD, and guarded
  GitHub runtime.
- Add GitHub Actions pull-request CI for tests and Docker builds.
- Add main-branch image publishing with GitHub OIDC and Azure `AcrPush`.
- Publish immutable Git commit SHA tags alongside any `latest` tag.

## Current Useful Verification Commands

```powershell
.\.venv\Scripts\python.exe tests\\test_runtime_llm_selection.py
.\.venv\Scripts\python.exe tests\\test_app_auth_http.py
.\.venv\Scripts\python.exe tests\\test_app_auth.py
.\.venv\Scripts\python.exe tests\\test_policy_assignment_api.py
.\.venv\Scripts\python.exe tests\\test_policy_auto_compile.py
.\.venv\Scripts\python.exe tests\\test_guardrails_run_http.py
.\.venv\Scripts\python.exe tests\\test_runtime_connector_access.py
.\.venv\Scripts\python.exe tests\\test_app_connector_api.py
.\.venv\Scripts\python.exe tests\\test_app_policy_scope.py
.\.venv\Scripts\python.exe tests\\test_tool_guard.py
.\.venv\Scripts\python.exe scripts\debug_nemo_output_check.py
.\.venv\Scripts\python.exe tests\\test_nemo_mcp.py
```
