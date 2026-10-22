# Automated verification application record - 22 October 2026

Subsequent follow-up: the user committed/pushed this source, both hosted CI jobs
passed, and the new local backend image plus live status and synthetic recovery
checks passed. See [the latest results](home-readiness-results-2026-10-22.md).

Status: **approved and applied**. After reviewing the tested patch contents, the
user approved application with "ok". All ten saved files match the tested
candidate SHA-256 values. The applied offline catalogue now has **38 checks**,
including tool-status regressions, a synthetic policy 210 rehearsal, and
disposable-runner ownership/cleanup checks. Five affected checks pass again from
the actual project source, with exit 0.

The preview and its original manifest remain isolated under
`.waylog/automation-preview-20261022/` as historical evidence. Application and
verification receipts record the subsequent applied state. Previous completed
home acceptance remains valid; this follow-up does not require replaying its
manual tests. Running service processes and previously built images were not
restarted/rebuilt as part of this local source application.

## Exact review artifact

- [Ten-file patch](../.waylog/automation-preview-20261022/automated-verification.patch)
- [Base/candidate hashes and patch digest](../.waylog/automation-preview-20261022/manifest.json)

Patch SHA-256:
`d09c0f1d1522f3bfc3aab6f5a7ff7f925574fbeb61f3de27d23bb3df35ff02a3`.
The application helper checked the patch digest and every base/candidate hash
before applying. Git converted some line endings while applying; the resulting
text matched the candidate and files were aligned to the exact approved bytes.
All ten final hashes match. The original manifest intentionally retains its
pre-application status; `application-receipt.json` records the applied state and
`applied-verification.json` records the five passing affected checks.

These private artifacts are ignored by Git; this document preserves the review
summary for handover. No commit/push, hosted CI run, work policy repair or
deployment ran at the application checkpoint. The user's subsequent push and
successful hosted run are recorded in the follow-up above; no work policy repair
or deployment ran in either continuation.

## Applied behavior

### Tool guard status

The previous executor hardcoded `passed` after agent completion, including a
plain text reply with no tool invocation. A pre-fix probe reproduced this
incorrect status. The applied executor observes actual wrapper decisions during the
current agent invocation:

| Current invocation | Tool guard status |
| --- | --- |
| No wrapper decision, including tool messages from old history | `not run` |
| A real wrapped tool passes its checks | `passed` |
| A policy blocks a tool | `blocked` |
| Guard evaluation cannot determine the target | `error` |
| Connector fails after its guard passed | `passed`, with overall `tool_error` |

The observation is independent of the bounded HTTP event list, isolated across
concurrent requests, sealed after invocation, and retains failure outcomes if
other tool calls subsequently pass. No prompts, arguments or credentials are
added to event storage. The existing frontend already renders `not run` neutrally;
this patch needs no frontend layout or model-registration format change.

The legacy HTTP authentication diagnostic's failing-tool fixture previously
raised directly without executing a guard. It now uses a real wrapper around a
synthetic failing connector, preserving its original `passed` assertion. New
tests separately require `not run` for an error raised without a guard decision.

Passing policy rails still does not establish factual answer accuracy. The
previous incorrect branch answer has not been independently root-caused.

### Policy 210 rehearsal

An offline SQLite fixture recreates the recorded legacy phrase, then checks the
proposed canonical condition `title = "test"` with `resource_condition_version=1`.
It verifies exact/case-folded title matching, nonmatching titles, update/read
exemptions, assignment/label preservation and compiled-rule refresh. IDs 210 and
214 exist only in synthetic in-memory fixtures during this test. This is evidence
for a proposed repair; actual policy intent, current work scope and deployment
still need their separate review. No production/rehearsal server repair is run.

### One-command PostgreSQL checks

The applied `scripts/run_postgres_checks.py`:

- Requires `--run`; default invocation only displays help.
- Accepts a local backend dependency image, never an existing database URL.
- Creates a unique internal Docker network and a tmpfs PostgreSQL 16 container,
  with synthetic credentials and no host database port or persistent volume.
- Mounts only source, config, scripts and tests; it does not mount `.env` or the
  Docker socket into the test worker.
- Checks migration wrong-target refusal, upgrade/idempotency, index/FK/check
  constraints and cascades, then runs the explicit 16 PostgreSQL diagnostics.
- Supplies and removes the documented legacy scope fixtures.
- Refuses non-dedicated or nonempty database targets in the container driver.
- Removes only container/network IDs returned by this invocation's creates,
  including on test failure; the cleanup logic has separate offline tests.

