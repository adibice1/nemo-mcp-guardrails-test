# Workday online execution and supervisor deployment - 23 October 2026

This supersedes the home-only preparation status in the earlier handoff. The
user authorized automation and approved fresh database `nemo_gms_release_20261023`,
reuse of work Azure/GitHub credentials and supervisor ownership. Hard stop is
15:00 Singapore time; **do not interrupt the existing service 11:30–14:00**.
Supervisor cannot perform Azure deployment in that window, so the agent prepares
the release and exact instructions for their later authenticated session.

## Completed online work

| Item | Actual result |
| --- | --- |
| Access | Work PostgreSQL admin connection verified; CREATEDB available. Registry login completed by user. No supervisor Azure subscription login is available to the agent. |
| Existing database | Existing deployment YAML points to `nemo_mcp_guardrails` on `guardrails-postgresql.postgres.database.azure.com`. It was not cleared, migrated or replaced. Rehearsal `nemo_restore_check_20261016` also preserved. These are configuration/SQL findings; actual running ACI identity is not authenticated. |
| Current backup | New custom-format archive of the current old online database captured, hash recorded and actually restored into a separate recovery database. Table sets, every table's row count and constraints match. Recovery database removed after verification; original databases unchanged. Owner/ACL replay was intentionally excluded from restore; operational role/config recovery remains separate. |
| Existing backup | Located `C:\Users\User\Downloads\nemo_before_security_migration_20261016.backup`; preserved and hashed. A new current archive was used for recovery validation rather than assuming the older archive is current. |
| Fresh database | Created and verified exact identity `nemo_gms_release_20261023`; 21 current tables, 2 connectors, 11 actions, 10 resources and 33 tool mappings. No old apps/users/history imported. |
| Supervisor account | One admin `admin@gmail.com` created with expiring setup password. User subsequently chose a replacement privately through the actual API. New admin login and setup-token invalidation pass. The chosen permanent password was not saved by the helper and is not in docs; user must hand it over privately. |
| Secrets | Independent new signing/encryption secrets generated privately for the fresh dataset. Root work `.env` and old keys preserved. Current work provider/GitHub credentials reused as authorized. |
| Images | Both Linux AMD64 images rebuilt on work machine. Backend's 117 installed constrained packages match pins; baked source hashes match checkout; backend UID 10001 and frontend UID 1001. Frontend login page returns 200. |
| Offline checks | All 38 groups pass across initial 37 passing checks and the single contract recheck. Initial contract invocation lacked its required read-only Dockerfile fixture; supplying that fixture passes unchanged. No application fix or weakened assertion was involved. |
| Registry publication | Matching pair published under new `fa76f78ba62d-work20261023` tags and inspected by digest. Existing `latest` tags untouched. These work-build identities supersede home-local identities for this published pair. |
| Fresh platform baseline | Mandatory global credential-output policy created through normal admin API and globally assigned. Disposable acceptance apps receive explicit main/classifier grants, connector links and app-policy assignments; no blanket approvals were seeded. |
| Image-pair read | Real loopback frontend proxy + native-MCP backend image pair using the fresh online database passes health, authenticated admin access, invalid app-key rejection and actual branch read with all stages passing plus `list_branches` start/return events. |

## Published release identities

| Component | Registry tag | Published digest |
| --- | --- | --- |
| Backend | `guardrail.azurecr.io/guardrail-be:fa76f78ba62d-work20261023` | `sha256:825d7e9a34883ca6950079f3ecea1c2451f84d66c0d5a1258b5503741ae8863e` |
| Frontend | `guardrail.azurecr.io/guardrail-fe:fa76f78ba62d-work20261023` | `sha256:7956e28052ebca8b763ecf281ed1c30d0044ca7ccbc677b177bc3911411d74f0` |

Application build inputs match `fa76f78`; current checkout `bdc5c2030563` adds
guides/documentation. Unlike the home rebuild, these work images have different
image IDs and received package/source/role/offline/live checks of their own.
Publication is complete; **actual ACI deployment is not**.

