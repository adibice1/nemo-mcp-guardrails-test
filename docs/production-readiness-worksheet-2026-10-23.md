# Production configuration and recovery worksheet - 23 October 2026

Status: **release direction confirmed; authenticated Azure execution pending**.
The user selected the existing Azure environment, a fresh database/data set and
supervisor ownership, and authorized building/deploying the second release.
Both local images are built. See the
[final-workday release/handoff record](final-workday-handoff-2026-10-23.md) for
the actual URL, registry, image IDs, successful fresh-start rehearsal and the
current access blocker. No real fresh online database/admin or replacement
deployment has been created in this session.

The supplied guide formats are now implemented in [UserGuide.md](UserGuide.md)
and [DeveloperGuide.md](DeveloperGuide.md). They cover user tasks, maintainer
setup and operations; review their deployed configuration details after rollout.

## Inputs required from the target/release owners

Fill in identifiers and ownership through the agreed workflow. Supply actual
secret values only through protected configuration, not this document.

| Input | Current state |
| --- | --- |
| Production database | Fresh database on the agreed existing online environment; exact new name/emptiness must be recorded at creation; existing database preserved |
| Release app scope | Fresh data: no old apps 208/214/222, test users, app grants or history are imported |
| First system administrator | Supervisor, email/username admin@gmail.com; privately generated expiring setup password and first password replacement |
| Release source/image pair | Local guardrail-be/fe:fa76f78ba62d built from fa76f78ba62d9fff6d97c6587a61b9984a373955; exact IDs in the release record |
| Deployment owner/window | Supervisor owns the second deployment; complete online-dependent work while the user still has work access |
| Secrets/custody | Supervisor owns ongoing administration and secrets; inspect and preserve the existing deployment's protected runtime-injection mechanism using authenticated access |
| Model encryption key | Fresh production data may use an independent privately provisioned key under supervisor custody; preserve old matching keys with old backups |
| Backup/recovery | User has a backup to hand over privately; supervisor takes recovery ownership; verify actual transfer, archive contents/integrity and applicable matching keys |
| Previous working release/rollback | Second deployment: capture current image/config/database identities from Azure before changing the deployment; retain old database for rollback |
| Public URL/ingress | http://guardrails-fe.southeastasia.azurecontainer.io; HTTP is current and remains a recorded transport-security limitation |
| Registry/execution access | guardrail.azurecr.io, username guardrail; local registry access is unauthenticated, Azure CLI absent and browser runtime unavailable; execute from a supervisor-authorized Azure/work session |
| Dependency disposition | User explicitly permits release with the documented findings; they remain unresolved |

The former app 208/214/222 questions are closed for this fresh release. Existing
rehearsal records, including app 221's deliberately retained grant, remain
unchanged in the old database. A fresh database still needs required platform
metadata, a baseline global credential policy and the first administrator; it
does not receive automatic access grants for future apps.

## Configuration matrix

| Location | Required configuration | Validation/evidence |
| --- | --- | --- |
| Backend | External persistent PostgreSQL connection | Confirm actual database identity in the intended process environment; health alone does not prove target identity |
| Backend | `GMS_JWT_SECRET`, intended JWT lifetime | One privately provisioned value per variable; verify management login and invalid/missing authentication rejection |
| Backend | `GMS_MODEL_CREDENTIAL_ENCRYPTION_KEY` | Independently protected key matching any restored ciphertext; verify applicable stored owned-profile decryption, not merely key format |
| Backend, current Azure path | `AZURE_OPENAI_API_KEY`, endpoint, API version and deployment | Resolve the selected main/classifier roles and run the approved read-only acceptance |
| Backend, extra model profiles | Approved origins/base URLs and credential variable names | Review `GMS_ALLOWED_LLM_ENDPOINTS`, `GMS_ALLOWED_COMPATIBLE_LLM_ENDPOINTS` and `GMS_ALLOWED_LLM_CREDENTIAL_ENV_VARS` only as needed for actual profiles |
| Backend GitHub connector | Default PAT or approved per-app credential reference; `GITHUB_MCP_READ_ONLY=1` | Confirm connector links, reference-name approvals and actual safe tool invocation; do not broaden token permissions for acceptance |
| Frontend build | `NEXT_PUBLIC_API_BASE_URL=/api/gms` | Browser requests use the same origin; public variables contain no credentials |
| Frontend runtime | `GMS_API_BASE_URL=http://127.0.0.1:8000` in the agreed shared-network-namespace ACI layout | Proxy health and actual authenticated runtime requests pass |
| Images/network | Frontend listens on public 80; backend listens on private 8000 | Verify actual release image digests and deployed exposure; no Docker-style ACI port remapping assumption |
| Backend limits/debug | Existing single-process contract, intended limits, runtime debug disabled for normal release | Scaling beyond one process requires the separately recorded shared-limiter design; inspect logs/responses for secret omission |

