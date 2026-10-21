# Developer main-model registration review - 22 October 2026

## Final home acceptance - 22 October 2026

The registration feature and unified form now have user-confirmed home use plus
clean-image verification. All 35 final-image offline checks, 16 PostgreSQL
diagnostics and schema idempotency/constraints pass. A linked developer registered
an encrypted app-owned Azure main profile through the real frontend proxy;
classification/cross-app grants were denied and a native-MCP branch read passed
with real Azure classification. Four model guides match the current API Type-first
form/default direct-key path and admin Advanced credentials; all 11 JSON examples
validate against application schemas. Existing home profiles/key/selection were
preserved. See [the final results](home-verification-results-2026-10-22.md); older
pending schema/key/registration/build statements below are historical.


## API-type-first UI applied - 22 October 2026

The user approved the exact one-file form correction with "ok". The applied
modal matches its reviewed hash. API Type is the first field for both roles;
default endpoint/API-key fields match. Admin backend-credential selection is
inside collapsed Advanced credentials, with developer main-only access retained.
Applied TypeScript and full ESLint passed. Earlier synthetic rendering verified
matching default forms and hidden/collapsed role-specific controls. No backend,
database, private environment or model selection operation ran for this change.
The user previously reported saving the developer Ollama profile; its live
guarded runtime test remains the next acceptance step. The preview-only section
below is historical.


## API type first for both roles - preview 22 October 2026

The user reported saving the instructed developer Ollama profile. No guarded
runtime request using that new profile has been reported yet. They then noted
that the admin credential-source selector appearing before API Type made the
forms look inconsistent. API protocol and credential source are independent.

A one-file UI preview puts API Type first for both roles and uses identical
default endpoint/API-key fields. The administrator-only backend credential
choice moves into collapsed Advanced credentials below those fields. Developer
main-only permissions and both submission paths are unchanged. This preview is
not applied. TypeScript, full ESLint and patch applicability pass; rendering
confirmed that default admin/developer markup matches after removing the admin
advanced section, which is collapsed and absent for developers. Exact patch and
review hashes are under .waylog/model-profile-api-type-first-preview-20261022.


## Unified UI applied after approval - 22 October 2026

The user approved the exact three-file UI patch with "ok". It is applied and
each file/deletion matches its reviewed hash. Models now has one Add model
profile button at the far right of the Save model selections action row and
one shared form. Developers submit endpoint/key profiles with automatic
main-only access; admins also retain backend-credential provisioning for
main/classifier profiles. The duplicate Add main model modal was removed.
Applied TypeScript, full ESLint and the two existing registration/grant HTTP
checks passed. Visual layout and live new-profile creation await user refresh/
acceptance. No additional database or private environment operation ran.
The earlier preview-only section below is historical.


## Unified model-profile UI preview - 22 October 2026

The user confirmed private encryption-key setup and reported the new button was
visible after restarting/refreshing. Actual new-profile creation/provider testing
is still pending. The user requested one Add model profile action aligned to the
far right of Save model selections, with developer-created profiles usable only
as main agents.

A three-file frontend preview now combines both modals into CreateLlmConfigModal,
removes the duplicate Add main model component/action, and places the single
button in a flex action row. Developers see endpoint/key entry and main-only
registration. Administrators additionally see the existing backend-credential
path in the same form for profiles that they may approve for main/classifier use.
The existing API and app/purpose permission checks are retained. The unified UI
is not applied; exact diff review is required first.

Preview TypeScript and full ESLint passed. The two existing offline registration/
grant HTTP checks passed. Rendering the form with empty synthetic inputs verified
that developer markup has a provider-key field and no backend/classifier choice,
while administrator markup includes the backend choice. Patch applicability
passed. Exact preview and hash manifest are ignored local files under
.waylog/model-profile-ui-preview-20261022; visual layout/user interaction awaits
approved application. No additional database or private .env operation ran.


## Home schema applied by user - 22 October 2026

The user ran scripts/migrate_app_main_models.py --apply with expected database
nemo_restore_check_ollama_20261020_153213 and supplied the successful verified-
rehearsal completion message. Record the home PostgreSQL schema application as
user-confirmed. This does not establish a second-run idempotency test or a
production migration. The next step is private encryption-key provisioning;
the backend is to remain stopped until setup is complete. Older no-migration
statements below describe the preceding source-only application checkpoint.


Status: the user approved the exact 17-file source patch with "ok" on 22 October
2026. It is applied and every file matches the reviewed candidate SHA-256. The
user chose to let developers enter their own endpoint and API key. Individual
main models need no administrator approval. Classifiers remain per-app and
admin-only. The existing global catalogue remains administrator-managed.

## Applied behavior

Linked app developers and administrators can add a profile through a new
app-scoped main-model endpoint, with an equivalent client-ID alias. The form
accepts a profile name, API protocol, model/deployment name, endpoint and key.
The profile and enabled main-purpose grant are created in one transaction.
The profile appears immediately among that app's main choices; selection is
saved separately. Creating it does not change the current classifier or grant
classifier access. Other apps cannot use it, even through an accidental grant.

The accepted protocols remain direct Azure OpenAI and openai_compatible. Native
vendor protocols still need a separately provisioned compatible API/gateway.
Existing backend destination approvals, URL validation and no-redirect SDK
transports remain in force. Typing a URL does not override those approvals.
No gateway, model download or endpoint provisioning is included.

## Key storage and scope

A dedicated GMS_MODEL_CREDENTIAL_ENCRYPTION_KEY supplies Fernet authenticated
encryption. Database rows store encrypted bytes, owner app ID and model metadata;
the submitted key is never returned or converted to a backend environment name.
The encrypted payload binds its key to the app, protocol, endpoint and model.
Moving it to a different context or changing the encryption key fails closed.
Encryption-key changes participate in runtime cache invalidation. Warm requests
still check live app/purpose grants and current destination policy.

