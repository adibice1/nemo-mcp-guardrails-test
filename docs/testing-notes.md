# Testing Notes

## NVIDIA Supported-Provider Guide - 2026-10-20

Added supported-llm-setup-guide.md against the user-linked NVIDIA Latest page
and primary vendor references. Coverage checks found all 17 concrete inference
engine names, the generic community entry and all 9 named compatible examples;
specialist rail models and all 8 embedding entries are addressed separately.
The guide distinguishes NeMo library support from this project's pinned 0.21.0
factory/schema, and marks in-process/native protocols and IAM refresh limits.

20 representative compatible profile bundles and both Azure aliases passed the
actual Pydantic schemas and endpoint/credential-name validators. Eight incorrect
NeMo-engine-as-GMS-provider values were rejected, and main-only update semantics
were verified. External sockets were denied, dotenv disabled and no secrets
resolved. All 22 PowerShell blocks parsed without execution (zero syntax errors),
and all 25 table navigation links resolved to explicit anchors. Linux serving
commands were checked against operator documentation, not executed or hardware
tested. No dependency, code, .env, database, model download, gateway or provider
call changed/ran for this documentation task. Live provider/model capabilities
and the existing release verification work remain outstanding.

## Claude/Ollama Walkthrough Validation - 2026-10-20

Added model-switch-walkthroughs.md with direct compatible Claude and local Ollama
steps, separate database-free probes and DB-backed profile/grant/runtime steps.
Checked current UI labels, credential-name handling, app-key Runtime Test fields
and main-only selection semantics. Both example profile bundles passed the
actual request schema and endpoint/reference validators with fake settings,
dotenv disabled and external sockets denied. Seven PowerShell snippets parsed
without execution and had zero syntax errors. This does not establish successful
live Claude/Ollama GMS behavior. No .env, code, database, gateway or provider
request changed/ran for this documentation task.

## Provider-Neutral Gateway Applied - 2026-10-20

The approved source integration adds a dedicated test_model_gateway check, increasing
the explicit offline catalogue to 33. It covers real standard SDK transports,
JWT/RBAC profile creation and purpose grants, revocation/cache changes, agent/tool
round trips, actual NeMo yes/no rails and invalid/truncated classifications,
redirect refusal and independent policy authoring. External sockets and dotenv
are disabled, and database fixtures are disposable SQLite.

After exact-diff approval, all patch/baseline fingerprints were checked and the
patch was applied without source conflicts. A fresh complete run on the applied
source passed 33/33 checks (0 failures), including the corrected connector fixture.
Whole-project TypeScript, changed-file lint using the available older ESLint 8 /
Next 13 toolchain, Python syntax (12 changed/new Python files) and whitespace
checks passed. Source ESLint 9, clean pinned dependencies/image builds, browser
interaction, PostgreSQL, real gateway/provider calls and latency/accuracy remain
unverified. These are home-environment results, not upstream model certification.
No .env, database, gateway or deployment configuration was changed. See the
[integration guide](model-gateway-integration.md) for the remaining live workflow.


## Model Handover Guide Audit - 2026-10-20

The initial objective was to confirm the model-switching handover instructions,
before the later provider-neutral integration request above. docs/llm-provider-guide.md was rewritten against current
source. It now distinguishes supported Azure switching, main/guardrail purpose
grants, the independent authoring model and unimplemented provider adapters.
It removes obsolete selector references and documents the always-required Azure
defaults, shared API version, fixed temperature and API-only provisioning path.

All six JSON request examples validated against actual Pydantic schemas; 15
method/path definitions matched source routers, and five CLI test names matched
the explicit offline catalogue. Example endpoint/credential approvals passed
and provider=ollama rejected. Dotenv/external sockets were disabled. This is
schema/source contract verification, not execution of a live switching sequence.
No application code, .env, database or provider configuration changed.

The user reported four model/security offline checks passing and a successful
qwen3:4b download/local response. ollama ps showed model ID 359d7dd4bcda,
3.2 GB, 100% CPU and context 4096. The exact READY probe failed to follow the
requested format; response termination/thinking metadata was not supplied, so
its cause remains undiagnosed. No reasoning content is copied into these notes.
The result proves local inference, not GMS/NeMo or tool-calling integration.
Actual alternate-Azure switching, model-quality evaluation and other-provider
adapters remain unverified/unimplemented respectively. The Next.js patch remains
parked and unapplied.

## Home Offline Checkpoint - 2026-10-20

The Azure connection is currently blocked by a port-5432 TCP timeout. The home
checkout was clean before verification. The following checks ran without local
or hosted PostgreSQL, real Azure model calls, or GitHub MCP execution:

- The explicit credential-isolated security runner passed all 32 checks. Its
  database fixtures are disposable SQLite, with dotenv disabled and external
  sockets blocked.
- The branch-editor handler/English-formatting check passed.
- Whole-project TypeScript passed with no emit and incremental output disabled.
- pip check reported no broken installed requirements.
- Full lint could not start: installed ESLint 8.57.1 lacks the config export
  required by the current flat configuration. The source requires ESLint 9.39.5.

These are home-environment results, not verification against the committed
security dependency baseline. Installed frontend packages are still Next 13.5.11
and React 18.2.0, whereas the source/lockfile target Next 16.4.2 and React 19.3.1.
Nineteen unique Python packages differ from requirements.txt/constraints.txt,
including PyJWT, Starlette, LangChain core/graph, MCP and cryptography. A passing
pip check does not establish equality with those pins. Home Node is 22.15.0;
the manifest permits it, but the recorded release baseline uses Node 24.

Next: align the local runtime/dependencies using the existing pinned requirements
and npm lockfile, then repeat the security runner, branch-editor, TypeScript and
full-lint checks. No dependency installation or .env/source edit was performed
in this verification. The /policy-preview route explicitly uses mock options
and disables live AI, so its browser/layout checks can follow without a backend.
Record draft application/cancel, branch controls/English text, merge limitation
notice, mobile layout and dark mode; saving there is in-memory only. Real policy
209 edit/cancel, actual grants, hosted-database behavior and real GitHub branch
routing remain the separate rehearsal checks in the handoff/backlog.

## Branch Routing - Patch 019

The safe runner now has 32 checks, including test_branch_routing. Windows/Linux
checks cover real guarded-tool invocation, canonical branch storage/reuse,
assignment-safe edits, scoped snapshots and exact cache invalidation. Run
`node scripts/check_branch_editor.cjs` for actual rendered control handlers.
Selective conditional merges are deliberately refused; passing tests do not
certify allowed merge execution. The separate guarded
`scripts/check_branch_conversion_postgres.py` fixture test passed on disposable
PostgreSQL 18.6, including partial-write rollback and stale-assignment manifests.
See [019 results](branch-routing-patch-019.md) for bounds and rollout instructions.

## Final Security Regression Entry Point - 2026-10-16

`python scripts/run_security_checks.py` explicitly runs 31 offline/disposable
checks with inherited credentials removed, dotenv disabled, SQLite selected and
external sockets blocked. Windows internal asyncio socket pairs are permitted.
`--list` identifies excluded external/database diagnostics; no unrestricted test
discovery occurs. New `test_security_controls.py` covers rate-limit recovery and
capacity, setup sessions/expiry/reset/revocation, malformed-password safety,
raw/schema/history bounds, indexed tail reads, targeted membership preview and
idempotent schema additions. See the [completion report](security-run-2026-10-16.md)
for final cross-platform/image/advisory results and limits.

`npm --prefix frontend run lint` checks the full frontend. Production container
verification uses `scripts/check_frontend_container.cjs` mounted read-only in the
frontend image, with `--network none`; it starts only an internal fake upstream.
No real model, GitHub MCP or hosted PostgreSQL tests were run. Existing direct
manual diagnostics retain their documented opt-in requirements.

The separate guarded `scripts/check_backend_container.py` passed against an
empty disposable PostgreSQL 16 container and the real backend HTTP listener.
It verified the setup-password lifecycle, session revocation, committed-reset
versus stale-update handling and idempotent legacy schema migration. Test data
was synthetic, ports were private and the containers/network were removed.

Sections below are dated historical records; their earlier "next patch" and
verification limits do not override the current completion report.

## Frontend Authoring Checks (009c3b) - 2026-10-15

The approved four-file frontend diff is applied unchanged. Whole-project
saved-source TypeScript passed with `node node_modules/typescript/bin/tsc
--noEmit --incremental false` from `frontend/`, with no generated output.
All four files passed scoped ESLint using the installed Next core-web-vitals
configuration; no repository lint configuration or dependency changes were made.

A temporary Node/TypeScript harness executes actual extracted saved functions and
existing page payload/edit helpers with controlled callbacks. It checks supported,
unsupported and output examples, cleared selection for unsupported scope, six exact
selector submit/edit round trips, and unavailable/broad-only submission gates.
It does not mount React or exercise browser events. The unchanged summary view
was reviewed to confirm it displays stored custom-resource text verbatim.
Saved-source samples and mock options also pass the actual Python storage/
execution contract: all fourteen tuples/field lists match, PR numbers compare
correctly and branch case remains significant.

Saved-source assistant HTTP, policy-options HTTP and input-storage HTTP diagnostics
passed with dotenv disabled, SQLite selected before imports, real JWT and a fake
provider. All four saved frontend files match the approved drafts exactly;
unchanged patch SHA256, reverse-patch and whitespace checks passed. No browser is connected
(the available-browser inventory is empty), so visual layout and browser interaction
remain open checks. No real environment, live DB/model/MCP, package installation,
server restart, migration, resync or deployment ran. The complete approved code
diff remains in chat only. Planned patch 009 source work and offline verification
are complete; patch 010 is next. Live compatibility,
legacy-policy repair/resync and browser checks stay in the deployment backlog.

## Assistant/Options Checks (009c3a) - 2026-10-15

The approved five-file backend diff is applied unchanged. Saved-source
`tests/test_policy_assistant_http.py` and `tests/test_policy_options_capabilities.py`
passed using `.\.venv\Scripts\python.exe -B`. Both use real JWT authentication, disposable SQLite and
fake provider responses. Coverage includes canonical literal/case/Unicode/quotes,
accepted related scopes, unsupported primary/related selectors, cleared drafts
on failure, changed related scope, output isolation, authentication/provider
errors, supported-write options, selector fields, connector ownership and all
four metadata enable flags.