`.env.example` contains duplicate JWT entries and development placeholders. Treat
it as a source of variable names to review, not a ready-to-deploy configuration.
No new secrets need to be generated for this worksheet. Preserve existing keys
with their data; use the agreed protected provisioning process for a new target.

## Schema/configuration rehearsal sequence

1. For this release, follow the fresh-database initialization in the release
   record: verify the exact new empty target, create current tables, seed the
   catalogue, bootstrap the supervisor and establish baseline global policy.
   This blank-target flow has passed a disposable PostgreSQL rehearsal. Do not
   restore old test data or apply all old migrations to make it fresh.
2. The following historical migration-review path applies only if scope later
   changes to an existing dataset: identify the target and controlled restored copy, then inventory
   their actual schema, app scope, effective policies/compiled artifacts and model
   selections/grants. Existing work schema checks remain accepted for that work
   rehearsal; they do not establish an unidentified production target.
3. Determine the exact required migration difference. Review the needed security
   foundation, model-grant and owned-main-model changes rather than executing all
   historical helpers. Preserve helpers' rehearsal-only restrictions.
4. Test the reviewed sequence on the controlled copy. Verify schema constraints,
   existing data compatibility, intended app membership/authentication, exact
   current policy artifacts, connector references and both selected model roles.
5. Record source revision, environment/backup identifiers, changed objects,
   acceptance results and rollback compatibility without recording secret values.
6. The user has authorized the fresh-database build/deployment. Preserve that
   scope and do not replace the existing database with a rehearsal. Actual Azure
   resource discovery/authenticated execution are still needed to carry it out.

## Target recovery and rollback sequence

1. Confirm the actual backup mechanism, storage/access and separate matching-key
   custody. The accepted synthetic dump/restore demonstrates application
   mechanics; verify the actual process and recovery access separately.
2. Restore an authorized appropriate backup into the agreed recovery environment.
   Verify records, app/model ownership, grants, policy assignments/artifacts and
   constraints. Inject the matching key privately and verify applicable stored
   owned-model decryption. If there are no owned profiles, state that scope
   explicitly rather than claiming a stored-profile recovery test.
3. Record recovery duration if a recovery objective is required; agree success
   criteria and custody responsibilities. Avoid including keys or raw sensitive
   dumps in reports, Git or chat.
4. Rehearse the selected prior-image/config rollback with its compatible schema
   and data plan. Do not assume changing image tags reverses database changes.
   Agree abort conditions and who executes recovery before the release window.

## Deployed acceptance sequence

After the authorized release pair is published/deployed: verify exact image
identities, intended public/private ports, proxy/API/database health, valid
management login, invalid app credentials rejected before runtime work, one safe
real tool read, one applicable block and matching Traffic/Audit evidence. Use
fresh conversations and expected policy scope; keep GitHub read-only.

New-provider acceptance is conditional on adding a provider/gateway. The user
explicitly permits release with the recorded dependency findings; compatible
remediation remains open.
The [automated home review](home-automation-review-2026-10-23.md) records the
current compatibility/advisory evidence; no production acceptance is inferred.
