# Python dependency review - 22 October 2026

23 October targeted refresh: [the automated home review](home-automation-review-2026-10-23.md)
confirms pinned/latest FastEmbed still excludes Pillow 13 for Python 3.12 and
the braces advisory still lists no patched version. Pillow's exact pinned
version now has 38 OSV IDs and 34 PyPI IDs in that targeted metadata snapshot;
older eight/nine-count statements below are historical. This was not a full
installed-graph audit, package update or exploitability assessment.

## Work virtual environment aligned after presentation

After the user stopped the backend and explicitly approved installation, the
work Windows venv was updated to the already approved source pins: aiohttp
3.14.5, certifi 2026.10.19 and yarl 1.25.1. All 120 constraints now match with
no missing packages; pip check and all 38 offline diagnostics pass. A restarted
read-only rehearsal backend passes a real Azure/native-MCP branch read through
the frontend proxy. Source constraints were not changed. See
[the post-presentation results](post-presentation-verification-2026-10-22.md).
The historical home-host statement below describes that earlier run only.
Pillow/FastEmbed compatibility and the development-only braces finding remain open.

## Clean image follow-up completed

The final Linux image installs all 17 direct roots and 117 constrained runtime
packages at the exact reviewed versions, including cryptography 50.0.0. All 35
offline checks and a real guarded Azure/native-MCP read pass. Scanning the initial
full installed image also identified old base-image pip outside the constraints.
The Dockerfile now runs pip check after installation and removes unused runtime
pip. The final 117-package runtime retains only the nine OSV Pillow advisory IDs;
Pillow/FastEmbed compatibility remains open. Frontend production audit is zero,
with the known development-only braces finding retained. The host venv was not
changed. See [the final run record](home-verification-results-2026-10-22.md).


Status: the user explicitly approved the exact three-pin diff after the
explanation. It is applied to constraints.txt and matches the tested candidate
SHA-256. git diff --check passes. The running home environment, database and
backend process are unchanged. Earlier developer model registration/read and
frontend production-build acceptance remain recorded in the feature review.

## Applied compatible slice

| Constraint | Previous source | Applied source | Reason |
| --- | --- | --- | --- |
| aiohttp | 3.14.3 | 3.14.5 | Published stable patch covering the recorded resource-exhaustion finding |
| certifi | 2026.4.22 | 2026.10.19 | Current trust-bundle release after compromised-root removal |
| yarl | 1.23.0 | 1.25.1 | Required minimum for the candidate aiohttp release |

The [aiohttp advisory](https://github.com/aio-libs/aiohttp/security/advisories/GHSA-2g87-pp6c-29x5)
lists 3.14.4 as patched; the candidate uses published 3.14.5. Its
[release metadata](https://pypi.org/pypi/aiohttp/3.14.5/json) requires yarl >=1.25.1.
The [certifi advisory](https://github.com/certifi/python-certifi/security/advisories/GHSA-6q48-6c7w-9gw2)
records compromised emSign intermediates and root removal in 2026.10.18; the
candidate is the published [2026.10.19 release](https://pypi.org/project/certifi/2026.10.19/).

## Pillow remains open

Pillow stays pinned to 12.3.0 in this slice. The
[Pillow 13 release notes](https://pillow.readthedocs.io/en/stable/releasenotes/13.0.0.html)
record security fixes. Both the currently pinned FastEmbed 0.8.0 and published
FastEmbed 0.8.1/0.9.0 require Pillow below 13 across supported Python markers; see
[published FastEmbed metadata](https://pypi.org/pypi/fastembed/0.9.0/json). Simply
raising the Pillow pin or upgrading FastEmbed to those releases does not resolve
that constraint conflict. Preserve the required NeMo embedding dependencies and
keep this finding open pending a reviewed compatible upstream/backport solution.
No dependency override or forced incompatible installation is proposed.

## Validation and limits

- Fetched published metadata for all 120 candidate constrained packages. Base
  dependency bounds show no conflicts for Python 3.12 on Windows or Linux. This
  metadata check does not replace a full resolver/clean installation or image run.
- Downloaded SHA-256-verified Windows CPython 3.12 wheels for the three changes
  into an ignored preview interpreter, reusing other home packages. Confirmed
  actual imports and distribution metadata resolve to the three candidate versions.
- Initial offline run: 19 passed, 15 failed during import because the temporary
  environment did not process the parent pywin32 bootstrap. Corrected only the
  temporary environment and reran those 15: all passed. Across the two runs, all
  34 catalogue checks pass with the candidate packages.
- A 120-version OSV query of the candidate graph reports nine advisory IDs, all
  against Pillow 12.3.0. PyPI metadata reports eight against Pillow. These are
  source-specific snapshots, not interchangeable counts or exploitability tests.
  No other candidate package was flagged in these queries.
- Exact patch applicability passes. The active home venv still has its existing
  versions and differs from the full source pins. Clean pinned Linux/backend image
  installation and live TLS/provider acceptance remain required after application.
- No database, private environment, backend process or deployment was changed.

The exact patch, baseline/candidate/patch hashes, downloaded wheel hashes,
published package metadata, advisory responses and both test outputs are retained
privately in `.waylog/python-dependency-review-20261022/`. The approved source now matches those candidate bytes. Next verification is a
clean pinned backend installation/image build; Pillow remediation remains open.