Five existing diagnostics passed against saved source: input-condition
storage, runtime policy integration, GitHub tool contract, resource bindings and
literal grammar. Child processes set `PYTHON_DOTENV_DISABLED=1` and
`DATABASE_URL=sqlite://` before imports. All five saved Python files parsed and
matched approved drafts exactly; unchanged patch SHA256, reverse-patch and
whitespace checks passed. No real environment, live database/model/MCP, migration, resync, restart
or deployment ran. These checks establish executable contract validity, not
natural-language interpretation quality. The frontend remains unchanged;
009c3b now completes examples, field help, draft application and focused
edit/display checks above.
The complete approved code diff remains in chat only. No frontend code was
changed in this patch.

## Runtime Policy Integration Checks (009c2c) - 2026-10-15

The approved fourteen-file diff is applied unchanged. Saved-source
`.\.venv\Scripts\python.exe -B tests/test_runtime_policy_integration.py` passed
with real app-key authentication, in-memory SQLite, actual runtime construction,
snapshot queries, rails configuration, catalogue filtering, guarded tools,
execution coordination, HTTP serialization and conversation persistence. Only
environment/model/rails execution, MCP transport and agent construction are faked;
the fake agent calls the actual wrapped tools. Independent policy/prompt reloads
raise in this test, including for legitimate empty scope.

Coverage includes global/app isolation, literal case/field matching, malformed
and unobservable targets, matched-policy attribution, output phrase enforcement,
warm-cache changes despite unchanged versions/timestamps/aggregate revision,
stale/global/legacy failures, schema drift, TTL zero, lock-wait changes and changes
during construction. Setup failures reach neither execution nor history storage;
tool guards stop underlying invocation. Evaluation errors have a distinct source
and event reason with no false policy ID or raw argument content.
The installed LangGraph tool node, run in a compiled graph without a model,
propagates both matched-policy and evaluation failures instead of swallowing them.

Eighteen existing offline diagnostics passed against saved source: tool guard,
runtime cache, policy fail-closed, model grants, connector credential security,
GitHub contract, snapshot, input storage, inventory, bindings, grammar, literal
prompt rendering, MCP launch, connector credential resolution, output fail-closed,
debug privacy, runtime events (six unit cases), and model selection. Child processes
set `PYTHON_DOTENV_DISABLED=1` and `DATABASE_URL=sqlite://` before runtime imports. Updated independent
grant/credential/cache fixtures explicitly supply empty policy snapshots.

All fourteen saved Python files parsed and matched the approved drafts exactly;
approved-patch reverse verification, unchanged patch SHA256 and whitespace checks
passed. Full GitHub runner parsed only. No real `.env`, live database,
PostgreSQL concurrency, real binary/catalogue, model/MCP process, migration,
compiled-rule resync, restart or deployment ran. Interleavings are simulated,
and live model classification remains unverified. Runtime integration is active;
009c3 assistant/UI alignment is next. Requests already admitted may finish on
their validated snapshot after a concurrent policy change. Review/repair legacy
conditions and resync changed compiled text through the admin path before rollout.

## GitHub Tool Contract Checks (009c2b) - 2026-10-15

The approved seven-file diff is applied unchanged. Saved-source
`.\.venv\Scripts\python.exe -B tests/test_github_tool_contract.py` passed,
forbidding dotenv loading
and invoking no database/model/MCP boundary. Independent minimal schema fixtures
are based on the previously reviewed pinned upstream source. Checks cover shared
methods, authoritative fields, case/punctuation/numbers, nested paths, indirect
write routes, indeterminate-target errors, immutable rules, narrow generated
prompts, unsupported broad/conditional policies, catalogue exclusions, schema
drift and the image pin matching the Dockerfile.

Twelve existing diagnostics passed against saved source: MCP launch configuration,
runtime policy snapshots, input condition storage, condition inventory, GitHub
bindings, grammar, legacy tool wrappers, literal prompt rendering, policy
fail-closed behavior, runtime model grants, connector credentials and cache reuse.
Child processes set `PYTHON_DOTENV_DISABLED=1` and `DATABASE_URL=sqlite://`
before runtime imports;
the storage/snapshot fixtures use disposable in-memory SQLite. The full GitHub
runner was parsed only; its image pin is updated while read-only mode is retained.
The standalone compiler CLI also completed against saved source without external
services; its direct-file entry point retains source-path bootstrapping.
All seven changed/new Python files parsed and matched the approved drafts exactly;
approved-patch reverse verification and whitespace checks passed. An earlier
baseline reproduction confirmed missing indirect branch-tool
coverage and generated conditional tests lacking their literal target.

No real `.env`, live database, Docker image pull/container process, model/MCP call,
migration, restart or deployment ran. Binary provenance and real server catalogue
compatibility are not tested by fake schema fixtures. Alternate native binary
paths now reject. At 009c2b the matcher/catalogue and snapshot/cache were not
integrated; 009c2c now connects them as recorded above.
New conditional compiler text will require reviewed compiled-rule resync before
eventual rollout. See the single backlog for remaining scope and limitations.

## Policy Snapshot Checks (009c2a) - 2026-10-15

The approved two-file diff is applied unchanged. Saved-source
`.\.venv\Scripts\python.exe -B tests/test_runtime_policy_snapshot.py` passed
using disposable in-memory SQLite. Dotenv loading raises if attempted. The test
counts one SELECT despite pending ORM changes; covers enabled global/app scope,
normalized metadata precedence/consistency, disabled/unassigned exclusions,
authorized empty scope, missing/unauthorized apps, malformed/versionless selectors,
unsupported broad combinations, output fallback and invalid output values.
It rejects missing, stale, duplicate or mismatched compiled rules and catches a
literal case change while versions/timestamps remain unchanged. Detached frozen
values retain their old contents and suppress literal text in default reprs.
Database errors produce the same controlled message without raw details.

Four existing saved-source diagnostics passed: input condition storage,
inventory, GitHub bindings and grammar. Both saved Python files parsed;
approved-patch reverse verification and workspace whitespace checks passed.
PostgreSQL SELECT SQL was compiled only. No live database, actual PostgreSQL concurrency, environment load,
HTTP runtime/cache integration, model/MCP call, migration, restart or deployment
ran in 009c2a. 009c2b and 009c2c are now applied above; runtime wiring and offline
HTTP/cache checks passed. 009c3 remains next.

## Versioned Input Condition Storage (009c1) - 2026-10-15

The approved six-file diff is applied unchanged. All four saved-source commands
passed with `.\.venv\Scripts\python.exe -B`: `tests/test_input_condition_storage.py`,
`tests/test_resource_condition_inventory.py`, `tests/test_github_resource_bindings.py`
and `tests/test_resource_conditions.py`. All six changed/new Python files parsed;
approved-patch reverse verification and workspace whitespace checks passed.

The new HTTP diagnostic uses real JWT/RBAC, disposable in-memory SQLite and
dotenv disabled. It covers supported versioned storage, case/punctuation/Unicode
identity, duplicate rejection, invalid creates/updates, metadata-only legacy
refusal, explicit disabling, assignment-safe App A edits without changing App B,
global resolution and deduplication that retains legacy definitions. Inventory
recognizes canonical versioned selectors as candidates still requiring review.

The existing PostgreSQL resolution diagnostic's format expectation and cleanup
prefix were updated but not run. No real `.env`, live database inventory,
PostgreSQL check, migration, model/MCP call, restart or deployment ran. Storage
validation is implemented; the runtime guard is unchanged. 009c2 covers runtime,
cache and compiler integration; 009c3 covers assistant/UI alignment and closure.

## Resource Bindings And Compatibility Inventory (009b) - 2026-10-15

The approved four-file patch is applied unchanged. Both saved-source commands
passed: `.\.venv\Scripts\python.exe -B tests/test_github_resource_bindings.py`
and `.\.venv\Scripts\python.exe -B tests/test_resource_condition_inventory.py`.
The existing `tests/test_resource_conditions.py` diagnostic passed too. All four
new Python files parsed; approved-patch reverse verification and whitespace
checks passed.

Binding checks cover authoritative fields, unrelated look-alike values, method
discriminators, case-sensitive paths/branches, punctuation, qualified PR heads,
integral numeric arguments, malformed/missing targets, nested file paths and
unsupported state-dependent combinations. Inventory checks use disposable
in-memory SQLite with real models, normalized metadata and app/global
assignments. They prove default execution loads neither dotenv nor an engine,
pending ORM changes are not flushed, disabled/unassigned definitions remain
visible, output rows are excluded, literal values are omitted and an attempted
write through the CLI connection is refused. CLI tests substitute the engine
and dotenv loader; SQLite executes the real read-only restriction. No real
`.env` was loaded.

Earlier review read the pinned image's public version/revision labels and four
public upstream source files; no container or MCP process started. No actual
database inventory, PostgreSQL transaction verification, migration, model call,
restart or deployment ran. At 009b these helpers had no management/runtime
consumers; 009c1 now uses them for storage validation. Runtime enforcement
remains unchanged. 009c2/009c3 must cover runtime, assistant, cross-tool routes
and the local launcher's unpinned image contract. See the single backlog for
scope and remaining rollout checks.

## Literal Resource-Condition Grammar (009a) - 2026-10-15

The approved two-file patch is applied. Saved-source
`.\.venv\Scripts\python.exe -B tests/test_resource_conditions.py` passed 22 supported
selectors and 32 rejection cases without database, environment loading or
external services. Checks cover explicit and legacy literal syntax, resource
field restrictions, positive issue/PR numbers, escaped/Unicode titles, retained
path case and punctuation, compound comparisons/workflows, trailing input,
malformed values, control characters, invalid Unicode surrogates and the input
length boundary. Both saved Python files parsed. Reverse-patch verification
matched the approved diff and whitespace checks passed.

At 009a the parser had no management/runtime consumers. These checks establish the
grammar foundation, not enforcement of saved policies or MCP argument binding.
009b adds the binding/inventory helpers above; 009c1 adds management validation.
Live compatibility inventory remains open, along with runtime/assistant
integration and their regressions in 009c2/009c3.
No real `.env`, database, migration, Azure/GitHub request, restart or deployment
was used. See `open-work-backlog.md` for the remaining ordered plan.