At inspection, registry `latest` digests were backend
`sha256:283bddbc72090613215d44b7cd5ffe6d4d83c55e4a402d0753fa7260b67867c0`
and frontend `sha256:cc8b068d2cb50098d7c11a3dfc2467edaf5aa14f65b523bd21a1c5c1d8859a46`.
They are candidate previous-registry references, not proof of actual running
ACI digests. Capture the actual deployment before any update.

## Runtime finding that must stay visible

The first exact-title acceptance request (`gms-release-blocked-test`) **did not
input-block**. Request `a7322a3b0fb34582ba9442a8acff6861` passed input, attempted
read-only `list_issue_types` and returned a controlled tool error. No GitHub write
occurred. This does not pass the expected input-block/no-tools criterion, and is
retained in the acceptance receipt. Additional focused classifier/scope diagnosis
is separate evidence; do not replace this failed observation with a successful
retry or call it a read-only policy-block success. No classifier/code change is
silently applied to make the check pass. The mandatory output baseline remains.

Focused follow-up: exact title `test` also passed input (request
`248ec121a1cc4f6ba18fcba502063ec0`); its response reported one input policy and
one input rule, and its stored artifact was active/current. A broad issue-create
restriction then blocked at input (request `fbd5d75bc767422b8bc2de9d1251a40d`),
with zero tool starts independently verified. Its policy update correctly
disabled/staled version 1 and activated version 2. Both diagnostic app/policy
were removed. These observations narrow the issue but do not prove its root
cause. Preserve title-scoped classifier false negatives as an open finding;
offline execution-binding tests still pass, but no live write bypass was tested.

The initialized fresh database now has exactly one admin (password setup cleared,
no setup expiry), zero apps, zero LLM profiles and one globally assigned baseline
output policy. New management audit/acceptance telemetry may remain deliberately;
no historical old-database records were imported.

## Database names versus backup files

A read-only account check after preparation distinguishes these databases on
the same existing Azure PostgreSQL server:

| Database | Observed account/data scope |
| --- | --- |
| `postgres` | No GMS `public.users` table; the supplied connection's database selection does not identify the application dataset. |
| `nemo_mcp_guardrails` | Original application dataset, six accounts; all three existing account names the user asked about are present and enabled. |
| `nemo_restore_check_20261016` | Restored rehearsal/testing copy with subsequent work, seven accounts; the same three named accounts are present and enabled. It is a live database copy, not an archive file. |
| `nemo_gms_release_20261023` | Fresh release dataset, one account: `admin@gmail.com`. Its replacement password is independent of same-email accounts in the older databases. |

The original application backup and the rehearsal backup represent different
datasets. Preserve both separately; do not describe the original application's
archive as containing later rehearsal-only models/policies/users. No old accounts
were deleted or reset, and no old dataset was imported into the fresh release.
The current rehearsal archive was separately captured using an exported consistent
snapshot and actually restored/verified at 14:05 Singapore time. It preserves
seven users, six apps, two model profiles, 53 policies, 15 app assignments and
16 model grants, alongside the remaining tables. All table sets/row counts match;
the same known-equivalent purpose-constraint cast normalization was observed.
There are zero encrypted owned profiles, so stored-profile decryption was not
applicable. Only the owned temporary recovery database was removed. The live
rehearsal and fresh release data were not changed or merged.

Archive: `nemo_restore_check_20261016_handoff_20261023.backup`, 153961 bytes,
SHA-256 `b241143b3aac0f2b23519f2335bdb58501a452032c07040b23c0b6b3b6b71df6`.
This is included in the private handover folder/manifest, in addition to the
original-application and initialized-fresh-release archives.

## Private artifacts to hand over

