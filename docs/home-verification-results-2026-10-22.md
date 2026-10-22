# Home verification results - 22 October 2026

Latest follow-up: [home readiness results](home-readiness-results-2026-10-22.md)
record the new 38-check image, real no-tool/read/blocked statuses, synthetic
database/key recovery and successful hosted CI for the user's pushed source.
The original image acceptance record below is retained.

Follow-up: the user approved and applied the
[ten-file automation/status patch](automated-verification-preview-2026-10-22.md).
Saved source now has 38 offline checks and fixes the no-tool badge; five affected
checks pass again after application. The 35-check image acceptance below is the
earlier image checkpoint. Those cached images were not rebuilt for this follow-up;
the subsequent hosted run now passes. Actual work policy repair remains deferred.

Status: **all four current home verification groups completed**. The user
explicitly authorized autonomous code changes and documentation updates while
asleep. This scope did not include production migrations, image publication,
external gateway provisioning or deployment. Existing home app settings,
credentials, API keys, database and server processes were preserved.

## Results

| Verification | Result |
| --- | --- |
| Clean Linux AMD64 backend installation | 17 direct roots and 117 installed constrained runtime packages match the source pins; imports pass; build-time pip check passes |
| Final backend offline catalogue | **35 passed, 0 failed**, with networking disabled and no private credentials mounted |
| PostgreSQL app-model migration | Wrong-database refusal, legacy-column upgrade, repeat-run idempotency, owner foreign key, credential-mode check constraints and delete cascades pass |
| Explicit PostgreSQL diagnostic set | **16 passed**, including the previously failing test_guardrails_run_http.py |
| Current frontend image | Clean npm ci and production build pass on digest-pinned Node 24.21.0; Next.js 16.4.2/React 19.3.1 |
| Image-pair contract | Non-root frontend on port 80, backend on 8000, same-network-namespace loopback /api/gms proxy, frontend health and DB health pass; Node has cap_net_bind_service=ep |
| Real management/app authentication | Synthetic users/apps; missing/wrong credentials rejected and valid credentials accepted through the real frontend proxy |
| App-owned registration on PostgreSQL | Real provider key submitted by a linked developer, encrypted at rest, omitted from responses, automatic main grant, separate selection, and successful decryption on cryptography 50.0.0 |
| Isolation | Cross-app owned-model grants, classifier grants for owned models, developer grant administration and developer classifier changes rejected |
| Live real runtime | App-owned Azure main + Azure classifier + bundled native GitHub MCP list_branches returns the five expected names, with actual tool.started/tool.returned events |
| Matching input policy | Issue-creation request blocked before tool execution; GitHub MCP remained read-only |
| Model guide formats | All **11 JSON examples** in the four model guides parse and validate against current API request schemas |
| Production frontend audit | **0 findings** in the current unchanged lockfile; full development graph still reports the known seven high entries rooted in braces |
| Final runtime Python advisory coverage | All 117 final installed package versions covered by the OSV query; nine remaining advisory IDs concern Pillow 12.3.0 |
| Whitespace/source checks | git diff --check passes; final app code is included in the verified local image |

The actual native GitHub MCP binary reports v1.0.4, commit
c3dedbece0bf3834829f638a245fb3c51cd98d0b, from the reviewed pinned image digest.
The first live read took about 6.70 s; the final-image read took about 6.89 s.
These are smoke-test samples, not a performance benchmark. The final request ID
was 84b84830bb83440b9e000651226223ab. Request/app/model IDs in the evidence belong
to the disposable database, not the user's home app 33 or Azure rehearsal apps.

## Code changes completed under the user's authority

1. **Canonical title block explanations.** The explanation helper now parses a
   supported title selector and matches its literal value with word boundaries.
   Previously it searched for the canonical selector string in ordinary prompt
   text and returned a generic reason. The original integration assertions for
   the specific reason and policy ID/name now pass unchanged. New offline tests
   cover canonical/legacy spellings, regex punctuation, case, unmatched literals,
   partial words and generic fallback. This helper remains explanatory; rails
   and tool guards continue to make enforcement decisions.
2. **Runtime installer cleanup.** The full installed-image scan found the old
   pip 25.0.1 bundled by the Python base image, outside requirements/constraints.
   The Dockerfile validates requirements with pip check after installation, then
   removes pip from the runtime image. The dependency-builder stage retains its
   installer. Final image imports, all 35 offline checks and a live guarded read
   pass without runtime pip. Do not use python -m pip check inside the final
   runtime image; installation consistency is checked during its build and by
   installed metadata verification.

