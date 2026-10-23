# Final workday handoff and second deployment - 23 October 2026

## Later work-machine execution

Read [the actual online execution and supervisor deployment record](workday-online-execution-2026-10-23.md)
first. The fresh online database/admin now exist, the user completed password
replacement, the current old database backup was restored/verified, and the
work-built pair is published under versioned tags. Actual ACI deployment remains
pending supervisor Azure access. A focused input-classifier acceptance finding
is retained there. The earlier home-preparation statements below describe that
checkpoint only and no longer mean online provisioning/publication is pending.

This is the current release decision record. The user says the next working day
is their last and wants online-database work finished while work access is still
available. It supersedes the earlier questions about carrying legacy rehearsal
apps into production. The user has now supplied SE-EDU templates; the Markdown
[User Guide](UserGuide.md) and [Developer Guide](DeveloperGuide.md) follow them.

## Confirmed decisions

| Item | Decision/state |
| --- | --- |
| Azure target | Keep the existing deployment environment; this will be its second deployment |
| Existing public URL | `http://guardrails-fe.southeastasia.azurecontainer.io` |
| Registry | `guardrail`, login server `guardrail.azurecr.io`; registry username supplied as `guardrail` |
| Database | Use a fresh database/data set, not the old test apps/users/policies/history; preserve the old database separately |
| Old apps 208/214/222 | No carry-over requested; their previous grant/classifier/HTTP questions do not block a fresh release |
| First GMS system administrator | Supervisor; initial email/username `admin@gmail.com`, display name can be edited later |
| Ownership | Supervisor takes over release, administration, secrets/key custody and recovery after handover |
| Backup | User has an existing backup and intends to transfer it privately to the supervisor; actual transfer/integrity/matching-key coverage still need confirmation |
| Release findings | User explicitly said release may proceed with the recorded dependency findings; they remain unresolved, not fixed or independently security-cleared |
| Current ingress | HTTP; no TLS/domain change was requested or implemented here |
| Guides | Markdown UserGuide.md and DeveloperGuide.md written using supplied SE-EDU structures; supervisor review remains |

The GMS `system_role=admin` is the application's administrator role. It does not
grant Azure subscription, registry or PostgreSQL administrator permissions.
Knowing the registry username does not establish a registry login.

## Prepared release pair

Both Linux AMD64 images built successfully from source commit
`fa76f78ba62d9fff6d97c6587a61b9984a373955` (`More security tests`). Their image IDs
are identical to the previously accepted images, so existing image/offline/live
evidence remains applicable; no identical 38-check rerun was needed.

| Component | Local tag | Image ID |
| --- | --- | --- |
| Backend | `guardrail-be:fa76f78ba62d` | `sha256:264ca205571599c80c8e48d38c0237dd6c9e05763621d6433c59cdfde5780176` |
| Frontend | `guardrail-fe:fa76f78ba62d` | `sha256:62e046cf517d5d9eebfc9f697a40ab49d3cd578ffa5c49b4a26ef01fd2279779` |

Intended remote tags are `guardrail.azurecr.io/guardrail-be:fa76f78ba62d` and
`guardrail.azurecr.io/guardrail-fe:fa76f78ba62d`. **They are not published by this
session.** A read-only registry manifest request returned authentication required.
Do not describe local image IDs as published registry digests or assume a
registry's latest tag identifies the running first deployment.

Azure CLI was not installed at the checked home locations, and browser automation
failed to initialize its runtime. No authenticated Azure deployment session was
available. Building/publishing/deploying is authorized by the user's request;
the current publication/deployment blocker is missing authenticated access and
actual resource discovery, not a new request for general permission.

## What the connection checks establish

Unauthenticated checks against the supplied deployed URL returned:

| Endpoint | Result |
| --- | --- |
| `/login` | HTTP 200 |
| `/api/gms/health` | HTTP 200, status ok |
| `/api/gms/health/db` | HTTP 200, database reachable |

The existing deployed backend can therefore reach its configured database from
its own environment. These health responses do not reveal/verify that database's
name, the running image version or the resource-group/container configuration.
Those details must be captured from an authenticated work/Azure session.