Current work-machine directory:
`C:\Users\User\Downloads\nemo-mcp-guardrails-test\.waylog\release-access-20261023\private`.
This directory is Git-ignored and contains real secrets/data; **do not commit it**.
Protected final storage and actual supervisor receipt are still unconfirmed.

- `aci-release.private.yaml`: proposed combined frontend/backend ACI definition,
  digest-pinned, new database/key settings, backend credential entries using
  `secureValue`, GitHub read-only and frontend proxy via shared localhost.
- `release-settings.env`: JSON configuration record despite its extension;
  contains actual database/signing/encryption/provider secrets. The supervisor
  must preserve the matching release keys privately.
- `nemo_mcp_guardrails_before_release_20261023.backup`: verified current old-data
  archive; preserve old configuration and any matching keys separately.
- `previous-config/fe-config.yaml`, `be-config.yaml`, `command.txt`: untouched
  copies of supplied first-deployment files. These contain credentials too.
- `nemo_gms_release_initialized_20261023.backup`: initialized fresh dataset,
  actually restored and verified after disposable-app cleanup.
- `nemo_restore_check_20261016_handoff_20261023.backup`: current rehearsal copy
  with later test/configuration work, independently restored/verified.
- `legacy-work-key.env`: preserved old work key, kept distinct from new release
  settings. Do not substitute it for the fresh dataset's encryption key.
- `README-HANDOVER.txt` and `handover-manifest.json`: private transfer instructions
  and required-file sizes/SHA-256 hashes. No permanent admin password is included.

Transient database access, admin-session and Docker env files were removed after
verification. The permanent password belongs to the user/supervisor, not these
artifacts. Keeping backup and keys temporarily in one working area
does not establish the final separately protected custody or transfer acceptance.

## Final verification and cleanup - 11:50 Singapore time

The new initialized archive is 110756 bytes, SHA-256
`69bb09a5380fab0beaa5f36db228d8e6f691eb33342302a794d13004a1a81a4b`.
Its restored table sets and every row count match. All other constraint
definitions match exactly; PostgreSQL normalized the purpose-check's array casts
to an equivalent expression. On the restored copy, invalid purpose `other`
raises check violation 23514; `main`/`guardrail` pass that check and reach the
deliberately missing-app foreign-key rejection 23503. This validates behavior
rather than treating the deparser's textual difference as corruption. Restored
admin identity/password-setup state and its signed-session compatibility pass.
No owned profiles exist, so actual owned-profile decryption is not claimed.
The owned recovery database was removed. Owner/ACL restoration was not exercised.

Final SQL inspection confirms: one user, zero apps/profiles/app assignments/
grants/connector links, one enabled global output policy with one matching active
compiled artifact. Twenty new management audit rows and four new runtime records
remain as preparation evidence; no old history was imported. Both original
databases remain, and neither owned temporary recovery database remains.

The isolated operator API on 8010 and both temporary acceptance containers on
3020/8020 were removed after verification; pre-existing processes/containers were
untouched. Private temporary `database-access.env`, `admin-session.env` and
`docker-release.env` were deleted. The needed private configs/backups/key copies
and hash manifest remain for protected transfer. Original Downloads YAML/commands
and root `.env` were not rewritten. Registry credentials in the prepared YAML
also passed an isolated login check; its temporary credential record was removed
without changing the user's global Docker login.

Credential-free checks of the existing public `/login`, `/api/gms/health` and
`/api/gms/health/db` return 200. No ACI create/update/restart/delete was executed.
The public site still runs the prior deployment/database; the newly chosen admin
password belongs to the fresh dataset and should be used there after cutover.
Actual deployment/rollback rehearsal and supervisor protected receipt remain
unverified. Known dependency findings and the new classifier finding remain open.

## Why the supervisor cannot only change two image tags

