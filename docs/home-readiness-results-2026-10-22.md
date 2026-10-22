# Home readiness follow-up results - 22 October 2026

Status: **all requested unconditional home checks passed**. The user requested
the remaining home-capable checks and reported committing/pushing the approved
patch. The verified source commit is
`5f84cffed834eb8c3d2bbd258e1b5b5e2f445a43` (`Bug fixes`, branch `main`).

## Results

| Check | Result |
| --- | --- |
| Hosted GitHub verification | Both backend and frontend jobs passed for the exact pushed commit |
| Hosted backend | Clean image build, 38 offline checks, 16 PostgreSQL diagnostics and migration/constraint/index/cascade checks passed |
| Hosted frontend | Locked install, ESLint, TypeScript and production build passed on pinned Node 24 |
| Rebuilt local backend | Latest committed application source baked into `gms-home-be:20261022-followup` |
| Local image offline suite | 38 passed, 0 failed; Docker networking disabled; no source overlay or private configuration mounted |
| Runtime consistency | 17 direct roots and 117 installed constrained packages match pins; UID 10001; runtime pip absent |
| Baked source identity | Both changed runtime modules match the approved/current source SHA-256 values |
| Plain live answer | Overall passed, Tool guard `not run`, no tool events |
| Actual branch read | Overall passed, Tool guard `passed`, one real `list_branches` invocation and all five expected branch names |
| Blocked issue-creation request | Input blocked, Tool guard `not run`, no tool events |
| PostgreSQL recovery | Real custom-format pg_dump/pg_restore into a new database passed after removing the disposable source database |
| Encryption-key recovery | Correct synthetic key decrypts restored credential; absent/wrong keys rejected; restoring correct key decrypts again |
| Restored relationships/schema | App model selection, main grant, policy assignment/label, compiled rule, conversation, owner FK, credential constraint and index preserved |
| Cleanup | All five owned containers and both test networks removed; existing home PostgreSQL remains healthy |

Hosted run: [Verification #39710898869](https://github.com/adibice1/nemo-mcp-guardrails-test/actions/runs/39710898869).
The frontend job is `119601718225`; backend job is `119601718437`. Job results
were independently read through the GitHub connector; its backend logs confirm
`Offline checks: 38 passed, 0 failed` and
`PostgreSQL diagnostics: 16 passed, 0 failed`, followed by successful cleanup.
The initial local CLI login returned 401; the existing project GitHub credential
was then supplied privately to a read-only CLI process. No login configuration,
credential scope, repository file or workflow run was changed by that lookup.

## Current local image

| Image | Identity |
| --- | --- |
| `gms-home-be:20261022-followup` | `sha256:264ca205571599c80c8e48d38c0237dd6c9e05763621d6433c59cdfde5780176` |

This is a new local image tag; the previously accepted image was retained. Docker
reused verified dependency layers and rebuilt the application layers. This local
rebuild is not a claimed new uncached dependency installation; the hosted backend
job independently passed its clean build. The matching local frontend image was
reused because its source did not change; the hosted frontend job rebuilt and
validated the committed frontend separately. Nothing was pushed to a container
registry or deployed by this follow-up.

## Live status smoke check

A fresh backend process from the new image and the previously accepted frontend
image shared a network namespace, exercising frontend port 80 -> loopback backend
8000 through `/api/gms`. These temporary services exposed no host ports. Checks
used a disposable app/admin, explicit default-model grants, a linked GitHub
connector and an issue-creation block policy. Azure main/classifier calls and the
bundled native GitHub MCP executable were real; `GITHUB_MCP_READ_ONLY=1` remained
set throughout. Each request used a fresh conversation ID.

| Request | ID | Tool guard | Tool starts |
| --- | --- | --- | --- |
| Plain greeting | `81cc0594e41f44b7ae16c7e6e27c1cb4` | `not run` | 0 |
| Existing branch names | `c1f0adb437b049589f1e7b09b701518f` | `passed` | 1 |
| Blocked issue creation | `3ab8d5e0112d489684416c223bdb581e` | `not run` | 0 |

The branch read returned development, feat/add-user-management, main, production
and staging. Traffic detail confirmed the actual tool and guard events; skipped
cases had `tool_guard.skipped` events. Requests took approximately 4.78 s, 4.85 s
and 2.25 s respectively. These are smoke samples, not the deferred work-network
cold/warm performance benchmark. No GitHub mutation ran.

This verifies the status payload that the existing frontend renders. It is not
a new browser screenshot/layout acceptance claim. Existing Windows server
processes were preserved; fresh temporary services loaded the changed code for
these checks. Any still-running older source process needs its normal restart
before it serves the saved source change.

## Backup and key-recovery rehearsal

Recovery used a separate synthetic database, independent of the live smoke
database. The fixture contained one app, an encrypted app-owned model, a main
grant, a selected model, a named policy assignment, a compiled policy and one
conversation message. A newly generated synthetic Fernet key encrypted only a
clearly synthetic provider-key string. Neither the user's real encryption key
nor any real provider credential was part of the recovery fixture or archive.

The PostgreSQL 16 container created a custom-format uncompressed archive. Checks
confirmed that neither the synthetic provider plaintext nor its encryption key
appeared in that archive. The disposable source database was then dropped and
the archive restored into a separate empty target database. Verification proved
record/relationship integrity, restored constraints/indexes and correct/wrong/
missing encryption-key behavior using the application decryptor.

The archive lived only in the test container's tmpfs `/tmp`; no database dump or
encryption key was saved in the workspace. This proves the current schema/key
mechanism on synthetic PostgreSQL data. It does not certify production backup
scheduling, offsite storage, access controls, actual key custody, a production
recovery time objective or an Azure cutover procedure.

## Isolation and evidence

All test container/network IDs came from this invocation's successful creates.
PostgreSQL used tmpfs and an internal Docker network, without a host port or a
persistent volume. Only the live backend received the existing Azure/GitHub
configuration by environment-variable name; no private values were printed.
Recovery workers received synthetic settings only. The test JWT/encryption keys
were synthetic, process-local and discarded with the resources.

The existing home database, stored app selections, root `.env`, real encryption
key and existing server processes were preserved. No production migration,
work policy repair, grant change or deployment ran. The user had already committed
and pushed the source; this follow-up adds documentation locally without making
another commit or push.

Private local evidence is under `.waylog/home-readiness-20261022/`: image
identity, offline log/exit, hosted CI metadata/job summaries, live status results,
synthetic recovery results and cleanup receipt. Harnesses there are local
verification artifacts, not additional registered regression tests; the shipped
catalogue remains 38 checks. They do not transfer through Git.

## Remaining work

The requested unconditional home checks are complete. Actual work-network Azure
timing/log evidence, policy 210 repair/app 214 validation and the app 221 unused
classifier-grant decision remain deferred. A new external provider/gateway still
needs a provisioned endpoint and credentials before live acceptance. Production
backup/key-custody review, rollout and deployment remain separate. The recorded
Pillow/FastEmbed and development braces findings are not remediated by these
checks. See [the remaining checklist](remaining-verification-2026-10-22.md) and
[the current backlog](open-work-backlog.md).