The home direct-DB probe resolved
`guardrails-postgresql.postgres.database.azure.com` to public IPv4
`20.104.96.171`, but the TCP connection to port 5432 timed out before PostgreSQL
TLS/authentication. No database credentials, SQL or configuration changes were
used. Do not diagnose this as a wrong password or weaken TLS based on that result.
The user reports that the supervisor allowed all IPs; actual networking mode and
firewall rule ranges have not been inspected in this session.

[Microsoft's networking guidance](https://learn.microsoft.com/en-us/azure/postgresql/network/concepts-networking-public)
requires client/network outbound TCP 5432 as well as the server's applicable
network access. Its [firewall guidance](https://learn.microsoft.com/en-us/azure/postgresql/security/security-firewall-rules)
distinguishes public IP rules from Azure-service access. At work, check the actual
public/private mode, DNS and rule ranges; compare a bounded TCP probe from work
and home/an alternate connection if direct home SQL access is still desired.
Do not broaden rules again merely because a home timeout occurred.

The deployed website is reachable from home, so ordinary GMS use can go through
its frontend/backend without opening a direct laptop-to-database connection.
Public HTTP remains a transport-security limitation for passwords/provider keys;
no secure-public-ingress claim is made by these health probes.

## Fresh-database initialization

Fresh means no legacy demo app IDs, old user accounts, selected-model grants or
history are copied into the new database. Required platform baseline data is
still necessary:

1. Create a new named database on the agreed online server and verify its exact
   identity and emptiness. Record the name; never clear the existing database
   to simulate a fresh one.
2. Initialize the current schema from the current model metadata. API startup
   calls `create_all`; that creates missing tables for a blank database and is
   not a migration mechanism for upgrading arbitrary old schemas. Do not run
   every historical migration against the fresh target.
3. Seed the existing connector/action/resource/tool catalogue using
   `scripts/seed_normalized_policy_metadata.py` from the checked-out work source.
   That helper seeds metadata, not the first administrator or all policies, and
   is not bundled into the normal runtime image.
4. Bootstrap exactly one intended supervisor system-admin account through the
   controlled database/operator path. Public signup is disabled and management
   user creation already requires an authenticated administrator. Use the
   existing password hasher, a privately generated temporary password, forced
   replacement and its existing 24-hour expiry; never put the password in Git,
   a command-line history, build arguments or this document.
5. Establish the platform's mandatory global credential-output policy through
   the normal administrative path after initial password setup. Do not copy
   unrelated old app-specific policies as an implicit default.
6. New apps still need deliberate selected-model approval for both roles,
   enabled connector links and appropriate policy assignments before runtime.
   A fresh database does not automatically grant every model/connector.

A new disposable PostgreSQL rehearsal of the current images passed: blank schema,
metadata seed, first-admin forced setup, password replacement, setup-token
revocation, real system-admin access and global credential-policy creation. It
contained no imported old app/profile data and was fully cleaned up. This was a
synthetic account/ASGI/PostgreSQL rehearsal; **the real supervisor account and
fresh online database have not been provisioned**.

For a genuinely fresh production data set, provision its independent model-key
configuration privately under supervisor custody. Preserve home/work keys with
their own backups; importing encrypted records later requires their matching
key. Do not overwrite a home/work key to perform this release.

## Priority sequence while work access remains

Current work-machine access collection is in the
[manual access intake and copyable commands](workday-access-intake-2026-10-23.md).
Azure CLI is installed at work but not logged in; Docker responds and only
`latest` release tags are listed locally. PostgreSQL 18 tools and the venv exist.
The user requested collection of manual inputs before automated provisioning;
no database/deployment changes ran for this access preflight.

1. **Capture the existing deployment before changing it.** From an authenticated
   supervisor/work Azure session, discover subscription, resource group, actual
   container-group/service name/layout, current image references/digests and
   database identity. Preserve runtime configuration/secret references privately
   for rollback. Health alone is insufficient. Never commit an Azure export that
   contains secrets; redacted exports may also be insufficient to recreate them.
2. **Create and bootstrap the fresh database.** Complete the sequence above and
   have the supervisor complete their first password replacement. Verify their
   access to administration while work access is still available.
3. **Publish the prepared pair and update the existing deployment.** Use the
   new database only for the replacement release, retain the old database and
   previous image/config identities for rollback, and keep the same frontend
   proxy/private-backend contract. Inspect the actual existing layout before
   assuming its two containers currently share localhost.
4. **Run the narrow deployed acceptance.** Verify exact new database/image
   identities, health, supervisor login, authentication rejection and one
   appropriately configured temporary app's safe read/applicable block/logs.
   Keep GitHub read-only and remove temporary app-specific acceptance data as
   appropriate. Do not claim policy blocking based only on MCP read-only refusal.
5. **Complete private operational handover.** Transfer/verify the existing backup,
   applicable matching keys, secret/config custody, Azure/registry access and
   rollback instructions with the supervisor. Record their receipt without
   including secret values. A promised future backup transfer is not a verified
   transfer or a completed restore test.
6. **Review and hand over the two guides.** The supplied SE-EDU templates have
   been applied to the Markdown User Guide and Developer Guide. Check the final
   deployed URL/setup against them after rollout and hand them to the supervisor.
   Do not mark online acceptance complete merely because the guides are written.

## Work-side commands that need an authenticated Azure session

These are preparation/discovery/publication examples, not commands executed here.
Use the supervisor's normal authenticated process; do not paste registry/Azure
passwords into chat or store them in these commands.

```powershell
az account show --query "{subscription:id,name:name}" --output json
az container list --query "[?ipAddress.fqdn=='guardrails-fe.southeastasia.azurecontainer.io'].{name:name,resourceGroup:resourceGroup,id:id,images:containers[].image}" --output json
az acr login --name guardrail
docker tag guardrail-be:fa76f78ba62d guardrail.azurecr.io/guardrail-be:fa76f78ba62d
docker tag guardrail-fe:fa76f78ba62d guardrail.azurecr.io/guardrail-fe:fa76f78ba62d
docker push guardrail.azurecr.io/guardrail-be:fa76f78ba62d
docker push guardrail.azurecr.io/guardrail-fe:fa76f78ba62d
```

The images are local to this home computer; these tag/push commands need those
images on the machine executing them. At work, rebuild the same checked-out
source first or transfer images through an agreed channel. Azure Cloud Shell
does not automatically have this laptop's Docker images. Use
[the documented build commands](containerisation.md#build-directly) with the
commit-specific tags above. Update the real Azure group only using its verified
configuration and privately provided secrets; the FQDN alone is not a complete
deployment definition.

## Model support clarification and guide deliverables

The [supported-model setup guide](supported-llm-setup-guide.md) explains connection
recipes across providers. The product executes direct Azure or compatible chat
APIs; a gateway can translate other native protocols. A supervisor/developer can
add appropriately served models without a new GMS adapter when that contract is
met. Provider/model availability, a valid model ID, backend endpoint approval and
credentials are still required.

Registration alone is not role acceptance: a main agent must handle tool calls
and results, a classifier must return reliable complete decisions, and policy
authoring has its own structured-output requirements. Specialist rails and native
protocols marked EXTRA INTEGRATION are not automatically enabled by adding a
profile. The project does not claim every model/provider recipe was live-tested.

The User Guide covers first login/password setup, admin vs developer access,
apps/connectors, policy configuration, model profile/selection, Runtime Test,
Traffic/Audit and recovery/support ownership. The Developer Guide covers
architecture/setup, fresh bootstrap, app authentication and `/run`, model protocol
contracts, encryption/endpoint approvals, tests, image/deployment configuration
and handover operations, with the supplied template's design and requirements
appendices. Both use original GMS content and label pending deployment work.

Guide checks: both Markdown documents rendered successfully; all 81 links resolve
to existing local files/heading anchors or the attributed external template URLs.
Both fenced JSON examples validate against current request schemas, and the
client Python example parses. Four Mermaid diagrams received source review;
they were not graphically rendered in this session. These are documentation
checks, not live model/API/deployment runs. Private review output is under
`.waylog/guide-review-20261023/`.

Local evidence is under `.waylog/final-handoff-20261023/` (build IDs, public-health
probe, credential-free connectivity probe and disposable fresh-start results).
No application source, private settings, existing online/home database or live
Azure resource was changed. No publication/deployment or first-supervisor login
is claimed by this preparation.
