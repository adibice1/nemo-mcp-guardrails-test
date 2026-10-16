# Security Review Completion Report - 2026-10-16

The user authorized autonomous local implementation of patches 010-018, without
per-diff approval. Earlier work was preserved. These patches are implemented;
final verification is recorded below. No production migration, credential change,
image publication, deployment or live Azure/GitHub request was performed.

## Implemented changes

| Patch | Result |
| --- | --- |
| 010 | Next.js 16.4.2, React/React DOM 19.3.1, matching React types, reproducible npm lockfile, async route parameters and current flat lint configuration. Production transitive PostCSS, nanoid and source-map fixes are pinned. |
| 011 | All frontend stages use the same digest-pinned Node 24.21.0 Alpine image. Non-root UID 1001, port 80 and NET_BIND_SERVICE remain intact. Node types target 24. |
| 012 | Thread-safe sliding-window limits for login, password change/reset and policy AI. At most 10,000 hashed keys; active entries are never evicted to admit an attacker-controlled key. Capacity exhaustion fails closed. Forwarded IP headers are not trusted. |
| 013 | Admin-created/reset passwords expire in 24 hours. Setup JWTs last at most ten minutes and allow only identity lookup/password replacement. Atomic replacement clears setup state and revokes prior sessions. `/setup-password` reuses the existing change-password form. |
| 014 | Raw body cap of 512 KiB in both proxy and API; 16,000-character messages; at most 32 supplied history turns and 64,000 aggregate history characters; conversation IDs at most 200 characters. Control/null validation avoids DB failures. The execution coordinator has a 120-second timeout. History reads use a bounded indexed tail and bounded content projection. Validation responses do not echo inputs. |
| 015 | Membership backfill requires one exact user/app pair, previews by default and mutates only with `--apply`. Disabled users and unauthorized apps reject; existing memberships remain unchanged. |
| 016 | Sixteen direct Python roots plus exact transitive constraints. Eight unused provider-only distributions removed. Mandatory NeMo embedding dependencies remain. Sixteen vulnerable distributions received compatible published fixes, with the required LangChain core/graph updates. |
| 017 | Removed the unmounted LLM-settings component, empty helper package, tracked compiler state and generated error log. Added narrow generated-file ignores. Manual diagnostics were retained. |
| 018 | `scripts/run_security_checks.py` runs an explicit 31-check catalogue. It strips inherited credentials, disables dotenv, defaults to disposable SQLite, blocks external sockets and excludes live/database scripts from discovery. `--list` classifies retained diagnostics. Container proxy checks use a fake upstream and no external network. |

Each boundary has one implementation: one limiter, one password-change operation,
one raw-body middleware, one schema rollout helper, one scoped membership helper
and one explicit regression entry point. Existing policy compilation/enforcement
and separate main/guardrail model selection remain covered by the combined suite.

## Verification

- Windows: 31 offline diagnostics passed against the patched Python libraries.
  New authentication changes also passed the focused password/security checks.
- Linux: all 31 diagnostics passed with networking disabled and source/fixtures
  mounted read-only. The first run passed 30; the tool-contract check needed the
  root Dockerfile mounted as a fixture and passed after that correction.
- Frontend: whole-project TypeScript and full lint passed. Final Next.js 16
  production image built successfully on Node 24. Its isolated smoke test passed:
  non-root capability/port 80, six pages, encoded asynchronous proxy routes,
  fake bearer/app-key forwarding, body rejection before upstream work and manual
  redirect handling.
- Backend: clean Linux dependency installation, final image build, non-root
  startup imports, removed-provider checks and `pip check` passed.
- Python constraint audit: no known advisories after the published fixes. This is
  a package-version advisory check, not an OS-image or exploitability certification.
- npm production audit: zero findings. Full development audit: seven high entries,
  all downstream of the single unpatched `braces` advisory described below.
- Disposable PostgreSQL 16: real backend HTTP startup, login, admin-created
  temporary passwords, setup-only restrictions, password replacement and session
  revocation passed. A committed reset defeated a stale password update. The
  schema helper ran twice against a legacy schema without changing passwords.
  This tested one reset/update interleaving, not concurrency load or stress.
- All Python files parsed. SQLite also verified schema-helper idempotency and
  the scoped tail query's composite-index plan. Test PostgreSQL used tmpfs storage
  on an internal Docker network with no published ports. Its containers/network
  were removed after verification; no existing database was used.

The safe default command is:

```powershell
.\.venv\Scripts\python.exe -B scripts/run_security_checks.py
.\.venv\Scripts\python.exe -B scripts/run_security_checks.py --list
npm.cmd --prefix frontend run lint
```

The runner never invokes real database/MCP/model diagnostics. Those retain their
separate documented manual opt-in commands. Do not replace this command with
unrestricted test discovery. One Starlette warning notes that its optional
httpx-based TestClient adapter is deprecated; the current checked adapter works.