The PostgreSQL set completed before the runtime-only pip removal; application
source and the 117 runtime dependency versions were unchanged. The final image
then passed the full 35-check offline catalogue and a fresh real read.

Initial harness findings were corrected without relaxing application checks:
the legacy app-scope diagnostic needed its baseline compiled input/global-output
fixtures, and the temporary membership fixture needed the established internal
admin app-link role (the user's system role remained developer). Fixtures were
created only in the isolated database. An initial Dockerfile continuation syntax
error was corrected before the successful final build.

## Model documentation updated

The following guides now agree with the current UI and API:

- [Supported-provider setup](supported-llm-setup-guide.md)
- [Claude/Ollama walkthrough](model-switch-walkthroughs.md)
- [LLM provider/API guide](llm-provider-guide.md)
- [Gateway integration](model-gateway-integration.md)

They document the single right-aligned Add model profile action, API Type-first
fields, default app-owned Provider API key entry, automatic main-only grant and
separate Save model selections. Administrators use the same default form; their
Advanced credentials checkbox enables the environment-reference path, which
needs explicit purpose approval and supports classifiers. Updated examples
separate POST /apps/{id}/main-models api_key payloads from POST /llm-configs
credential_reference payloads. They also distinguish provider keys, GMS app API
keys and management JWTs, explain fresh conversation IDs, and preserve endpoint
allowlists, encryption-key backup and container localhost limitations. Native
vendor/gateway recipes remain role-specific live-acceptance targets; updating
these formats does not certify every provider or classifier.

## Credential handling and cleanup

Existing private Azure and GitHub values were loaded by name into the temporary
backend environment without being printed or written into reports/docs. No new
provider key, PAT, real management password or user app-key rotation was needed.
Only disposable fixture app keys were generated/regenerated. Test identities,
JWT/encryption settings and database credentials were synthetic. Private root
.env and the user's encryption key were not changed. A final scan of 89 changed
source/report files found none of the four existing private Azure, GitHub, JWT
or encryption-key values. Both existing host service health endpoints returned
HTTP 200 after cleanup.

Temporary frontend/backend/PostgreSQL containers and both test networks have
been removed. The test database used tmpfs, exposed no host port and contained
no restored user data. The original nemo_mcp_guardrails_postgres remains healthy
on host port 5433. Local images are retained for review, with no push/deployment:

| Local image | SHA-256 ID |
| --- | --- |
| gms-home-be:20261022 | b8bfcefb6e646b7fa72a7191014452a5beb353c10e2cdd916a47fd4825344f32 |
| gms-home-fe:20261022 | 62e046cf517d5d9eebfc9f697a40ab49d3cd578ffa5c49b4a26ef01fd2279779 |

Detailed evidence and the exact four-file autonomous code-fix patch are retained
privately under .waylog/home-verification-20261022/. They do not transfer with
Git; this document preserves the reviewable summary. No commit or push ran.

## When resuming

The user's Windows backend uses reload=False and was deliberately left running.
To load the saved explanation fix there, restart it once in the same verified
home backend terminal, preserving its database selection and read-only setting:

~~~powershell
python -B scripts/run_api.py
~~~

Its existing host virtual environment was not upgraded; the final pinned
verification ran in the isolated Linux image. The current frontend can stay
running. Do not regenerate the encryption key or reapply historical patches.

The repeat npm audit initially encountered an automatic-approval rejection over
potential private dependency metadata. Inspection confirmed that all 452 lock
entries resolve to public npm URLs, with no private/local/authenticated sources,
and both package manifests were unchanged from the user's earlier audit. The
evidence-backed retry was approved and completed with zero production findings;
no audit approval remains pending.

## Still open, separate from completed home checks

- Pillow 12.3.0 advisories: current and newer published FastEmbed versions still
  require Pillow below 13; no incompatible override/removal was applied.
- Development-only braces advisory remains an upstream follow-up. The no-tool
  Tool guard passed badge is fixed in saved source by the approved follow-up
  linked above; existing source processes need a restart to load it.
- The earlier incorrect branch answer is not independently root-caused; fresh
  conversation retries worked, but its original raw tool result is unavailable.
- Work-network Azure timing/log evidence, policy 210 repair/validation and the
  unused Qwen classifier-grant review remain deferred.
- External gateway/new-provider acceptance is conditional on provisioning.
- Production recovery, schema/policy rollout, matching image publication and
  deployment verification remain deferred. Production is not declared ready.
- Selective branch merging remains unsupported and fails closed.

See [the reconciled remaining checklist](remaining-verification-2026-10-22.md)
and [current backlog](open-work-backlog.md).
