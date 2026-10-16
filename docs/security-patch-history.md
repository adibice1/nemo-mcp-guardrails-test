# Security Review Patch History

This records completed and prepared patches from the project security review.
The full ordered list of next patches lives in the
[security review sequence](open-work-backlog.md#security-review-patch-sequence),
the single backlog for this work. Keep summaries, status, verification, and
operational impact in docs. Show complete code diffs in chat only; do not store
code previews in docs. Mark a patch applied only after saving and checking the
approved changes; applied source does not imply a deployment or Git commit.

| Patch | Change | Status |
| --- | --- | --- |
| 001 | Runtime debug-content privacy | Applied to source |
| 002 | Literal policy text in NeMo prompts | Applied to source |
| 003 | LLM credential destination controls | Applied to source |
| 004 | Block output when Azure refuses classification | Applied to source; offline checks passed |
| 005 | Fail closed on database policy-loading errors | Applied to source; offline checks passed |
| 006 | Restrict app authorization changes to system admins | Applied to source; offline checks passed |
| 007 | Restrict connector credential-reference provisioning | Applied to source; offline checks passed |

## 001: Runtime Debug-Content Privacy

Raw agent output could be exposed through debug responses even when an output
rail blocked or modified it. Runtime responses now leave `debug_agent_response`
and `debug_output_rule_texts` null. Tool traces expose event and tool names only,
excluding arguments, results, and errors. `.env.example` disables debug by default.

Changed implementation: `src/nemo_mcp_guardrails/api/runtime.py`, `.env.example`,
and new `tests/test_runtime_debug_privacy.py`. Related API, backlog, testing,
and handoff documentation was updated.

Verification: six offline HTTP cases passed across debug enabled/disabled and
passed/blocked/modified output. No schema migration is required. This protects
client debug fields; it is not a general retention change for runtime user logs.

## 002: Literal Policy Text In NeMo Prompts

Database rule text could be interpreted as Jinja instructions. The prompt
compiler now parses YAML first and inserts encoded literal strings in a single
placeholder-replacement pass, preventing rule text from assigning template
variables or recursively expanding policy placeholders.

Changed implementation: `src/nemo_mcp_guardrails/prompt_rule_compiler.py` and
new `tests/test_prompt_rule_literals.py`. Runtime-flow and testing documentation
was updated.

Verification: 24 cases passed using the installed NeMo prompt renderer, including
Jinja expressions/directives, malformed syntax, Unicode, and empty rule sets.
No schema migration is required. Natural-language prompt injection remains a
separate concern.

## 003: LLM Credential Destination Controls

Developers could provision arbitrary model destinations and server environment
credential references. Configuration creation now requires a system administrator.
Creation and runtime construction require an exact backend-approved HTTPS origin;
runtime checks existing stored configurations before resolving their selected
credential references. Synchronous and asynchronous model clients refuse redirects.

Changed implementation: new `src/nemo_mcp_guardrails/llm_security.py`,
`api/llm_configs.py`, `api/runtime.py`, `runtime_factory.py`,
`frontend/components/apps/app-llm-settings.tsx`, and `.env.example`. Added
`tests/test_llm_endpoint_security.py`; updated model-selection/API fixtures and
provider, deployment, API, backlog, testing, file-map, and handoff docs.
Backend paths above are relative to `src/nemo_mcp_guardrails/` unless specified.

Verification: offline JWT/SQLite authorization, endpoint rejection, legacy-record
checks, and actual SDK redirect checks using mock transports passed. Model
selection, earlier regressions, full frontend TypeScript, Python AST checks, and
diff checks passed. The live-Postgres API diagnostic was not run.

Operational impact: `AZURE_OPENAI_ENDPOINT` is automatically approved; extra
origins require `GMS_ALLOWED_LLM_ENDPOINTS` and a backend restart. Existing
unapproved endpoints now return controlled HTTP 503 responses. No schema
migration is required. App-specific model/credential grants remain unfinished.
The guarded frontend component is currently unmounted by application routes.

## 004: Fail-Closed Output Classification

Status: **approved and applied to source**. The complete code diff was previewed in chat.
Its scope and the remaining patch order are recorded in the
[security review sequence](open-work-backlog.md#security-review-patch-sequence).

Previously, Azure refusal of an output self-check could release an unclassified
response if a short secret-pattern scan found nothing. The patch removes that
fallback and returns a controlled block, preserving reported Azure categories. It also
recognizes raw Azure and LangChain filtered-completion errors in this path.

Verification: the regression reproduced the bypass before application and passed
against saved source after application. Twelve offline HTTP cases cover
response serialization, SQLite conversation history, and log values at the
persistence boundary. Normal classifications, unrelated errors, and earlier
security regressions also passed against saved source. Python AST and diff checks
passed. The live-Postgres diagnostic was not run.

Operational impact: harmless output may also be withheld when classification is
refused. No new setting or migration is required. Database policy-loader fallbacks
need a separate reviewed patch.

## 005: Database Policy Loading

Status: **approved and applied to source**. See the ordered backlog for scope
and status; the complete code diff was previewed in chat only.

The patch replaces silent database fallbacks with a shared controlled error,
rejects malformed selected policy/compiled rows, and maps runtime setup failures
to a generic HTTP 503. Policy reads/compilation finish before model or MCP
construction. Tool-guard imports stop reading the database. Current rules are
loaded when a wrapper is built unless its caller supplies explicit rules/tools.

Static defaults remain available to offline diagnostics, including generated
input/output prompt rules. Authenticated runtime construction requires database
policies. Empty database results remain empty, rather than becoming defaults.
Cache revision/refresh failures stop the request; a later successful refresh can
recover without installing an incomplete policy bundle.

Changed files: new `database/policy_errors.py`, `database/policy_loader.py`,
`database/prompt_rule_loader.py`, `tool_guard.py`, `runtime_factory.py`,
`api/runtime.py` (all relative to `src/nemo_mcp_guardrails/`), and new
`tests/test_policy_fail_closed.py`.

Verification: the old fallback was reproduced before application; the new
isolated SQLite/mocked-boundary regression passed against saved source. Existing tool-guard,
cache, model-selection, debug-privacy, literal-rendering, LLM-endpoint, and
output-classification diagnostics also passed against saved source. AST and
diff checks passed. No live-Postgres diagnostic was run.

Operational impact: unavailable or malformed policies stop runtime requests.
Authenticated runtime deployments using explicit static policy mode must switch
to database policies. No migration, live database change, restart, or deployment
was performed. A consistent transaction-wide policy snapshot and active-row
completeness checks are outside this patch.
The HTTP 503 mapping covers runtime setup, not authentication/history failures or
the API startup database check.

## 006: Administrator-Controlled App Authorization

Status: **approved and applied to source**. The complete code diff was previewed in chat only.

The patch adds a field-presence permission check in `api/apps.py` before
model-reference validation or mutation: only a system admin can submit `authorized` through
app updates. App developer links with role admin/owner do not grant that system
permission. Unchanged values and null are also rejected for developers, and a
mixed request cannot partially rename/rebind an app before rejection.

The numeric-ID route is the only general metadata update route. The client-ID
alias remains readable but does not support metadata PUT. The frontend already
hides authorization and makes Client ID read-only; no UI change was needed.
Existing developer API name/client-ID editing is preserved without bypassing
revocation. Administrator enable/disable remains available without app membership.

Changed code files: `src/nemo_mcp_guardrails/api/apps.py` and new
`tests/test_app_authorization_http.py`. No schema or configuration changes.

Verification: old code allowed developer reauthorization; the approved saved-source
handler passed the isolated regression with real JWT,
RBAC, SQLite storage, 24 protected-field cases, and real runtime authentication
before/after revocation and rename. Password-change, management-audit, and
policy-loading diagnostics also passed against saved source. AST and diff checks
passed. No live database, Azure/GitHub call,
service restart, or deployment was used. Already-authenticated requests are not
cancelled by this change; API-key rotation behavior is unchanged.

## 007: Connector Credential Provisioning

Status: **approved and applied to source**. The complete code diff was previewed in chat only.

New connector links and explicit credential-reference fields require a system
administrator on both app-ID/client-ID routes. Linked developers retain existing
link toggles and unlink. Omitting a credential field during POST upsert preserves
the existing reference. Creating a link without that field is still admin-only,
preventing developer unlink/relink from selecting the shared default credential.
Frontend provisioning controls reflect those permissions.

GitHub references are validated against the default PAT variable plus exact
backend-approved names in `GMS_ALLOWED_GITHUB_CREDENTIAL_ENV_VARS`.
The runtime validates legacy references before reading secrets and constructing
model/MCP clients. Unapproved or unavailable credentials yield a generic 503;
invalid admin API writes yield 400. GitHub read-only defaults are preserved.
Non-GitHub connectors remain metadata-only and receive no new resolver.

Changed code/config files: new `connector_credentials.py`, `api/apps.py`,
`runtime_factory.py`, `api/runtime.py` (relative to `src/nemo_mcp_guardrails/`),
`.env.example`, frontend connector controls/API payload typing, new
`tests/test_connector_credential_security.py`, and two existing connector
diagnostic fixtures/expectations.

Verification: the old JWT-reference bypass was reproduced before application
with fake secrets. The isolated real-JWT/SQLite regression passed 60 protected-
field cases plus provisioning, omissions, scope, legacy, and runtime checks.
Six related offline diagnostics passed against saved source. Full frontend
TypeScript, scoped ESLint, AST, and diff checks passed. The live-Postgres connector
API diagnostic was not run. Browser verification was not performed.

No migration is required. Existing custom references need backend approval and
a restart after deployment. No real `.env`, live database, external service,
restart, or deployment was changed here. Backend operators remain trusted;
already-allowlisted legacy references are not retroactively tied to an admin
creator or per-app credential owner. Review existing links during rollout.

## 008: App-Specific Model/Credential Grants

Status: **design and slices 008a/008b/008c approved and applied to source**.
See the single plan in `open-work-backlog.md`. PostgreSQL/browser verification
and reviewed grant rollout remain open; no live rollout has been performed.

008a adds one constrained default-deny grant table, a standalone helper for
DDL/inventory previews and explicit reviewed-manifest seeding, and an offline
regression. The helper never changes existing grants, app selections or app
authorization. The 008b management API retains disabled grant rows when
revoking access so old bootstrap manifests cannot recreate them. No new runtime
or management permission behavior is included in this first slice.

Changed files: `src/nemo_mcp_guardrails/database/models.py`, new
`scripts/migrate_app_llm_grants.py`, and new
`tests/test_app_llm_grant_migration.py`. The exact diff was previewed in chat only.
Saved-source checks passed on disposable SQLite for schema constraints/cascades, write-free preview,
strict and stale manifest rejection, transaction rollback after insertion,
idempotence and disabled-grant preservation. App-authorization and connector-
security regressions also passed against saved source. PostgreSQL DDL compiled
only. AST parsing, approved-diff reverse verification, and whitespace checks
passed. No live database or external service was used, and no real environment,
live migration, restart or deployment was changed. Fixture schema/data changes
were confined to disposable SQLite.

008b is approved and applied. Its exact 13-file diff adds admin
grant management and retained revocation rows, app/purpose-specific model
options, admin-only global catalogue access, backend-approved LLM credential
names, explicit selection validation and grant mutation audit classification.
The complete scope remains in the backlog; code previews stay in chat only.

Changed files: new `llm_credentials.py`, new `llm_access.py`, new
`api/app_llm_grants.py`, `api/app_schemas.py`, `api/apps.py`, `api/llm_configs.py`,
`api/main.py`, `management_audit.py` (relative to `src/nemo_mcp_guardrails/`),
`.env.example`, new `tests/test_app_llm_grants_http.py`, and three existing LLM/
RBAC diagnostics. No new schema change was needed beyond 008a's grant table.

The new real-JWT/SQLite HTTP diagnostic and five related offline diagnostics
passed against saved source. AST parsing for all 12 changed/new Python files,
approved-diff reverse verification and whitespace checks passed. Two live-
PostgreSQL diagnostics have updated fixtures/expectations but were not run.
Runtime legacy credential checks and cold/warm grant enforcement were added by
008c below. No live database, real environment, live migration, restart, external
service or deployment was changed.

008c is approved and applied. Its exact 12-file diff adds live
grants for both runtime model purposes, exact grant/model cache comparisons,
lock/build rechecks, approved LLM credential resolution, generic setup failures
and app-scoped selector options without implicit defaults. The selector remains
unmounted. Existing diagnostic fixtures adapt to the new model-grant boundary.

Changed files: `llm_credentials.py`, `runtime_factory.py`, `api/runtime.py`
(relative to `src/nemo_mcp_guardrails/`), frontend API client/model settings,
new `tests/test_runtime_llm_grants.py`, and six related diagnostic fixtures or
messages. No new schema or backend environment setting was added in this slice.

The new real-app/JWT/SQLite runtime diagnostic and eight related offline checks
passed against saved source. Full frontend TypeScript, scoped ESLint, AST parsing
of all ten changed/new Python files, approved-diff reverse verification and
whitespace checks passed. Actual PostgreSQL behavior and browser verification remain
unverified. No live database, real environment, migration, restart, Azure/GitHub
request or deployment was changed. See the single backlog for remaining rollout
checks and limits; full code previews are in chat only. Both named/default
purposes require reviewed grants before deployment. Requests already admitted
may finish after concurrent revocation; provider calls are not cancelled.

## 009a: Literal Resource-Condition Grammar

Status: **approved and applied on 2026-10-15**. The exact two-file preview adds
`src/nemo_mcp_guardrails/resource_conditions.py` and
`tests/test_resource_conditions.py`: a pure parser for one resource-field literal
equality, limited legacy syntax, and an isolated offline diagnostic. Literal
case, punctuation and internal whitespace are preserved; unsupported compound
logic, malformed values and invalid Unicode surrogates are rejected.

The saved-source diagnostic passed 22 supported selectors and 32 rejection cases.
Both Python files parsed; approved-diff reverse verification and whitespace
checks passed. At 009a no management/runtime code imported the parser; 009c1
below now adopts it for storage validation. This foundation alone does not
fix the custom-resource enforcement boundary. 009b adds inventory tooling and
tool-field bindings below; live compatibility review and storage/runtime/assistant
integration remain open in 009c in the single backlog. No live database,
migration, environment edit, external
request, restart or deployment ran. Full code previews remain in chat only.

## 009b: Resource Bindings And Read-Only Inventory

Status: **approved and applied on 2026-10-15**. The exact four-file diff adds
`src/nemo_mcp_guardrails/github_resource_bindings.py`,
`scripts/inventory_resource_conditions.py`, `tests/test_github_resource_bindings.py`
and `tests/test_resource_condition_inventory.py`. Bindings use authoritative
fields and reviewed method discriminators, rejecting malformed targets and
unsupported state-dependent cases. The inventory requires database opt-in,
suppresses autoflush, reports enabled assignment scope and omits literal values.
It never rewrites, enables or disables stored definitions or assignments.

Both new saved-source diagnostics and the existing grammar diagnostic passed.
The SQLite checks include real refusal of an attempted CLI write. All four new
Python files parsed; approved-diff reverse verification and whitespace checks
passed. No real environment, live database inventory, PostgreSQL verification,
migration, model/MCP execution, restart or deployment ran. Public upstream
sources and pinned image labels were read during review; no container started.

At 009b management/runtime did not consume these helpers; 009c1 adopts them for
storage validation below. Runtime was unchanged at 009b; 009c2 now integrates
runtime validation, cross-tool/indirect effects and the pinned launcher contract
below. 009c3 assistant/UI alignment remains open. Live saved-policy compatibility review remains open.
The single backlog retains the ordered plan and limitations; exact code previews
remain in chat only.

## 009c1: Versioned Selector Storage And Management Validation

Status: **approved and applied unchanged on 2026-10-15**. The exact six-file diff
adds `input_conditions.py` and an isolated HTTP diagnostic, updates management
resolution/equivalence and safe deduplication, recognizes versioned inventory
rows, and adapts the existing PostgreSQL resolution diagnostic's expected format
and cleanup prefix. The approved non-doc patch has 342 insertions/19 deletions.

New supported input selectors store canonical field equality text plus integer
`resource_condition_version: 1` in existing conditions JSON. Paths/branches retain
case; titles/repository names fold case without losing punctuation or Unicode.
Unknown keys, invalid markers, unsupported conditions and oversized canonical
text reject before successful persistence. Broad input and output-policy storage
behavior are preserved. Legacy literals are excluded from automatic reuse and
deduplication; metadata-only edits require condition resubmission, while exact
disable-only edits remain available. Assignment-safe resolution can create a
reviewed definition without rewriting another app's legacy definition.

All four saved-source offline diagnostics passed: input storage HTTP/JWT/RBAC,
inventory, GitHub bindings and grammar. All six changed/new Python files parsed;
approved-patch reverse verification and whitespace checks passed. Tests use
in-memory SQLite with dotenv disabled. The PostgreSQL diagnostic was not run.
No real environment, live inventory/database, migration, model/MCP call, restart
or deployment ran. There is no schema migration or automatic existing-row rewrite.

Version 1 describes serialization, not enforcement or administrator approval.
009c1 itself left the runtime guard unchanged. 009c2 now integrates
runtime/cache/compiler enforcement and the MCP contract below; 009 remains open
for 009c3 assistant/UI alignment and the recorded rollout checks. Full code previews remain in chat only.

## 009c2a: Immutable Scoped Policy Snapshot

Status: **approved and applied unchanged on 2026-10-15**. The exact two-file diff
adds `database/runtime_policy_snapshot.py` and
`tests/test_runtime_policy_snapshot.py`: 425 added lines. One SELECT reads app
authorization, enabled global/app definitions, normalized connector metadata and
enabled compiled artifacts. Scalar projections avoid ORM identity-map reuse and
lazy queries; the reader suppresses autoflush and has no connection-module,
environment-loader or policy-default dependency.

Selected nonempty input conditions must already be supported canonical version-1
selectors. Unsupported broad combinations, unavailable/inconsistent normalized
metadata, invalid output definitions and missing/stale/duplicate/mismatched
compiled artifacts produce a controlled policy-loading error. Disabled historical
artifacts are ignored. Frozen values retain exact policy/compiler contents for
later cache comparisons and omit literal text from default representations.

The new saved-source diagnostic and four related storage/inventory/binding/grammar
diagnostics passed. Both Python files parsed; approved-patch reverse verification
and whitespace checks passed. Tests use in-memory SQLite, forbid dotenv loading,
count one SELECT despite pending/dirty ORM state, verify global/app isolation and
detect literal changes without version/timestamp changes. PostgreSQL SELECT SQL
compiled only; live PostgreSQL and concurrent-writer behavior remain unverified.

At 009c2a the reader had no active runtime consumer. 009c2b and 009c2c are now
applied below, connecting snapshots to runtime/cache and adding offline HTTP proof.
009c3 and patches 010-018 retain their order in the single backlog. No live
database, inventory, migration, model/MCP call, restart or deployment ran. The
complete approved code diff remains in chat only.

## 009c2b: GitHub Execution Contract And Compiler Artifacts

Status: **approved and applied unchanged on 2026-10-15**. The exact seven-file diff
adds `github_tool_contract.py` and `test_github_tool_contract.py`, updates input
capability validation and compiler artifacts, pins the runtime/full-runner Docker
image references, and adapts the launch diagnostic: 467 insertions/15 deletions.

Immutable rules bind conditions to authoritative fields and shared-method
discriminators, accounting for reviewed cross-tool and indirect write effects.
Broad restrictions cover indivisible operations that may perform the restricted
write. Conditional routes raise an evaluation error when the target cannot be
observed, rather than invent remote state. This can refuse otherwise valid
merge/fork calls under a file restriction. The catalogue helper selects reviewed
names, rejects ambiguous names and relevant schema drift, and permits read-only
catalogues. At 009c2b it was not connected to active tool construction; 009c2c
connects it below.

Conditional NeMo text names the actual field/literal/comparison, and generated
blocked prompts carry that literal. Broad input policies now pass the same
supported-write capability gate. Unsupported read-block definitions reject;
connector discovery metadata remains available. Docker launchers use the reviewed
Dockerfile digest, including the full runner, which retains hardcoded read-only
mode. Native configuration requires the bundled executable path. Provenance
depends on that pinned/bundled image; the schema gate does not authenticate a
substituted binary.

The new diagnostic and twelve existing offline diagnostics passed against saved
source. They cover launch settings, snapshots, storage/JWT/RBAC, inventory,
bindings, grammar, legacy wrappers, literal Jinja rendering, policy failures,
model grants/cache and connector credentials. The standalone compiler CLI passed.
All seven Python files parsed and matched the approved drafts exactly;
approved-patch reverse verification and whitespace checks passed. Child tests
disabled dotenv and used disposable SQLite/fake external boundaries.

No real `.env`, live database, image pull, binary/container/MCP process, model call,
migration, restart or deployment ran. The full GitHub runner was parsed only.
Actual binary/catalogue compatibility remains unverified. At 009c2b runtime
wrappers still flattened arguments; 009c2c connects the matcher/catalogue and
snapshots to runtime/cache and proves offline HTTP behavior below. Compiler
reporting names alone do not complete enforcement. Before eventual rollout, review/repair legacy conditions
and explicitly resync compiled rows for changed conditional text. No live resync
or data rewrite ran. The complete approved code diff remains in chat only.

## 009c2c: Shared Runtime Policy Snapshot And Field-Bound Enforcement

Status: **approved and applied unchanged on 2026-10-15**. The exact fourteen-file
non-doc diff has 559 insertions/156 deletions. Its complete preview remains in
chat only.

Authenticated runtime construction uses one validated immutable snapshot for
NeMo rules, input attribution, guarded tools and output phrases, including empty
scope without independent reloads. Exact contents join model grants and aggregate
revision in cache comparisons; fresh checks occur before reuse, after lock waits
and after builds, including when caching is disabled. Invalid or changed state
fails setup closed. Existing model-grant checks remain intact.

Reviewed catalogue filtering precedes field/method-bound tool matching in runtime
and the read-only full runner. An actual matched rule supplies its policy ID/name.
Malformed or unobservable targets stop with a controlled `tool_error`, evaluation
source/event reason, and no false matched-policy identity or raw argument content.
Standalone DB loaders reject unversioned/noncanonical selectors; conditional
wrappers require an executable binding. Manual broad tool-name sets remain for
diagnostics.

All nineteen saved-source offline diagnostics passed: the new authenticated HTTP
integration diagnostic plus eighteen related diagnostics, including six event
unit cases. The integration fixture uses real app authentication, in-memory
SQLite, actual runtime/snapshot/rails configuration, guarded tools, execution and
history persistence with fake external boundaries. It covers scope, empty rules,
shared methods, exact title/path matching, output phrases, policy identity,
evaluation privacy, stale artifacts, schema drift, cache changes with constant
aggregate revision, TTL zero and simulated lock/build interleavings. A compiled
LangGraph tool node propagates both guard error kinds without invoking the tool.
All fourteen saved Python files parsed and matched approved drafts exactly;
unchanged patch SHA256, reverse-patch and whitespace checks passed.

The full GitHub runner was parsed only. No real `.env`, live database, image pull,
model/MCP process, inventory, migration, resync, restart, publish or deployment ran.
Actual PostgreSQL concurrency, binary/catalogue compatibility and model quality
remain unverified. Already admitted requests may finish on their validated
snapshot after a concurrent policy change. Before rollout, review/repair legacy
conditions and resync changed compiled text through the existing admin path.
009c3a backend alignment is now applied below; 009c3b frontend alignment remains
next. Patch 009 and patches 010-018 retain their backlog scope and order.

## 009c3a: Assistant Draft Validation And Supported Policy Options

Status: **approved and applied unchanged on 2026-10-15**. The exact five-file diff
has 240 insertions/18 deletions; its complete approved preview remains in chat only.

Primary and related input drafts now pass the same condition preparation as
storage. Accepted selectors return canonical equality text. Unsupported conditions
or changed related-policy scope return clarification with no drafts. Related
suggestions must retain the primary connector, resource and canonical selector.
Input instructions describe executable field equalities and explicitly refuse
compound/negated conditions, workflows and unobservable branch-based merge
restrictions. Output drafting remains separate.

Policy options require enabled, connector-consistent metadata and the supported
write capability gate. Unsupported read-block/other-connector combinations are
excluded. Each resource gains an additive `condition_fields` list; an empty list
means broad scope only. This changes neither discovery metadata nor runtime tool
availability.

All seven saved-source offline diagnostics passed: assistant HTTP, the new
policy-options HTTP diagnostic, input-condition storage, runtime policy
integration, GitHub tool contract, resource bindings and grammar. Real JWT and
disposable SQLite cover authentication, canonical case/Unicode/quotes, related
scope changes, unsupported selectors, output isolation, metadata enable flags and
cross-connector ownership. All five saved Python files parsed and matched the
approved drafts exactly; unchanged patch SHA256, reverse-patch and whitespace
checks passed.

No real environment, live database/AI/MCP, migration, resync, restart or deployment
ran. Contract validation cannot prove faithful natural-language interpretation;
users must review drafts, and live model quality remains unverified. At 009c3a
frontend examples/help were unchanged; 009c3b now completes the source work below.
Rollout checks remain open; patches 010-018 retain their order.

## 009c3b: Frontend Authoring Alignment And Source Closure

Status: **approved and applied unchanged on 2026-10-15**. The final planned 009
source slice changes four frontend files: 60 insertions/61 deletions. Its complete
approved preview remains in chat only. Patch 009 source implementation and offline
verification are complete; **patch 010 is next**.

Supported samples use PR number 17 for merging and exact target branch Production
for PR creation. The compound source/target/negation example returns clarification
with no draft. Independent local samples no longer suggest each other as related
scopes. Backend conditional-field names drive modal help/placeholders; unavailable
combinations and nonempty conditions on broad-only combinations cannot be submitted.
Existing condition text is retained for explicit review/clearing. Backend
validation stays authoritative. Preview options now match all fourteen supported
write combinations and equality-field lists; unsupported read authoring choices
are removed. No payload/edit/summary refactor or new test framework was introduced.

Saved-source whole-project TypeScript and scoped Next core-web-vitals lint passed.
A temporary harness checks actual extracted functions with controlled callbacks:
supported/unsupported/output samples, six exact-selector submit/edit round trips,
and unavailable/broad-only submission gates. It does not mount React or test
browser events. The unchanged summary display was reviewed for verbatim stored
text. Saved samples/mocks also pass actual backend storage/execution checks,
including case-sensitive branch and numeric PR behavior. Existing assistant,
policy-options and input-storage HTTP diagnostics passed with disposable SQLite,
real JWT and fake provider boundaries. All four saved files match approved drafts
exactly; unchanged patch SHA256, reverse-patch and whitespace checks passed.

Browser inventory is empty; interaction and visual layout remain unverified.
Actual PostgreSQL/concurrency, binary/catalogue compatibility, live model quality,
browser and reviewed legacy repair/resync remain explicit rollout checks. No real
environment, live database/model/MCP, package installation, migration, resync,
server restart or deployment ran. No additional 009 source slice is planned;
continue with 010-018 in order.

## 010-018: Autonomous Security Foundation And Review Closure - 2026-10-16

Implemented under explicit user authorization to continue without previews.
Changes cover the framework/runtime refresh, bounded management throttling,
expiring setup credentials and restricted sessions, request/history bounds,
explicit-target membership backfills, a smaller patched dependency closure,
verified dead/generated-file removal and a safe combined regression entry point.
See the [completion report](security-run-2026-10-16.md) for per-patch results,
current versions, checks, the prerequisite schema rollout and remaining upstream
findings. Existing work was preserved; no live data/policies or deployments changed.
Local dependency/image builds and isolated tests ran. The historical ?no image
build/package update? descriptions above apply to their earlier patches.

## Verification And Deployment Boundaries

For patches 001-009, no real `.env` values were edited, no live
PostgreSQL diagnostic or model/MCP request ran, and no migration, service
restart, image publish, or deployment was performed. See
[testing notes](testing-notes.md) for detailed checks and
[the backlog](open-work-backlog.md) for remaining work.
009b's review read public GitHub source files and pinned-image metadata only.
