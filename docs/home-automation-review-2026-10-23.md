# Automated home review - 23 October 2026

Later continuation: the [fresh-release handoff](final-workday-handoff-2026-10-23.md)
records the user's target/ownership decisions and accepted local preparation.
The supplied SE-EDU templates have now been applied to [UserGuide.md](UserGuide.md)
and [DeveloperGuide.md](DeveloperGuide.md). The original review below remains a
record of its earlier checkpoint, not an outstanding request for those decisions.

The user asked whether the remaining home work can be automated. The read-only
dependency review and configuration-template inspection have now run. A
[production configuration/recovery worksheet](production-readiness-worksheet-2026-10-23.md)
is prepared for the target/release owners to fill in. Accepted tests were not
rerun merely to generate another passing result.

## Automation boundary

| Task | What automation can complete at home | Remaining dependency |
| --- | --- | --- |
| Dependency review | Fetch public package/advisory metadata; evaluate version bounds on Python 3.12 Windows/Linux; retain source hashes and evidence | A compatible remediation still needs implementation review and validation, or a release disposition |
| Configuration preparation | Inspect committed placeholder examples and source/docs; identify required variables, template inconsistencies and missing deployment inputs | Actual target, app scope, secret provisioning/custody and release-owner decisions |
| Recovery/rollout planning | Draft the sequence, required evidence, rollback inputs and post-deployment acceptance | Actual target backup/key access and authorized deployment/recovery environment |
| Regression/integration checks | Existing offline and disposable PostgreSQL runners already automate these | Rerun when a relevant change warrants it; current accepted coverage remains valid |

Automation can prepare the remaining work. It cannot infer production app intent,
create access to an unreachable target or turn a synthetic restore into evidence
for the actual production backup process.

## Dependency findings refreshed

The review queried public PyPI/npm metadata and OSV for the two source-pinned
packages. It did not install packages, resolve an entire candidate environment,
scan the entire graph again or assess exploitability.

### Pillow/FastEmbed

- Source pins: Pillow 12.3.0, FastEmbed 0.8.0 and NeMo Guardrails 0.21.0.
- The current [FastEmbed publication](https://pypi.org/pypi/fastembed/json) reports
  0.9.0. Both it and [the pinned 0.8.0](https://pypi.org/pypi/fastembed/0.8.0/json)
  require Pillow below 13 for Python 3.12. Evaluated Windows/Linux markers reject
  Pillow 13.0.0 in all four pinned/latest cases.
- The pinned [NeMo metadata](https://pypi.org/pypi/nemoguardrails/0.21.0/json)
  requires FastEmbed for the project's Python 3.12 runtime. Removing it is not an
  established compatible remediation.
- The latest [Pillow metadata](https://pypi.org/pypi/pillow/json) reports 13.0.0,
  while the pinned [12.3.0 metadata](https://pypi.org/pypi/pillow/12.3.0/json)
  reports **34 advisory IDs**. The targeted OSV query reports **38 IDs** for that
  exact pinned version. The full ID lists are retained in the local report.
- These are refreshed source-specific metadata counts, superseding the older
  eight/nine-count snapshot for this package. They are not interchangeable
  counts, independent exploit proofs or a new full installed-image audit.

The straightforward Pillow 13 pin bump still conflicts with FastEmbed's declared
dependency. A reviewed compatible upstream/backport/dependency solution remains
open; no forced override or removal was applied.

### Development-only braces

- The committed lockfile still resolves braces 3.0.3 and marks it development-only.
- The [npm publication](https://registry.npmjs.org/braces/latest) still reports
  3.0.3; the targeted OSV query returns GHSA-vfj7-8cjw-p6xm.
- The [reviewed advisory](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm)
  lists affected versions through 3.0.3 and no patched version.

This refresh did not rerun npm audit, change the frontend lockfile, upgrade
Tailwind or claim a new zero-finding audit. The earlier production-audit result
remains its dated result. Development/tooling exposure and the finding's release
disposition remain separate from runtime regression success.

## Configuration-template finding

Committed `.env.example` contains duplicate `GMS_JWT_SECRET` and
`GMS_JWT_EXPIRY_MINUTES` entries. Only placeholder values were inspected; no
private `.env` was read. Use one deliberate value per variable in the eventual
production configuration. A template cleanup would be a separate exact-diff
change under the repository's approval rule; no template or private setting
was silently rewritten in this review.

## Evidence and scope

The script and machine-readable report are under
`.waylog/home-automation-20261023/`. The report records public metadata URLs,
versions/requirements, marker checks, advisory IDs, duplicate variable names and
SHA-256 values for requirements, constraints, lockfile and placeholder example.
Requests sent only public package names/versions; no app/user/credential data.
The local script is a review artifact, not a new registered regression or CI job.

Application source, pins, host dependencies, private `.env`, encryption keys,
databases, model grants and services were unchanged. No production operation ran.
Current test acceptance remains the 38-check catalogue and 16 isolated PostgreSQL
diagnostics documented in [the post-presentation results](post-presentation-verification-2026-10-22.md).
The three production verification groups remain open in
[the deployment checklist](deployment-checklist-2026-10-22.md).