Available local commands:

```powershell
docker build --tag gms-verification:local .
python -B scripts/run_postgres_checks.py --run --backend-image gms-verification:local
```

The preview was tested using the previously verified `gms-home-be:20261022`
dependency image with candidate application source mounted read-only. Dependency
pins and the host virtual environment were unchanged. No new backend image build
or provider call was needed for this follow-up.

### Continuous integration

The saved `.github/workflows/verification.yml` runs on push, pull request and
manual dispatch. It uses a SHA-pinned
[official checkout action](https://github.com/actions/checkout/blob/11bd71901bbe5b1630ceea73d27597364c9af683/action.yml),
read-only repository permissions and disabled credential persistence. It does not
request provider credentials, publish images, migrate existing databases or deploy.

The backend job builds a pinned-dependency image, runs the explicit offline suite
with Docker networking disabled, and runs the isolated PostgreSQL runner. The
frontend job runs locked installation, ESLint, TypeScript and a production build
on the same digest-pinned Node 24 image as the frontend Dockerfile. Full advisory
audits remain separate; the known Pillow/FastEmbed and development braces findings
are not fixed by this automation.

At the application checkpoint the workflow was saved locally, with YAML and
underlying commands verified locally. The user's subsequent branch publication
triggered [the successful hosted run](https://github.com/adibice1/nemo-mcp-guardrails-test/actions/runs/39710898869),
which passed both jobs for commit 5f84cffe. Its separate hosted evidence is in the
follow-up linked above.

## Validation

| Check | Validation result |
| --- | --- |
| Pre-fix no-tool baseline | Reproduced `passed` despite no tool; expected regression assertion failed |
| Initial expanded offline catalogue | 37 passed on Windows and 37 passed in pinned Linux, with external sockets disabled |
| Final added runner safety check | Passed on Windows and pinned Linux; five ownership/cleanup cases |
| Final Windows catalogue | All 38 passed in one run, process exit 0 |
| New tool-status check | Eight cases pass: text/history, actual calls, error/block/filter paths, trace limit, concurrency/nesting and late callbacks |
| Synthetic policy repair | Passed without connecting to the work database |
| Final disposable PostgreSQL run | 16 passed, 0 failed, plus migration/idempotency/constraints/index/cascade checks |
| Frontend CI command sequence | Locked install, ESLint, TypeScript and Next.js production build passed on pinned Node 24 |
| Patch/YAML review | Exact patch passed apply check before application; workflow YAML parses and expected triggers/permissions/jobs match |
| Applied source identity | All ten file hashes match the tested/approved candidate |
| Applied affected checks | Tool status, synthetic policy rehearsal, runner safety, runtime events and runtime policy integration: 5 passed, 0 failed, process exit 0 |

Linux coverage is the initial 37-check run plus the final added runner check.
Windows also passed a final single 38-check run. The first database candidate run
found the legacy fake-agent mismatch described above; the final 16-check runs
pass with that fixture strengthened. An additional captured run confirms the
PostgreSQL runner exits 0. Direct subprocess capture avoids PowerShell treating
dependency warnings on stderr as a failed shell command; exit JSON files retain
the actual Windows and PostgreSQL process results.

All disposable PostgreSQL runs removed their containers and networks. The
existing home PostgreSQL service, stored model selections and private encryption
key were preserved. No new private credentials were requested.

Evidence is under `.waylog/automation-preview-20261022/`, including Windows/Linux
suite logs, baseline reproduction, final PostgreSQL output, frontend output,
patch and hashes. Historical home image acceptance is recorded separately in
[home-verification-results-2026-10-22.md](home-verification-results-2026-10-22.md).

## Remaining boundary

Actual work-network timing/log checks, policy 210 repair/validation, the app 221
classifier-grant decision, provisioned external-provider acceptance and production
rollout remain as listed in [the remaining checklist](remaining-verification-2026-10-22.md).
The no-tool badge is fixed in saved source. Restart an older source backend
process in its normal verified terminal to load the change. The original cached
image predated this patch; the follow-up now verifies the rebuilt local tag
`gms-home-be:20261022-followup`. Published deployment images still require their
normal authorized build/publication workflow. The current source commands are:

```powershell
python -B scripts/run_security_checks.py
python -B scripts/run_api.py
```

Use the second command after stopping the existing backend in its own terminal;
it is not a request to start a duplicate server or change database settings.