`scripts/check_frontend_container.cjs` is the isolated frontend image check.
`scripts/check_backend_container.py` is a separate opt-in PostgreSQL/HTTP check:
it requires an explicitly disposable, dotenv-disabled `reviewdb/review` database
and refuses to seed one containing users. It is excluded from the default runner
and must never be pointed at an existing deployment.

## Rollout requirements - not executed on production

1. Back up/review the target PostgreSQL deployment and apply
   `python scripts/migrate_security_foundation.py --apply` **before** the new API
   image. Running the helper without `--apply` prints the plan without connecting.
   It adds `users.must_change_password`, `users.temporary_password_expires_at` and
   `ix_conversation_messages_scope_tail`. Existing passwords are preserved and
   existing users are not forced into setup. Older management sessions must sign
   in again because JWT purpose/version checks have changed.
2. Keep the earlier app-model-grant rollout and reviewed legacy-policy repair /
   compiled-rule resync from patches 008/009. This run does not silently grant
   access, rewrite policies or execute those operations.
3. Deploy a matching reviewed frontend/backend pair. Keep frontend public 80,
   backend private 8000 and the same-origin proxy. Browser interaction, hosted
   database, real Azure classification and live MCP catalogue checks remain open.
4. The limiter matches the current single-process backend. Limits are per process:
   login 10/account/5 minutes, password change 20/user/15 minutes, password reset
   10/admin/15 minutes, policy AI 60/user/5 minutes. Each operation also charges a
   peer bucket of at least 60 attempts in the same window. The same-origin proxy
   shares a transport peer bucket. Uvicorn is explicitly started with proxy-header
   trust disabled. Multiple workers/replicas require a shared gateway/store limit
   before scaling; no distributed enforcement is claimed.
5. Runtime timeouts cancel local awaiting work; they do not roll back a remote
   connector operation already accepted. Normal GitHub operation remains read-only.
   Stored history is a bounded suffix, and oversized legacy turns/older context
   can be omitted with `history_truncated` set. No history is silently reinterpreted
   as a new client bootstrap when stored rows exist.

Targeted membership preview/application now uses explicit IDs:

```powershell
python scripts/backfill_existing_app_users.py --user-id 12 --app-id 34
python scripts/backfill_existing_app_users.py --user-id 12 --app-id 34 --apply
```

## Remaining upstream/tooling limitations

`braces` 3.0.3 has no published fixed version. It is reached through development
lint/CSS tooling (seven npm audit entries reflect that dependency chain), not the
production dependency tree. Build only trusted source/configuration and do not
expose development servers. It remains an explicit upstream follow-up, rather
than a claimed fix or a forced incompatible package substitution.

The bundled Next lint plugins still declare ESLint 9 compatibility. ESLint
9.39.5 is retained with passing checks; ESLint 10 produced unsupported peer ranges.
ESLint 9 is now marked unsupported by its publisher, so plugin compatibility and
the tooling upgrade remain a maintenance follow-up. The new performance-oriented
`set-state-in-effect` rule is disabled explicitly to preserve existing mount-time
auth/preference hydration; other hook/correctness rules remain enabled. This run
does not refactor every management screen during a security dependency update.

NeMo still requires fastembed, annoy, onnxruntime, community integration, pandas
and their closure. Removing them on import-count evidence alone would break a
clean install. WebSockets remains required by the patched LangGraph SDK and is
pinned to the clean Linux resolver's version. The removed packages are filetype,
google-auth, google-genai, langchain-google-genai, langchain-ollama, ollama, pyasn1
and pyasn1_modules. The existing virtual environment may retain such previously
installed extras; the clean backend image verifies they are not installed by the
new requirements. No unrelated environment-wide uninstall was performed.

Sources checked on 2026-10-16:

- [Next.js October security release](https://nextjs.org/blog/nextjs-security-update-october-14-2026)
- [Node release schedule](https://github.com/nodejs/Release)
- [PostCSS maintained advisory](https://github.com/postcss/postcss/security/advisories/GHSA-fxqj-rqcc-2cmp)
- [Unpatched braces advisory](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm)
- [PyJWT options-reuse advisory](https://github.com/jpadilla/pyjwt/security/advisories/GHSA-gvp8-978c-rx2q)
- [Starlette form-limit advisory](https://github.com/Kludex/starlette/security/advisories/GHSA-82w8-qh3p-5jfq)
- [MCP session-reclamation advisory](https://github.com/modelcontextprotocol/python-sdk/security/advisories/GHSA-84m7-p3x7-pcfv)
- [LangChain path-handling advisory](https://github.com/langchain-ai/langchain/security/advisories/GHSA-gr75-jv2w-4656)

The original security-review patches are implemented locally. Remaining items
above are deployment verification or explicitly unresolved upstream maintenance;
this is not a claim that the application cannot fail or has no security risks.