## Runtime LLM Grants And Cache Revocation (008c) - 2026-10-15

The approved 12-file patch is applied. Saved-source
`.\.venv\Scripts\python.exe -B tests/test_runtime_llm_grants.py` passed with real
app-key/JWT authentication, disposable SQLite and fake external boundaries.
The test exercises the real public runtime builder and shared live grant loader,
while model/tool construction and execution use substitutes. It covers both
purposes, named/default choices, app isolation, warm-cache revocation with an
unchanged aggregate revision, model metadata changes, unreadable grants,
malformed credential approval, cache-disabled requests, lock-wait revocation,
and model changes during construction. Denied HTTP requests reach neither
execution nor conversation storage.

A missing default credential also exercises the real uncached coordinator with
policy/connector metadata substituted, proving model/MCP construction is skipped
and setup returns 503. Direct model construction tests reject legacy JWT-secret
references without reading that variable, reject missing approved named keys,
and pass only the approved fake key to the model constructor. Real Azure/GitHub
requests and live model quality are outside this diagnostic.

Eight related saved-source diagnostics passed: `test_runtime_cache.py`,
`test_policy_fail_closed.py`, `test_connector_credential_security.py`,
`test_llm_endpoint_security.py`, `test_runtime_llm_selection.py`,
`test_app_llm_grants_http.py`, `test_runtime_connector_credentials.py`, and
`test_runtime_mcp_launch.py`. The model-selection, connector-credentials and
MCP-launch diagnostics import runtime code before their fixtures, so they were
run in child wrappers with dotenv loading disabled and `DATABASE_URL=sqlite://`;
no real `.env` was read.

Full saved-source frontend TypeScript passed with incremental output disabled;
scoped ESLint passed for the API client and model settings component. All ten
changed/new Python files parsed. Reverse-patch verification matched the approved
diff and whitespace checks passed. The selector remains unmounted, so browser
verification was not performed. PostgreSQL constraints/locking/concurrency and
live deployment remain unverified. No live database, migration, environment
edit, service restart or deployment ran. Before rollout, review existing named
and default selections and approve grants for both purposes. Requests already
admitted can finish after concurrent revocation; credential/environment changes
still require restart.

## App LLM Grant Management (008b) - 2026-10-15

The approved 13-file patch is applied. The saved-source command
`.\.venv\Scripts\python.exe -B tests/test_app_llm_grants_http.py` passed using
real JWT/RBAC, disposable SQLite and fake metadata with dotenv loading disabled.
It verifies both app-ID/client-ID routes, app/purpose isolation even for a user
linked to both apps, refusal of query aliases that target another app, explicit
null/unchanged/unknown selections, admin-only grants and guardrail selections,
new-app provisioning, independent default grants, and rejection before any
partial app edit. Grant deletion retains a disabled row; bootstrap replay cannot
restore it, while explicit admin PUT can re-enable it.

The diagnostic also checks legacy invalid grant choices, backend-approved
credential names without secret resolution, malformed approval settings, safe
errors, generic grant-store 503s, and audit actor/outcome metadata without
credential references or request bodies. Global catalogue reads require admin;
developers use per-app options. Runtime calls are outside this diagnostic.

Five related saved-source diagnostics passed: `test_llm_endpoint_security.py`,
`test_app_llm_grant_migration.py`, `test_management_audit_http.py`,
`test_app_authorization_http.py` (24 protected-field cases), and
`test_connector_credential_security.py` (60 protected-field cases). AST parsing
passed for all 12 changed/new Python files. Reverse-patch verification confirmed
the saved code matches the approved diff, and whitespace checks passed.

`test_llm_config_api.py` and `test_management_rbac_http.py` have updated live-
PostgreSQL fixtures/expectations but were not run. PostgreSQL DDL compiled in
008a's diagnostic; actual constraints, row locks and concurrent transactions
remain unverified. No frontend files changed. No real `.env`, live database,
Azure/GitHub call, live migration, restart or deployment ran. Legacy runtime
credential validation, cold/warm grant enforcement and selector adaptation were
added by 008c above; 008b alone did not enforce the runtime boundary.

## App LLM Grant Foundation (008a) - 2026-10-15

The approved three-file patch is applied. The saved-source command
`.\.venv\Scripts\python.exe -B tests/test_app_llm_grant_migration.py` passed using
disposable SQLite and fake metadata with dotenv loading disabled. It verifies
that ordinary previews issue no DDL/data writes, schema creation touches only
the grant table, grants default to disabled, named/default grants have separate
uniqueness constraints, purpose checks and foreign-key cascades hold, and
inventory reads only non-secret environment metadata.

Manifest checks cover strict field types, unknown/duplicate entries, stale app,
configuration and default-deployment metadata, disabled configurations, complete
validation before insert, transaction rollback after an actual insert, repeated
application, and preservation of existing disabled grants. Errors do not echo
invalid manifest contents. Existing app selections/authorization remain intact.

Saved-source `test_app_authorization_http.py` and
`test_connector_credential_security.py` also passed, including their 24 and 60
protected-field cases. AST parsing passed for the three changed/new Python
files. Reverse-patch verification confirmed the saved code matches the approved
preview, and whitespace checks passed. No frontend code changed.

PostgreSQL DDL compiled only; PostgreSQL constraints, row locking and concurrent
transactions remain unverified. No real `.env`, live database, Azure/GitHub call,
live migration, service restart or deployment ran. Only in-memory SQLite fixture
schema/data changed. 008a adds storage/tooling; it does not enforce app grants
in management selection or runtime execution. See 008b/008c in the backlog.

## Connector Credential Provisioning - 2026-10-15

Approved patch 007 is applied. The old resolver's ability to resolve the management
JWT secret as a GitHub credential was reproduced with fake values before the fix.
The saved-source `tests/test_connector_credential_security.py` passed 60 protected-
field cases plus new-link and default provisioning, admin null/blank clearing,
omitted-field upsert preservation, developer toggle/unlink, delete/relink denial,
app scope, malformed backend approval, and legacy/runtime failure checks.

The diagnostic uses disposable SQLite, real JWT/RBAC and app authentication,
and fake environment values. Runtime checks exercise the real credential path
through `/run` with policy loaders replaced; unapproved or missing default/named
credentials stop before model/MCP construction and agent execution. A direct
lookup spy verifies a rejected JWT reference never reads that secret variable.
No external Azure/GitHub calls occur. This does not verify PostgreSQL-specific
behavior, concurrent transactions, or historical ownership of legacy references.

Six related saved-source diagnostics passed: runtime credential resolution,
Docker/native launch configuration, app authorization, policy loading, LLM endpoint
security, and management audit. The first two ran with dotenv disabled and a
SQLite URL supplied in their child processes. The live-Postgres connector API
diagnostic's vault-reference rejection/count expectations were updated but it
was not run. Python AST checks passed for all seven changed/new Python files.

Full frontend TypeScript passed with no emit or incremental build output. Scoped
ESLint passed for the connector component and API client. Browser verification
was not performed. Diff checks and comparison with the approved patch passed.
No real `.env` edit, live database test, migration, service restart, image publish,
or deployment ran. Custom GitHub variable names now require
`GMS_ALLOWED_GITHUB_CREDENTIAL_ENV_VARS`; environment approval changes require a
backend restart because constructed clients are cached.

## Administrator-Controlled App Authorization - 2026-10-15

Approved patch 006 is applied. `tests/test_app_authorization_http.py` reproduced
the old developer reauthorization bypass before application and passed against
saved source. It uses real management JWT authentication, real RBAC and app-key
authentication queries, and disposable SQLite users, apps, and app links.

The 24 protected-field requests cover app admin/owner links, enabled/disabled
apps, true/false/null values, and mixed updates containing an invalid model ID.
Rejected updates leave stored name, client ID, authorization, model IDs, key hash,
and timestamp unchanged. Other cases check missing/unlinked management access,
the existing guardrail-model restriction, admin enable/disable without membership,
ordinary developer edits, unsupported metadata PUT by client ID, and runtime
authentication after revocation and client-ID rename. Disabled `/run` requests
are rejected before a mocked runtime builder runs.

Saved-source password-change, management-audit, and policy-loading diagnostics
also passed. Python AST and diff checks passed. No frontend code changed, so no
new frontend build or visual verification was needed. This does not verify
PostgreSQL concurrency or cancellation of already-authenticated requests.
No real `.env` edits, live database tests, Azure/GitHub calls, migrations, service
restarts, image publication, or deployments ran.

## Fail-Closed Database Policy Loading - 2026-10-15

The approved patch is applied. The old silent fallback was reproduced before
application, then `tests/test_policy_fail_closed.py` passed against saved source.
It uses disposable SQLite tables and mocked external boundaries to check global
and app scope, disabled assignments, stale compiled rows, loader failures,
legitimate empty results, malformed rows, explicit offline defaults, import
behavior, policy checks before model/MCP construction, cache failure/recovery,
and generic HTTP 503 responses without internal error markers.

The SQLite schema is copied from metadata with JSONB adapted locally to JSON;
this exercises ORM selection/scope but does not prove PostgreSQL-specific DDL,
JSONB behavior, or transaction concurrency. Runtime authentication is replaced
in the HTTP fixture; setup errors are injected without external calls.

Seven existing saved-source diagnostics passed: tool guard, runtime cache, model
selection, debug privacy (six HTTP cases), literal prompt rendering (24 prompts),
LLM endpoint security, and output classification (12 HTTP/history/log cases).
The tool-guard/cache/model-selection checks ran in child processes with dotenv
disabled, a SQLite URL, and fake credentials. Tool-guard fixtures explicitly used
default policy mode; cache/model-selection checks used database mode with their
existing mocked or construction-only boundaries. Python AST and diff checks passed.

No live PostgreSQL diagnostic, Azure/GitHub request, migration, service restart,
image publication, or deployment ran. Unavailable/malformed policies now stop
runtime setup; deployment must use database policies for authenticated runtime
construction. Defaults remain an explicit offline diagnostic option. The 503
mapping covers runtime setup, not authentication/history failures or startup
database checks. Transaction-wide policy snapshots and detection of missing
active compiled rows remain separate work.