The form holds the key only in component state, masks it and clears it after
submission or closing. Read schemas omit plaintext keys, ciphertext and legacy
credential references. Validation errors remain generic, and management audit
records retain action metadata without reading request/response bodies.

Fernet's key must be provisioned privately and backed up separately from database
backups. Losing it makes stored keys unreadable; replacing it without re-encryption
requires re-registering affected profiles. This preview does not supply an
automatic key-rotation tool or choose a production secrets-manager provider.
Reference: [cryptography Fernet documentation](https://cryptography.io/en/latest/fernet/).

## Schema and rollout

Two nullable llm_configs columns track the owning app and encrypted key. Existing
admin-managed profiles retain null values and their environment references. A
check constraint rejects mixed legacy/owned credential modes. The owner foreign
key deletes owned profiles when the app is deleted.

The helper previews DDL without connecting. Applying it requires both
--apply and the exact expected restored-rehearsal database name; current_database()
is checked before transactional DDL. It refuses production database names. The helper
ran in no-connection preview mode only; no schema change or private key
provisioning has run. Existing databases
must receive the reviewed additive schema before starting the changed API.
Production backup/recovery, rollout and release remain separate work.

## Verification

Current live home frontend TypeScript and full ESLint passed after npm ci.
Isolated preview TypeScript, full ESLint and all 34 offline catalogue checks
passed (33 existing plus the new registration/encryption/scope check). Tests use
synthetic credentials and disposable SQLite; external sockets and dotenv are
disabled. Existing Azure prerequisite behavior was preserved after regression
review. The host test environment has cryptography 48.0.0, while the proposed
direct requirement matches the existing 50.0.0 constraint; clean pinned install/
image validation is still required.

The exact 17-file patch passes git apply --check. Baseline/candidate SHA-256
hashes and final test output are retained privately under the isolated preview
folder. Actual PostgreSQL migration/idempotency was not exercised: the agent
cannot access the Docker engine pipe, although user-terminal Docker checks work.
No container or database was changed. Browser/provider acceptance of the new form
also awaits approved application and local schema/key setup.

## Applied-source verification checkpoint

The applied source passes TypeScript and full ESLint. The schema helper default
preview completed without connecting. The complete applied offline runner
passed all 34 checks; the prior isolated preview also passed all 34. The running
backend uses reload=False, so the source application did not restart it. Apply
the reviewed additive schema before restarting the changed backend, and provision
the dedicated encryption key privately before registering a model.


## Admin approval-button alignment (2026-10-22)

Applied the approved one-line spacing change in `app-models.tsx`: the admin
Approve access button now uses `ml-auto` so its right edge aligns with Add model
profile above it. Approval behavior and permissions are unchanged. The applied
file matches the preview candidate and `git diff --check` passes. Browser visual
confirmation remains pending.


## Live developer-profile correctness check (2026-10-22)

The user reported Input, Tool guard and Output all passing, but the answer
claimed that the repository had no branches, contradicting the earlier verified
branch-list result. Treat live model correctness acceptance as unresolved. The
request ID, tool invocation events and actual tool result for this run have not
yet been supplied, so no cause is established.

Source inspection confirms that the output rail checks active output policies
using only the assistant response; it does not compare GitHub evidence. The
normal completion path also sets tool_guard_status to passed even when the
agent called no tool. Thus the displayed Tool guard passed badge alone does not
prove a list_branches call occurred. Inspect Traffic execution events next; if
repeating, use a fresh conversation ID to avoid stored conversation context.
No application code, model selection, credentials or database was changed.


### Follow-up execution evidence

The user supplied the 2026-10-21 18:39:20 UTC run: list_branches had both
tool.started and tool.returned events, with tool guard passed and a 1278.7 ms
tool duration. Total duration was 26694.5 ms. This rules out a skipped tool for
this particular run. Events omit arguments and result content, so they do not
establish the requested owner/repository parameters, nonempty success data or
faithful model interpretation. The incorrect-answer report remains unresolved;
no source changes were applied. A fresh-conversation read requesting only actual
returned branch names is the next user-run diagnostic.


### Fresh-conversation retry reported

The user supplied a retry response listing development, feat/add-user-management,
main, production and staging, with Input, Tool guard and Output all passed.
These names match the earlier home acceptance response. The response included
JSON metadata despite the request for branch names only; no raw tool-result
payload or new execution trace was supplied. Record a successful expected-name
retry, not independent verification of the generated SHA/protection fields or
a resolved root cause for the preceding empty-branch answer. The retry changed
both conversation context and prompt wording, so their effects are not isolated.
No source, credentials, model selection or database was changed.


### Original-prompt fresh-conversation check

The user repeated the original branch-list prompt with another fresh conversation
ID and reported all three stages passed with the expected five branch names.
They confirmed that changing the conversation ID works. Stored conversation
context is now the leading explanation for the earlier incorrect answer, although
the original raw tool result is unavailable and model variability is not excluded.
Use a fresh ID for each independent acceptance test and reuse an ID intentionally
for follow-up turns. The developer profile has user-reported live expected-name
read acceptance; this does not establish general model accuracy or independent
verification of every response field. No source or database change was needed.


### Production frontend build accepted

The user ran npm.cmd --prefix frontend run build on the applied home source.
Next.js 16.4.2 compiled successfully; TypeScript, page-data collection, all 13
static pages and final optimization completed. This confirms the current frontend
production build, not a clean pinned Python install, image build or deployment.