The supplied original YAML describes **two separate public groups**, frontend
`64aiguardrails-fe` on 80 and backend `64aiguardrails-be` on public 8000. Its
frontend uses the backend public FQDN and its GitHub setting enables writes.
The prepared current-release definition instead puts both containers in one
group, exposes only frontend 80, uses backend loopback 8000 and keeps writes off.
The proposed group/name/DNS comes from the supplied frontend file; authenticate
and reconcile actual Azure resource identity before applying it.

All containers in an updated ACI group restart, and some topology/resource
changes require replacement. Preserve the old group/configuration and agree the
cutover/rollback window; **no blind deletion/recreation command is supplied**.
See [Microsoft's update limitations](https://learn.microsoft.com/en-us/azure/container-instances/container-instances-update),
[YAML port contract](https://learn.microsoft.com/en-us/azure/container-instances/container-instances-reference-yaml)
and [secure environment values](https://learn.microsoft.com/en-us/azure/container-instances/container-instances-environment-variables).
The private YAML itself still contains secrets even when Azure hides secureValue.

## Supervisor commands and deployment sequence

Use the supervisor's own Azure login on a machine with the privately transferred
YAML. Registry admin credentials alone cannot update ACI. No image rebuild or
push is necessary when deploying the published digests above.

```powershell
az login
az account show --query "{name:name,id:id}" --output json
$gmsResourceGroup = '64aiguardrails'
az container list --resource-group $gmsResourceGroup --query "[].{name:name,fqdn:ipAddress.fqdn,images:containers[].image,state:provisioningState}" --output json
```

Confirm the intended subscription/resource group/container names. Capture actual
old images, networking, deployment configuration and private secret references
for rollback before making changes. The supplied YAML is historical evidence,
not an authenticated export. Existing keys/secret values may not be recoverable
from an export; keep the private configuration copies and agreed protected store.

Then inspect the privately supplied release YAML: verify fresh database name,
new keys, published digests, intended group/DNS and the one-public-port layout.
Only after reconciling the actual existing layout and cutover plan:

```powershell
$gmsReleaseYaml = Read-Host 'Full protected path of aci-release.private.yaml'
if (-not (Test-Path -LiteralPath $gmsReleaseYaml -PathType Leaf)) { throw 'Release YAML not found' }
az container create --resource-group $gmsResourceGroup --file $gmsReleaseYaml --query "{state:provisioningState,fqdn:ipAddress.fqdn,images:containers[].image}" --output json
```

This command is a real deployment and can restart/replace service. If Azure
rejects an in-place layout/resource update, stop and use the operator's planned
replacement sequence; do not improvise deletion or change to public backend
8000 simply to bypass the error. An agreed temporary group/DNS can validate the
new pair before a separately planned production DNS/name cutover if needed.

After deployment, verify the actual returned FQDN, database and image identities:

```powershell
Invoke-RestMethod 'http://guardrails-fe.southeastasia.azurecontainer.io/api/gms/health'
Invoke-RestMethod 'http://guardrails-fe.southeastasia.azurecontainer.io/api/gms/health/db'
```

Use the actual FQDN instead if the agreed cutover changes it. Health alone does
not establish the database name or image digest. Confirm those from the actual
backend/operator environment without displaying a full connection string.
Sign in with `admin@gmail.com` and the privately chosen replacement password.
Verify administration, auth rejection, an intentionally configured disposable
app's real safe read, applicable policy block and corresponding Traffic/Audit.
Use fresh conversation IDs and normal read-only GitHub mode. The classifier
finding above needs explicit review; do not mark every blocking case passed.

After acceptance/cutover, retire the old separately public backend if it remains
running; the new backend is inside the combined group. Preserve its old database
and rollback configuration. Do not stop a group based on a guessed resource name.

Finally verify supervisor receipt of password/configuration/backup and keys,
their independent Azure/registry/PostgreSQL access, and the reviewed rollback
procedure. HTTP ingress and the recorded dependency findings remain unresolved;
the user's release disposition for those findings is preserved. Actual deployed
acceptance, final custody and supervisor guide review are not completed by this file.