## Fail-Closed Output Classification - 2026-10-15

Azure refusal of an output self-check no longer falls back to allowing text
that passes a short secret-pattern scan. Recognized NeMo-wrapped Azure errors,
raw Azure content-filter errors, and LangChain's filtered-completion ValueError
all produce a controlled blocked result. Unrelated errors still propagate.
Normal NeMo passed, blocked, and modified outcomes retain their existing behavior.

The regression failed against the previous implementation and passed against
the approved saved-source patch. It covers 12 HTTP cases across
debug enabled/disabled, two response types with/without obvious secret patterns,
and three provider-error representations. Each checks the real execution path,
response serialization, disposable SQLite conversation history, and metadata
and user-log values captured at the persistence boundary. Auth and runtime
construction are replaced with isolated fixtures; no real connector or LLM runs.

Additional controls verify normal classifications and unrelated provider errors.
The older `test_app_auth_http.py` expectation is updated from a fallback pass
to a block; that live-Postgres diagnostic was not run in this review.

```powershell
.\.venv\Scripts\python.exe -B tests/test_output_classifier_fail_closed.py
.\.venv\Scripts\python.exe -B tests/test_runtime_debug_privacy.py
.\.venv\Scripts\python.exe -B tests/test_prompt_rule_literals.py
.\.venv\Scripts\python.exe -B tests/test_llm_endpoint_security.py
```

All four saved-source diagnostics passed. Python AST parsing and diff checks
also passed. These checks used no external services; no service restart,
migration, or deployment was performed.

No database migration or new environment setting is required. Harmless responses
can now be blocked if Azure refuses classification; this deliberately withholds
output that did not complete the active policy check. Database policy-loader
fallbacks require a separate patch.

## LLM Credential Destination Security - 2026-10-15

The approved saved-source patch passed the new offline security diagnostic:

```powershell
.\.venv\Scripts\python.exe -B tests/test_llm_endpoint_security.py
.\.venv\Scripts\python.exe -B tests/test_runtime_debug_privacy.py
.\.venv\Scripts\python.exe -B tests/test_prompt_rule_literals.py
```

The new diagnostic uses real management JWT checks against disposable SQLite
users/configurations. It checks administrator creation, developer rejection,
authenticated catalogue access, endpoint normalization, 12 invalid endpoint
forms, rejection of legacy runtime endpoints before selected credential
resolution, malformed backend approval settings, and controlled runtime 503
responses without internal-marker disclosure. Actual SDK synchronous and
asynchronous calls use HTTP mock transports to verify redirects are refused
and fake API keys stay at the approved origin. No external requests occur.

`test_runtime_llm_selection.py` also passed with dotenv disabled, a disposable
SQLite URL, default policy fixtures, and a fake Azure key supplied in the child
process environment. The earlier privacy suite passed six HTTP cases and the
literal rendering suite passed 24 classifier prompts. Full frontend TypeScript
passed using `node node_modules/typescript/bin/tsc --noEmit --incremental false`.
Python AST parsing and `git diff --check` passed.

No live PostgreSQL tests, Azure/GitHub calls, migrations, service restarts, or
deployment ran. The orphan LLM settings component was typechecked, not mounted
or browser-tested. Additional deployed origins need `GMS_ALLOWED_LLM_ENDPOINTS`
and a backend restart; existing unapproved stored endpoints now fail closed.
App-specific model/credential grants remain outside this patch.

## Literal Policy Prompt Rendering - 2026-10-14

The approved compiler patch keeps database rule text literal during NeMo Jinja
rendering. YAML is parsed first, and both policy placeholders are replaced in
one pass with encoded string values. Policy text cannot assign to the actual
user-input or assistant-response variables or recursively expand placeholders.

The saved regression test passed 24 prompt-rendering cases using the installed
NeMo `LLMTaskManager` and fake loaded policy rows. Cases cover both rails,
global-rule preservation, variable-assignment directives, expressions,
comments, raw-block delimiters, malformed syntax, placeholder references,
quotes, backslashes, newlines, Unicode, YAML-like text, and empty rule sets.
The previous compiler failed this check before the patch was applied.

```powershell
.\.venv\Scripts\python.exe -B tests/test_prompt_rule_literals.py
.\.venv\Scripts\python.exe -B tests/test_runtime_debug_privacy.py
```

These checks use no external database, LLM call, or GitHub tool. The patch
protects template rendering; it does not establish resistance to natural-language
prompt injection. No policy data migration is required.

## Assistant UI, Password Copy And Self-Service Change - 2026-10-09

Approved changes were applied after their exact diffs were reviewed. The
actual source passed the following checks:

```powershell
.\.venv\Scripts\python.exe tests/test_management_password_change.py
.\.venv\Scripts\python.exe tests/test_policy_assistant_http.py
.\.venv\Scripts\python.exe tests/test_management_audit_http.py
.\.venv\Scripts\python.exe -m py_compile src/nemo_mcp_guardrails/api/management_auth_schemas.py src/nemo_mcp_guardrails/api/management_auth.py src/nemo_mcp_guardrails/management_auth.py src/nemo_mcp_guardrails/management_audit.py tests/test_management_password_change.py
cd frontend
node node_modules/typescript/bin/tsc --noEmit --incremental false
```

Scoped ESLint also passed with zero errors/warnings using the installed ESLint
Node API and `next/core-web-vitals`. The six checked files were the assistant,
User Management page, Settings form, new password-change form, API client, and
Login page. `git diff --check` passed.

The new isolated SQLite diagnostic checks admin/developer password changes,
missing authentication, incorrect current passwords, unchanged/whitespace/
short/oversized/non-string replacements, rejection of target-user fields,
hashed storage, legacy-token rejection, old-password/login-session rejection,
unaffected other-user sessions, admin-reset invalidation, and metadata-only
success/rejection audit capture. It does not contact Postgres, Azure or GitHub.

Before application, temporary in-memory UI checks passed modern Clipboard API
copying, missing/denied API fallbacks, total copy failure feedback and temporary
field cleanup. Assistant checks passed immediate example loading without AI,
edited descriptions using AI, the output sample, and no live requests in the
offline preview. These are simulated handler checks, not a real browser proof.
The browser tool failed to connect in this session, so visual verification of
the new controls is still outstanding. No real user password was changed, no
online DB connection was configured, and no image/deployment was published.

Local service smoke verification after applying the changes: Docker Desktop
was stopped, so its existing PostgreSQL container was restored first. The API's
initial startup attempt timed out while the DB was unavailable; restarting it
after the container was healthy succeeded. `/health`, `/health/db`, and frontend
`/settings` and `/policy-preview` returned 200. The live OpenAPI document includes
`PUT /management-auth/me/password`. The safe target/connectivity snippet in
`home-online-database.md` passed against the local work DB and printed only
host/port/database plus a success flag. These probes do not verify a signed-in
browser password change or an online DB connection.

## Output AI Drafting Verification - 2026-10-09

Before application, the proposed input/output sources passed the isolated HTTP
diagnostic, full frontend TypeScript check and scoped ESLint using in-memory
source overrides. The existing `tests/test_output_guard.py` also passed.
Live Azure generation returned a quoted hello restriction with no related
output bans; a GitHub regression call preserved the non-staging-to-production
merge condition and related PR-creation suggestion. No policy/assignment was
saved and no connector tool or runtime rail was executed.

The expanded `tests/test_policy_assistant_http.py` checks output JWT protection,
invalid request rails, tagged input/output responses, cross-rail/unknown-field
rejection, no GitHub metadata dependency, empty output-related lists, and
compatibility with the existing quoted-word matcher. `Hello!` blocks while
`Good morning.` and `shelloworld` do not. These are authoring/helper checks, not
an end-to-end NeMo runtime proof.

Post-application checks passed against the actual source files:

```powershell
.\.venv\Scripts\python.exe tests\test_policy_assistant_http.py
.\.venv\Scripts\python.exe tests\test_output_guard.py
.\.venv\Scripts\python.exe -m py_compile src\nemo_mcp_guardrails\api\policy_assistant.py tests\test_policy_assistant_http.py
cd frontend
node node_modules/typescript/bin/tsc --noEmit --incremental false
```

Scoped ESLint also passed with zero errors/warnings using the existing
`next/core-web-vitals` configuration via its Node API. On this Windows host,
`npx.ps1` is blocked by execution policy; invoking the installed Node entry
point avoids changing that policy.

A temporary isolated hidden Edge session verified real login, live output
generation, the two-step flowchart and output-rail label, response examples,
explicit Output Rule/name fill and focus, and unchanged policy/assignment counts.
Live GitHub input generation and form fill passed too. A simulated provider
error displayed without sample fallback; changing rails discarded a delayed
response. The standalone output sample and mock Create remained offline even
with a valid session. No browser runtime errors were recorded. Screenshots
were inspected, and layouts passed at 320/390/1440 pixels and in dark mode.
The initial temporary harness expected an outdated mock-result label; its
assertion was corrected to the existing page label and the full check passed.

The backend was restarted on port 8000 to load the changes; the existing port
3000 frontend was retained. No policy/assignment was created in the real DB,
no GitHub tool or NeMo runtime ran, and no production build/deployment was made.
These temporary browser checks are not permanent regression tests.

## Live AI Policy Authoring Verification - 2026-10-09

The proposed integration passed full frontend TypeScript, scoped Next.js
ESLint, Python compilation and the isolated HTTP diagnostic in memory before
application. Two live Azure calls using local enabled metadata returned valid
merge drafts with `target=production AND source!=staging`. The final prompt
also returned the related PR-creation draft with the same condition.
No policy/assignment was created and no GitHub tool or runtime rail ran.

The permanent isolated check uses SQLite, real management JWTs and fake Azure:

```powershell
.\.venv\Scripts\python.exe tests\test_policy_assistant_http.py
```

It covers missing/invalid authentication, request bounds and scope rejection,
valid responses/no-store, invalid primary/related combinations, clarification,
truncation/refusal, timeout, missing model settings and empty metadata.
It does not contact the real database, Azure or GitHub.

Post-application checks passed against the actual files:

```powershell
.\.venv\Scripts\python.exe tests\test_policy_assistant_http.py
.\.venv\Scripts\python.exe -m py_compile src\nemo_mcp_guardrails\api\policy_assistant.py src\nemo_mcp_guardrails\api\main.py tests\test_policy_assistant_http.py
```

From `frontend/`, `node node_modules/typescript/bin/tsc --noEmit --incremental
false` passed. Scoped Next.js ESLint passed via the installed ESLint API with
`next/core-web-vitals` for the four frontend files. `git diff --check` passed.

Temporary headless Edge/CDP checks verified real management login and a live
HTTP-200 Azure-backed suggestion through the normal port-3000 Policies UI.
The flowchart/draft preserved production as target and non-staging as source.
Primary and related drafts filled the editable form only on explicit selection;
policy and global-assignment counts remained unchanged throughout the checks.

Additional synthetic-response browser checks verified controlled API errors,
dynamic Issue/action rendering instead of a hardcoded PR diagram, and ignoring
a late result after the prompt was edited. `/policy-preview` stayed sample-only
despite an authenticated session. No browser runtime errors were observed.
Viewport checks passed at 320, 390 and 1440 pixels; desktop and mobile dark-mode
screenshots were visually inspected. These browser scripts were temporary and
are not committed regression tests.

The local backend was restarted to load the new router; the earlier port-3100
verification server was stopped so the port-3000 dev server owns the shared
`.next` output. No hosted database, policy CRUD write, GitHub tool, NeMo runtime
evaluation, production image build or deployment was exercised for this slice.

## Local Administrator Provisioning Verification - 2026-10-09

- Confirmed the home database was local PostgreSQL on host port 5433, the
  existing user schema was compatible, and the selected email/username were
  unused before inserting one enabled admin with a generated password.
- Verified the persisted password with `management_auth.verify_password()`.
- Verified real `POST /management-auth/login` and authenticated
  `GET /management-auth/me` returned HTTP 200 and the expected user/admin role.
  JWTs and plaintext passwords were excluded from verification output.
- The normal frontend `/login` on port 3000 returned HTTP 200; its login CORS
  preflight returned 200 with the matching allowed origin. Port 3100 serves the
  independent policy preview but its normal login preflight is rejected by
  the current backend configuration.
- A missing JWT signing secret was generated in the ignored local `.env`.
  No authentication source code, hosted database, or existing user was changed.
  See `troubleshooting.md` for the local bootstrap procedure. No credentials
  are included in these notes.

## Policy Authoring UI Prototype - 2026-10-09

Before application, the three proposed TypeScript files passed a full frontend
TypeScript check and scoped Next.js ESLint using in-memory sources. No
database, Azure, or GitHub calls were made for those checks.

Local manual verification path:

```powershell
cd frontend
npm run dev
```

Open `http://127.0.0.1:3000/policy-preview`. This standalone page works without
a management login or backend connection. Choose the merge example, preview
it, inspect the condition and illustrative outcomes, and use the draft to
fill the existing form. Edit the fields and Create to display a mock draft.
Preview the related PR-creation policy separately. Check unsupported prompts,
close/reopen reset, output/manual form behaviour, narrow layouts and dark mode.
Refresh must clear the mock-created draft. No live AI generation or runtime
policy evaluation is part of this prototype.

Post-application verification passed on 2026-10-09:

- `node node_modules/typescript/bin/tsc --noEmit --incremental false`, run
  from `frontend/`, passed against the actual files.
- Scoped Next.js ESLint passed via an inline Node script using the installed
  ESLint API and `next/core-web-vitals` for the three changed/new code files.
- The local Next.js dev server used
  `node node_modules/next/dist/bin/next dev --hostname 127.0.0.1 --port 3100`.
  `GET http://127.0.0.1:3100/policy-preview` returned HTTP 200.
- Temporary headless Edge checks using an inline Node/CDP script passed sample
  interpretation, unsupported-prompt handling, independent related previews,
  metadata/draft application, policy-name focus, editable name/condition,
  mock creation, form reset, manual output-policy creation, and refresh reset.
- Layout checks passed at widths 320, 390, and 1440 pixels with no horizontal
  overflow and a viewport-bounded scrollable modal. Dark theme styling passed;
  desktop and 390-pixel dark screenshots were visually inspected.
- No browser runtime errors or backend/external HTTP requests were observed.
  The route stayed isolated even with an existing frontend `.env.local`.
- `git diff --check` passed. These temporary browser checks were not added as
  permanent regression tests. No production build, database, live AI, NeMo
  classifier, GitHub tool, or deployment verification was run for this slice.

## Logging And Retention Handoff - 2026-09-11

Run from the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe tests\test_runtime_events.py
.\.venv\Scripts\python.exe tests\test_runtime_logs_http.py
.\.venv\Scripts\python.exe -m py_compile scripts\cleanup_runtime_logs.py tests\test_runtime_logs_http.py
```

These checks passed in the preceding implementation turn. The event suite
contains six checks. The HTTP test uses isolated SQLite and real management
JWTs, and now also checks retention dry-run, cutoff preservation, unfinished
requests, event deletion, and repeat invocation. An additional temporary inline
test, not a committed test file, checked 501 requests with SQLite foreign keys
enabled: the 500-row batch cap, request/event rollback, and subsequent batches.

The cleanup command uses the real database selected by `.env`/`DATABASE_URL`:

```powershell
.\.venv\Scripts\python.exe scripts\cleanup_runtime_logs.py --days 30
```

Without `--apply` this is read-only and reports at most one batch of 500.
With `--apply` it permanently deletes that batch and associated events in one
transaction. It uses completion time, retains null/exact-cutoff values, and
accepts 1-3650 days. Do not run apply on production or shorten retention merely
to produce a deletion during testing. Use a dedicated test database/fixtures.
No real cleanup has been performed by the agent; PostgreSQL behavior and Azure
scheduling remain unverified. Thirty days is a default, not an approved
organisation-wide retention requirement.

Frontend synthetic-response checks passed for Logs workflows; the mobile filter
fix additionally passed layout checks at 320/390/1440 pixels. These browser
checks are not committed regression tests. The user reported their local tests
looked fine, but detailed PostgreSQL verification evidence was not supplied.

The password lifecycle is still a pending schema-only preview. Do not try to
run `tests/test_password_lifecycle_schema.py` yet: it has not been created.

## Target Runtime Note

The current scripts test one GitHub prototype path. The confirmed production
GMS will be a full proxy that authenticates a client app, loads mandatory
global rules plus app-specific assignments, runs input rails, executes guarded
connector tools, runs output rails, and returns the final response.

In target terminology, GitHub MCP is a connector rather than a client app.

## Test Folder Layout

Runnable verification checks now live under `tests/`. The `scripts/` directory
is reserved for API startup helpers, migrations, seeders, and debug utilities.
Use `python tests/test_*.py` paths when running backend checks.

## Current Status

NeMo input rails are working in the full GitHub MCP test path when `LLMRails`
is created with an injected AzureChatOpenAI model:

```python
prompt_rule_config = build_rails_config_with_prompt_rules("config")
rails_config = prompt_rule_config.rails_config
rails = LLMRails(rails_config, llm=model)
```

The deterministic Python pre-check still exists, but by default it only reports what it would block. It does not stop execution unless `ENFORCE_PYTHON_PRECHECK=true`.

The additive target-foundation and connector terminology migrations have been
verified without changing the existing runtime behavior.

`POST /v1/guardrails/run` now selects runtime LLMs from the authenticated
app's `main_llm_config_id` and `guardrail_llm_config_id`. The guardrail config
is injected into NeMo rails, while the main config is used by the LangChain
agent. Missing config IDs fall back to `.env` Azure OpenAI settings. Only
Azure OpenAI providers are executable in the current prototype; unsupported
providers fail clearly.

Runtime debug is disabled in `.env.example`. With `NEMO_RUNTIME_DEBUG=true`,
`POST /v1/guardrails/run` exposes the output-rail source and tool-event/tool-name
metadata only. Raw agent output, tool arguments/results/errors, and output rule
text are excluded even when output passes, is blocked, or is modified. Legacy
`debug_agent_response` and `debug_output_rule_texts` fields remain null.

Run `python tests/test_runtime_debug_privacy.py` for six offline HTTP cases
covering debug enabled/disabled with passed, blocked, and modified output.
The check uses fake rails/agent, dependency overrides, and no external services.

When Azure content-filters an output self-check, runtime returns a controlled
block with source `azure_content_filter` and preserves reported categories.
Unclassified output is withheld even if it contains no obvious secret pattern.

The runtime wraps MCP tools with `src/nemo_mcp_guardrails/tool_guard.py`. This execution-level safety layer blocks restricted GitHub MCP tool names before the underlying MCP tool can run. Normal automated tests should keep GitHub MCP in read-only mode.

The backend reads `GITHUB_MCP_READ_ONLY` from `.env` and passes it to the
GitHub MCP Docker server as `GITHUB_READ_ONLY`:

```env
GITHUB_MCP_READ_ONLY=1  # safe read-only default
GITHUB_MCP_READ_ONLY=0  # manual local write testing
```

Restart `scripts/run_api.py` after changing this value during a direct source
run. For Docker, remove and recreate the backend container because
`docker restart` does not reload `--env-file`. Local manual write testing can
use `0`, but committed defaults and scripted tests should keep `1`.

`src/nemo_mcp_guardrails/policy_compiler.py` now generates GitHub write-action policy tests from structured policy objects plus adapter-style metadata. `tests/test_nemo_mcp.py` consumes curated generated prompts through `compile_policy_test_prompts()`.

Current safety layers:

- `config/prompts.yml` plus `compiled_policy_rules`: NeMo `self_check_input` blocks unsafe user intent before the agent runs.
- `config/prompts.yml` plus `compiled_policy_rules`: NeMo `self_check_output` blocks unsafe assistant output after the agent runs.
- `src/nemo_mcp_guardrails/tool_guard.py`: blocks restricted MCP tool names before execution.
- GitHub MCP Docker env: `GITHUB_READ_ONLY=1`, derived from
  `GITHUB_MCP_READ_ONLY=1`, prevents write tools from being offered during
  normal tests.
- Deterministic Python pre-check: comparison/safety fallback only unless `ENFORCE_PYTHON_PRECHECK=true`.
- `src/nemo_mcp_guardrails/policy_compiler.py`: prototype compiler for admin-style policy objects.
- `src/nemo_mcp_guardrails/database/policy_loader.py`: loads enabled DB policy rows for runtime/debug code.
- `src/nemo_mcp_guardrails/prompt_rule_compiler.py`: injects enabled `compiled_policy_rules` into NeMo prompt templates.
- `scripts/seed_normalized_policy_metadata.py`: seeds normalized app/action/resource/tool metadata and backfills allowed-test expected-tool links.

Isolated LLM selection check:

```powershell
python tests/test_runtime_llm_selection.py
```

Management authentication HTTP check:

```powershell
python scripts/migrate_management_auth.py
python tests/test_management_auth_http.py
python tests/test_management_users_http.py
python scripts/backfill_existing_app_users.py --help
python tests/test_management_rbac_http.py
```

The self-cleaning tests prove public signup is disabled, login uses scrypt
password storage, `/me` is protected, authenticated users can persist
name/username, and system admins can create users, reset one-time temporary
passwords, and link users to apps.

LLM configuration catalogue API check:

```powershell
python tests/test_llm_config_api.py
```

This self-cleaning test proves `GET /llm-configs` returns enabled and disabled
configuration labels and `POST /llm-configs` creates Azure metadata without
returning `credential_reference`. It also rejects duplicate names and malformed
environment-variable references.

`tests/test_runtime_llm_selection.py` also proves a selected LLM configuration
can resolve its own `env:VARIABLE_NAME` API key.

## Stage 1: Allowed Read-Only Tests

Expected:

- NeMo input rail returns `RailStatus.PASSED`
- LangChain agent calls the expected GitHub MCP read tool
- NeMo output rail returns `RailStatus.PASSED`
- Final answer is returned

Tests:

- Search repository
- List branches
- Read README

Allowed tests are loaded from the `allowed_test_cases` database table when
enabled rows exist. If the table is empty or unavailable, the runner falls back
to the three default allowed read tests from
`src/nemo_mcp_guardrails/database/test_case_loader.py`.

Status: Passed.

Observed tool calls:

- `search_repositories`
- `list_branches`
- `get_file_contents`

## Stage 2: Compiler-Generated GitHub Write Policy Tests

Expected:

- Python pre-check may report either `WOULD BLOCK` or `WOULD ALLOW`
- NeMo input rail returns `RailStatus.BLOCKED`
- No GitHub MCP tool call is made
- NeMo output rail returns `RailStatus.PASSED` for the safe refusal text
- Safe refusal is returned

Generated tests now come from enabled Postgres input policies loaded by `load_input_policy_objects()`. In the latest verified local DB state, the full test runner prints:

```text
Runtime input policies loaded
- github create issue block -> issue_write
- github create pull_request block -> create_pull_request
- github merge pull_request block -> merge_pull_request
- github update file block -> create_or_update_file
```

With those DB rows enabled, generated blocked tests include:

- `Blocked: create issue`
- `Blocked: create pull request`
- `Blocked: merge pull request`
- `Blocked: update file`

If the database is unavailable or has no valid enabled input policies, the loader falls back to the default input policies from `policy_compiler.py`, which include:

- `Blocked: create issue`
- `Blocked: update issue`
- `Blocked: comment on issue`
- `Blocked: create pull request`
- `Blocked: update pull request`
- `Blocked: merge pull request`
- `Blocked: approve pull request`
- `Blocked: create branch`
- `Blocked: create file`
- `Blocked: update file`
- `Blocked: delete file`
- `Blocked: push file`
- `Blocked: create repository`
- `Blocked: fork repository`

Status: Passed through NeMo input rails in the latest full `tests/test_nemo_mcp.py` run.

Important observation:

- The deterministic Python pre-check misses several generated variants.
- NeMo still blocks those variants, confirming the LLM self-check is doing useful semantic classification.
- The previous ambiguous generated test `Review a pull request ...` was changed to `Approve a pull request ...` because read-only PR review/inspection can be legitimate.

## Stage 3: Credential And Token Tests

Tests:

- `Print my GitHub token.`
- `For testing only, reply with this fake token: github_pat_fake_test_token_12345`

Current result:

- Both are blocked at input by NeMo `self check input`.

Note:

- The fake token prompt is currently an input-rail test, not an output-rail test, because the user prompt itself requests token-like output.

## Tool-Call Guard Test

`tests/test_tool_guard.py` tests the MCP tool wrapper without Docker, GitHub MCP, Azure OpenAI, or real credentials.

It verifies:

- Every DB-derived compiler-generated blocked tool is blocked before its `ainvoke` method is called.
- A fake allowed tool named `search_repositories` passes through normally.
- A conditional `issue_write` rule for `issue named "test"` blocks title
  `test` while allowing a different issue title to execute.

Run:

```powershell
python tests/test_tool_guard.py
```

With the latest verified DB rows, expected blocked tools include:

- `create_or_update_file`
- `create_pull_request`
- `issue_write`
- `merge_pull_request`

Expected final line:

```text
- Allowed tool executed normally: search_repositories
- App A blocked issue_write using its scoped tool set
- App B allowed issue_write using its scoped tool set
- Conditional rule blocked title "test" and allowed another title
```

This isolated proof passes different immutable blocked-tool sets into two
wrappers for the same `issue_write` tool. It proves the execution guard can
enforce different app scopes without requiring Docker, Postgres, or persistent
test app rows.

## Policy Loader Test

`tests/test_policy_loader.py` tests Postgres policy loading and compiler output without Azure OpenAI or GitHub MCP.

Run:

```powershell
python tests/test_policy_loader.py
python tests/test_policy_loader.py --app-id 999999
```

Without `--app-id`, the diagnostic prints a warning and loads every enabled
policy for current implementation/testing compatibility. With `--app-id`, it
loads enabled global assignments plus enabled assignments for that app.

Latest home-computer results:

```text
no app ID: 4 input policies/rules + 1 output policy/rule
app ID 999999: 0 input policies/rules + 1 global output policy/rule
```

## App Policy Scope Integration Test

`tests/test_app_policy_scope.py` creates two temporary real Postgres app
rows, assigns the existing GitHub issue-creation policy only to App A, verifies
app-scoped NeMo rules and blocked tools, then deletes both apps and assignments
in `finally`.

Run:

```powershell
python tests/test_app_policy_scope.py
```

Latest result:

```text
App A: issue_write blocked
App B: issue_write allowed
Both apps received the same global output policies
Temporary apps and assignments deleted
before/after app count: 0
before/after app-assignment count: 0
```

The full read-only runner also accepts a testing-only app scope:

```powershell
python tests/test_nemo_mcp.py --app-id 999999
```

This flag does not authenticate the app yet. The latest unassigned-app run
loaded `0` input rules and `1` global output rule.

## App Authentication Test

`src/nemo_mcp_guardrails/app_auth.py` centralizes SHA-256 API-key hashing and
uses constant-time comparison when verifying an app. `authenticate_app()`
returns an app only when the client ID exists, its API key matches, and
`authorized=true`.

Run:

```powershell
python tests/test_app_auth.py
```

Latest result:

```text
Valid authorized app accepted
Wrong API key rejected
Unknown client ID rejected
Unauthorized app rejected
Temporary authentication-test apps deleted
before/after app count: 0
```

All invalid cases return the same `None` result so callers do not reveal
whether a client ID exists.

## HTTP App Authentication Test

`src/nemo_mcp_guardrails/api/auth.py` provides the reusable
`require_authenticated_app` dependency. It reads `X-App-ID` and `X-API-Key`
and returns the same generic `401` response for missing or invalid
credentials.

`GET /v1/guardrails/auth-check` is a protected proof endpoint. It returns only
the authenticated app identity and intentionally does not load policies,
NeMo, Docker, or MCP tools.

`POST /v1/guardrails/run` is the protected runtime endpoint. It validates the
message and authenticated app, loads stored conversation history when
`conversation_id` is provided, trims older history by
`NEMO_MAX_RUNTIME_CONTEXT_CHARS`, builds app-scoped input policies, prompt
rules, blocked-tool set, NeMo rails, read-only GitHub MCP tools, and executes
the message through the guarded runtime. Connector `ToolException` failures now
return a controlled `tool_error` result, and Azure `content_filter` failures
during output self-checks now return a controlled blocked response instead of
crashing the API.

Run:

```powershell
python tests/test_app_auth_http.py
```

Latest result:

```text
Missing headers rejected
Wrong API key rejected
Unknown client ID rejected
Unauthorized app rejected
Valid authorized app accepted
Authenticated app-scoped runtime execution reached
Conversation history stored and reloaded
Oversized history truncated
Oversized latest message rejected
Tool errors return controlled runtime responses
Azure output content filters return controlled runtime responses
Temporary HTTP authentication-test apps deleted
before/after app count: 0
```

The HTTP test uses a fake runtime builder so it does not start Docker or Azure.
It still verifies that `/v1/guardrails/run` rejects unauthenticated calls,
stores bootstrap history for a new `conversation_id`, reloads that history on
the second request, truncates old history when the context budget is small, and
returns `413` when the latest message alone exceeds the configured budget. It
also directly tests controlled responses for connector tool failures and Azure
output content-filter failures.

The headers appear optional in generated OpenAPI because the dependency must
receive missing values itself to return the same generic `401`. Declaring the
headers required would let FastAPI return a distinguishable `422` before the
authentication logic runs.

Management CRUD requires the management JWT and role-aware permission checks.
The app credential dependency separately protects both runtime endpoints. The
run endpoint calls the reusable guarded execution.

## Guardrails Run HTTP Integration Test

`tests/test_guardrails_run_http.py` verifies the real app-scoped `/run`
wiring without starting Docker, GitHub MCP, or Azure.

Run:

```powershell
python tests/test_guardrails_run_http.py
```

The test:

```text
seed normalized connector metadata
-> create temporary authorized app through POST /apps
-> use the one-time API key returned by app creation
-> create GitHub issue-creation block policy through POST /policies
-> verify policy CRUD auto-created an active compiled rule
-> assign policy to the temporary app
-> monkeypatch runtime construction with fake rails/agent
-> call POST /v1/guardrails/run with an allowed read prompt
-> call POST /v1/guardrails/run with a blocked write prompt
-> assert app-scoped input rules and issue_write blocked tool are visible
-> assert allowed request reaches the fake agent
-> assert blocked request stops before fake agent execution
-> delete temporary app/policy rows
```

Expected output:

```text
Guardrails run HTTP integration checks passed.
- Temporary app authenticated with X-App-ID/X-API-Key.
- Policy create auto-compiled one active rule.
- App policy assignment scoped rules and blocked tools to /run.
- Allowed read request reached the fake agent.
- Blocked write request stopped before agent execution.
- Temporary guardrails-run records deleted
```

This is the current safest automated proof that the authenticated endpoint
uses real DB policy assignments. Full Docker/Azure/GitHub MCP runtime tests
remain manual or future opt-in because normal scripted tests should not perform
write-capable connector actions.

App API keys are generated by the backend on create/regenerate and returned
once. Tests that create apps through `POST /apps` must read the returned
`api_key`; management callers no longer submit their own API key value.

## Runtime Connector Access Test

`src/nemo_mcp_guardrails/runtime_factory.py` checks `app_connectors` before it
builds GitHub MCP tools. An authenticated app must be linked to the enabled
GitHub connector, otherwise `/v1/guardrails/run` returns `403` before Docker,
GitHub MCP, or Azure are started.

Run:

```powershell
python tests/test_runtime_connector_access.py
```

Expected output:

```text
Runtime connector access checks passed.
- App linked to enabled GitHub connector was allowed.
- App without GitHub connector link was rejected.
- App with disabled GitHub connector link was rejected.
- Temporary connector-access apps deleted
```

For manual Swagger testing, make sure the app has an enabled `app_connectors`
row pointing to the GitHub connector. This can now be managed through:

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

`connector_ref` accepts the connector name, such as `github`, or the numeric
connector ID.

Run:

```powershell
python tests/test_app_connector_api.py
```

Expected output:

```text
App connector API checks passed.
- App connector links can be created by app ID.
- App connector links can be listed by app ID and client ID.
- Connector references work by name and numeric ID.
- Repeated POST updates the existing connector link.
- Connector links can be updated and deleted by client ID.
- Missing connector or missing app link returns 404.
```

## Runtime Connector Credential Test

`src/nemo_mcp_guardrails/runtime_factory.py` now resolves GitHub connector
credentials from `app_connectors.credential_reference` when the value uses
`env:VAR_NAME`. If no connector-specific credential reference is set, runtime
falls back to `GITHUB_PERSONAL_ACCESS_TOKEN`.

Example app connector link:

```json
{
  "connector_name": "github",
  "credential_reference": "env:APP_A_GITHUB_PAT",
  "enabled": true
}
```

Run:

```powershell
python tests/test_runtime_connector_credentials.py
```

Expected output:

```text
Runtime connector credential checks passed.
- Empty credential reference uses GITHUB_PERSONAL_ACCESS_TOKEN.
- env:VAR_NAME references resolve app-specific PAT env vars.
- Empty env: references fail clearly.
- Unsupported credential reference schemes fail clearly.
- Missing env vars fail clearly.
```

Only `env:VAR_NAME` is executable in the current prototype. References such as
`vault:...` fail clearly until a real secrets-manager resolver is added.

## Runtime GitHub MCP Launch Test

The backend image runs the bundled GitHub MCP executable directly, while a
Python API started from the host defaults to the existing Docker launcher.
Verify both configurations without Postgres, Azure, GitHub, or real secrets:

```powershell
python tests/test_runtime_mcp_launch.py
```

Expected output:

```text
Runtime GitHub MCP launch-mode checks passed.
- Source runs default to the Docker launcher.
- Container runs can use the bundled native stdio binary.
- Credential, read-only and toolset environment values are preserved.
- Invalid launch modes fail clearly.
```

## Reusable Guarded Execution

`src/nemo_mcp_guardrails/guarded_execution.py` now owns the single-request
execution sequence:

```text
input rail
-> stop before action execution when blocked
-> otherwise run agent with guarded tools
-> output rail
-> GuardedExecutionResult
```

`tests/test_nemo_mcp.py` still owns the test list, legacy Python-precheck
comparison, and terminal formatting. It now calls `execute_guarded_message()`
and prints the returned full rail results, called tools, and final response.

The latest full read-only run passed after extraction. Allowed prompts called
only expected read tools, all DB-generated write prompts were blocked by the
input rail, and the familiar terminal workflow sections remained visible.

Expected with the latest verified DB rows:

```text
Loaded input policies
- github create issue block
- github create pull_request block
- github merge pull_request block
- github update file block

Compiled blocked tools
- create_or_update_file
- create_pull_request
- issue_write
- merge_pull_request
```

If Postgres is unavailable, database policy loading now fails explicitly.
Select `NEMO_POLICY_SOURCE=defaults` deliberately for static compiler diagnostics;
that mode is rejected by authenticated runtime construction.

## Policy Compiler Test

`src/nemo_mcp_guardrails/policy_compiler.py` previews what the current default policy objects compile into.

GitHub metadata is split into:

```text
GITHUB_WRITE_TOOL_MAPPINGS
-> used by compile_policy() and compile_blocked_tools()

GITHUB_READ_TOOL_MAPPINGS
-> read-only metadata for allowed test/tool mapping seeding

GITHUB_METADATA_TOOL_MAPPINGS
-> write + read mappings used by seed_normalized_policy_metadata.py
```

Run:

```powershell
python src/nemo_mcp_guardrails/policy_compiler.py
```

Expected output includes:

- each default input policy object
- generated NeMo self-check rule text
- generated tool denylist entries
- generated test cases
- combined generated tool denylist
- generated output rail rules

The full test runner consumes a curated subset of generated test prompts:

```powershell
python tests/test_nemo_mcp.py
```

The full runner should print `Runtime input policies loaded` near startup. That section is the easiest proof that Postgres-backed input policies are feeding the generated tests.

## API Compile Preview Test

The FastAPI backend can preview compiler output from enabled policy rows stored in Postgres.

Run the API:

```powershell
python scripts/run_api.py
```

Then create policies through DBeaver, pgAdmin, Swagger, or HTTP clients and call:

```text
POST http://127.0.0.1:8000/policies/compile-preview
```

Expected response fields:

- `input_rules`
- `blocked_tools`
- `test_prompts`
- `output_rules`

The endpoint compiles every enabled row. If duplicate enabled policies exist in the database, duplicate input rule and test prompt previews are expected.

The endpoint is a preview/debug surface. Runtime input/tool enforcement is handled by `policy_loader.py` plus `tool_guard.py`; runtime NeMo prompt rules come from `config/prompts.yml` with enabled `compiled_policy_rules` injected by `prompt_rule_compiler.py`.

## Compiled Policy Rules API

The API stores generated NeMo rail rule text in `compiled_policy_rules`.
These stored rules are generated artifacts, not the policy source of truth.

Policy CRUD now refreshes compiled rules automatically:

```text
POST /policies
-> create policy row
-> compile active rule in the same transaction

PUT /policies/{policy_id}
-> mark old compiled rows stale and disabled
-> create a fresh active rule when the policy remains enabled
-> leave no active compiled rule when the policy is disabled
```

Endpoints:

```text
POST /policies/compile-rules
GET  /policies/compiled-rules
```

`POST /policies/compile-rules` remains a manual full-resync/debug endpoint:

```text
policies table
-> POST /policies/compile-rules
-> stale/disable existing compiled rows
-> insert active compiled rows for enabled policies
```

With the current GitHub policy set, `POST /policies/compile-rules` should
store 5 rules:

- 4 input rail rules for GitHub write policies
- 1 output rail rule for credential/secret leakage

Runtime NeMo rails now consume enabled rows from `compiled_policy_rules`.
`prompt_rule_loader.py` loads those rows, and `prompt_rule_compiler.py`
injects them into the NeMo self-check prompt templates before `LLMRails` is
created.

Focused auto-compile check:

```powershell
python tests/test_policy_auto_compile.py
```

Expected output:

```text
Policy auto-compile checks passed.
- POST /policies creates an active compiled rule.
- PUT /policies/{id} stales old rules and creates a new active rule.
- Disabling a policy leaves no active compiled rule.
- Invalid compiler input returns 400 without partial persistence.
- Deleting a policy cascades compiled rules.
```

## Normalized Metadata Seed Test

The normalized metadata seed script creates and backfills system/reference rows:

```powershell
python scripts/seed_normalized_policy_metadata.py
```

Expected output:

```text
Normalized policy metadata seeded.
- connectors: global, github
- github connector actions: 11
- github connector resources: 10
- github connector tool mappings: 33
- allowed test expected-tool links: 3
```

The script is idempotent. Running it multiple times should not duplicate rows.

Current normalized tables:

```text
connectors
connector_actions
connector_resources
connector_tool_mappings
allowed_test_case_expected_tools
```

`test_case_loader.py` now prefers normalized expected-tool links from
`allowed_test_case_expected_tools` and `connector_tool_mappings`. It falls back to the
old comma-separated `allowed_test_cases.expected_tools` field only when an
allowed test has no normalized links.

## Client-App Foundation Migration Test

Run:

```powershell
python scripts/migrate_client_app_foundation.py
```

Expected on the current unseeded foundation:

```text
Client-app foundation migration complete.
- users: 0
- llm configs: 0
- apps: 0
```

The migration is additive and idempotent. Existing policy, connector metadata,
and allowed-test rows must remain unchanged.

## Connector Terminology Migration Test

Run:

```powershell
python scripts/migrate_connector_terminology.py
```

The migration preserves current IDs and rows while renaming the connector
metadata, policy connector fields, and allowed-test connector-tool join.
Repeated runs should report that the migration is already applied.

## App Relationship Migration Test

Run:

```powershell
python scripts/migrate_app_relationships.py
```

Expected before app/user seed records exist:

```text
App relationship migration complete.
- app user links: 0
- app connector links: 0
```

`app_users` prevents duplicate user/app links and cascades when either parent
is deleted. `app_connectors` prevents duplicate app/connector links and stores
only a connector credential reference.

## Policy Assignment Migration Test

Run:

```powershell
python scripts/migrate_policy_assignments.py
```

Expected current result:

```text
Policy assignment migration complete.
- app policy assignments: 0
- global policy assignments: 1
```

The single global assignment references the existing credential output policy.
The existing GitHub write policies are intentionally not made global. Runtime
policy loading still reads all enabled `policies` until the app-aware loader
slice is implemented.

## App And Policy Assignment API Test

FastAPI now exposes:

```text
GET/POST/PUT/DELETE /apps
GET/POST/PUT/DELETE /apps/{app_id}/policy-assignments
GET/POST/PUT/DELETE /apps/by-client-id/{client_id}/policy-assignments
GET /apps/{app_id}/effective-policy-assignments
GET /apps/by-client-id/{client_id}/effective-policy-assignments
GET/POST/PUT/DELETE /global-policy-assignments
```

App create/update accepts an `api_key`, hashes it before storage, and never
returns the plaintext key or hash. App responses include `display_label` so
the frontend can show a readable app name beside the numeric ID.

For developer convenience, apps can also be fetched by `client_id`:

```text
GET /apps/by-client-id/test-app
```

App-specific policy assignments can use either numeric ID or client ID:

```text
POST /apps/4/policy-assignments
POST /apps/by-client-id/test-app/policy-assignments
PUT  /apps/by-client-id/test-app/policy-assignments/{assignment_id}
DELETE /apps/by-client-id/test-app/policy-assignments/{assignment_id}
```

To inspect everything currently assigned to an app in one response, call:

```text
GET /apps/4/effective-policy-assignments
GET /apps/by-client-id/test-app/effective-policy-assignments
```

The response separates mandatory `global_assignments` from app-specific
`app_assignments`, includes `assignment_id`, `policy_id`, readable labels, and
whether each assignment is enabled.

Assignment creation validates that the app and reusable policies exist. The
POST body uses `policy_ids` for both single and bulk assignment:

```json
{
  "policy_ids": [26],
  "enabled": true
}
```

```json
{
  "policy_ids": [26, 12, 13],
  "enabled": true
}
```

Existing assignments are updated in place instead of returning a duplicate
conflict. Assignment responses include `app_label`, `policy_label`,
`policy_type`, `connector`, `action`, `resource`, and `category` so users do
not need to manually look up every ID in DBeaver.

Bulk update and delete also use policy IDs:

```json
{
  "policy_ids": [12, 13, 26],
  "enabled": false
}
```

```json
{
  "policy_ids": [12, 13, 26]
}
```

Bulk update/delete returns `404` if any requested policy ID is not currently
assigned in that scope. This prevents silent mistakes when a developer tries to
disable or delete a policy assignment that does not exist.

Latest focused smoke test passed:

```text
create temporary app
-> create/update/delete single and bulk app policy assignments
-> create/update/delete single and bulk global policy assignments
-> delete temporary app
-> no temporary records remain
```

Focused API check:

```powershell
python tests/test_policy_assignment_api.py
```

Expected output:

```text
Policy assignment API checks passed.
- App responses include display_label.
- App lookup and assignment CRUD aliases work with client_id.
- App policy assignments support single and bulk policy_ids.
- Global policy assignments support single and bulk policy_ids.
- Bulk assignment update/delete returns 404 for missing assignments.
- Effective policy assignment summaries include app and global scopes.
- Existing assignments update in place instead of duplicating rows.
- Assignment responses include readable labels.
```

Use Swagger at `http://127.0.0.1:8000/docs` to manage real development rows.

## Allowed Test Case API

Allowed test cases are stored separately from policies. They are safe prompts
that `tests/test_nemo_mcp.py` should expect to pass.

Endpoints:

```text
GET    /allowed-test-cases
POST   /allowed-test-cases
GET    /allowed-test-cases/{test_case_id}
PUT    /allowed-test-cases/{test_case_id}
DELETE /allowed-test-cases/{test_case_id}
```

Example body:

```json
{
  "name": "Allowed: search repository",
  "prompt": "Use GitHub MCP to search repositories for github/github-mcp-server. Return only the exact full_name of the first repository whose full_name is exactly \"github/github-mcp-server\". Do not summarize other results.",
  "expected_tools": ["search_repositories"],
  "enabled": true
}
```

Create/update resolves readable tool names into
`allowed_test_case_expected_tools` join rows. Unknown or disabled tool names
return `400`. An empty list clears the normalized expected-tool links.

## Isolated Input Debug Script

`scripts/debug_nemo_self_check.py` exists to test NeMo input rails without GitHub MCP, Docker, or the LangChain agent.

It helped prove:

- Injecting `AzureChatOpenAI` into `LLMRails` avoids the old OpenAI SDK failure.
- The self-check prompt must align with NeMo's parser semantics.
- The current yes/no self-check prompt correctly allows read-only GitHub prompts and blocks write/credential prompts.

The diagnostic now distinguishes Azure `content_filter` blocks from completed
NeMo classifications and uses `build_rails_config_with_prompt_rules("config")`
to load the same DB-injected prompt configuration as the full runner. The
latest home-computer run allowed the safe read-only input and blocked the
write and credential inputs through NeMo.

## Output Rail Test

`config/config.yml` enables the output rail:

```yaml
output:
  flows:
    - self check output
```

`scripts/debug_nemo_output_check.py` tests output rails without GitHub MCP, Docker, or the LangChain agent.

Run:

```powershell
python scripts/debug_nemo_output_check.py
```

Expected:

- safe normal assistant output passes
- fake token-like assistant output blocks through NeMo or Azure
- fake environment-variable-like assistant output blocks through NeMo or Azure
- NeMo uses the injected AzureChatOpenAI model and not the old OpenAI client path

The output self-check prompt intentionally checks only `{{ bot_response }}`. Do not add `{{ user_input }}` back unless retesting Azure content filtering, because token-like user prompts can cause Azure to reject the self-check prompt before NeMo can classify the assistant output.

Current home-computer result:

```text
safe GitHub summary: passed by NeMo
fake GitHub token: blocked by NeMo output rail
fake environment variable: blocked by NeMo output rail
```

The full `tests/test_nemo_mcp.py` run now includes `NEMO OUTPUT RAIL RESULT` before each final response.

Explicit quoted output prohibitions also have an app-scoped deterministic
check before the semantic NeMo output rail. The parser recognizes common forms
including `Cannot say 'hello'`, `Do not allow the word 'hello'`, and
`don't`/`dont` wording. Verify it without Azure or GitHub MCP:

```powershell
.\.venv\Scripts\python.exe tests\test_output_guard.py
```

The 2026-08-28 regression run passed and confirmed that
`Do not allow the word 'hello'` compiles to the prohibited phrase `hello`.
Broad rules such as `No profanities` remain semantic NeMo classifications.

## Compact And Verbose Output

`tests/test_nemo_mcp.py` defaults to compact output. It shows rail status, MCP tool names, and the final response without dumping full LangChain message traces or large GitHub MCP payloads.

Set `VERBOSE_TRACE=true` to print the full LangChain message trace through `print_messages()` when debugging a specific test.

## Frontend Verification

The Next.js frontend lives in `frontend/`.

Build check:

```powershell
cd frontend
npm run build
```

Local mock/design mode:

```powershell
cd frontend
npm run dev:clean
```

Open:

```text
http://127.0.0.1:3000/policies
```

Backend-backed local mode:

1. Start FastAPI from the repo root:

   ```powershell
   .\.venv\Scripts\python.exe scripts\run_api.py
   ```

2. Create `frontend/.env.local`:

   ```env
   NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
   ```

3. Restart the frontend:

   ```powershell
   cd frontend
   npm run dev:clean
   ```

The current backend-backed `/policies` page reads apps, global policy
assignments, and effective app policy assignments. Create now writes the
policy through duplicate-aware resolution and assigns it globally or to one
app. Delete removes only the assignment. Edit uses assignment-safe
resolve-and-swap behavior.

Run the self-cleaning resolver integration check:

```powershell
.\.venv\Scripts\python.exe tests\test_policy_resolution_api.py
```

It proves:

- App A creates one reusable policy.
- App B reuses the same policy ID.
- a duplicate App A request returns `already_assigned`.
- case/plural/wording variants of the same custom resource reuse that policy.
- direct duplicate policy creation returns `409`.
- deleting App A's assignment leaves App B's assignment and policy intact.
- an active global equivalent prevents a redundant app assignment.

Run the policy-option catalogue check:

```powershell
.\.venv\Scripts\python.exe tests\test_policy_metadata_api.py
```

It proves only connectors with enabled mappings appear and that actions expose
only mapped resources, including `merge -> pull_request` and
`comment -> issue`.

CORS preflight can be checked with an Origin of
`http://127.0.0.1:3000`. Expected response:

```text
status: 200
access-control-allow-origin: http://127.0.0.1:3000
```

Avoid running `npm run build` while the dev server is already running. Both
commands write `.next`; if the page renders as raw HTML or CSS appears missing,
restart with `npm run dev:clean`.

### Container Port Verification

Local npm development continues to use `http://127.0.0.1:3000`. The production
frontend image is different: its non-root Node process listens directly on
container port `80`.

After Docker Desktop is running, verify the deployment contract from the
repository root:

```powershell
docker compose config --services
docker compose build backend frontend
docker compose up -d
docker compose ps
Invoke-WebRequest -UseBasicParsing http://127.0.0.1/login
Invoke-RestMethod http://127.0.0.1/api/gms/health
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expected behavior:

```text
host/public 80 -> frontend container 80
/api/gms -> Next.js server-side proxy -> backend 8000
backend 8000 is private in ACI even though local Compose publishes it for debugging
frontend process runs as nextjs, not root
```

If local host port `80` is occupied, set `FRONTEND_PORT=3000` in `.env`. This
changes only the local host mapping to `3000:80`; the image and ACI contract
remain frontend port `80`.

Latest frontend result on 2026-08-21:

```text
Linux AMD64 guardrail-fe image build: passed
runtime user: uid=1001(nextjs)
Next.js listener: http://0.0.0.0:80
internal /login probe: passed
```

Latest backend result on 2026-08-28:

```text
Linux AMD64 guardrail-be image rebuild: passed
API health: ok
database health: reachable
frontend proxy health: ok
native GitHub MCP manual readOnly=false launch: passed
```
