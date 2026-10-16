# Patch 019: Configurable PR Branch Conditions

The user authorized implementation in chat with "ok apply everything" after
reviewing the eight-part change list. This covers local source, tests, images
and rehearsal tooling, not production databases, GitHub writes/settings or
deployment. Earlier patches are preserved.

## Implemented behavior

Administrators can author source/target comparisons in the shared policy builder
using checkboxes, equals/does-not-equal selectors and branch-name inputs. Both
selected comparisons must match to block. Names remain configurable and
case-sensitive; owner-qualified creation heads are compared by branch name.
Existing conditions survive edit and require an explicit action before replacement
with a branch selector. After the user-approved presentation follow-up, policy
summaries, branch-editor previews and AI draft previews show branch comparisons in
plain English, such as 'The source branch is not "development" and the target
branch is "staging".' Branch rules are edited with the structured controls rather
than a symbolic textarea. Stored comparisons, exact branch names and enforcement
remain unchanged. Other custom-resource conditions retain their existing editor.

Existing validation, duplicate resolution, compilation, immutable snapshots and
tool enforcement share the new immutable comparison model. No parallel policy
engine, table, dependency or runtime topology is added. Single-field equality
retains format version 1 and existing artifacts. Branch inequality/two-field AND
uses canonical ordered selector text with resource_condition_version 2 in existing
conditions JSON. OR, repeated fields, mixed fields and workflows remain rejected.
Git branch names receive canonical-reference validation.

AI drafts use the same validator. Related drafts must preserve condition scope.
Merge explanations receive a backend-enforced limitation notice. The static
sample demonstrates source-not-staging AND target-production for creation.

| Operation | Matching condition | Nonmatching condition |
| --- | --- | --- |
| PR creation | Block before connector execution | Continue through other policies and rails |
| Branch-conditional merge | Trusted PR metadata; block with policy identity | Controlled evaluation refusal; no merge invocation |
| Missing/invalid PR metadata | Controlled evaluation refusal without claiming a match | Same |

## Selective merge execution remains unavailable

The actual bundled MCP v1.0.4 catalogue was inspected in a network-disabled
container with a synthetic token and no GitHub tool invocation. Its merge tool
has owner/repo/pullNumber and merge-message/method fields, but no expected-head
SHA or expected-base-ref precondition. The reviewed filter admits 31 tools.

Even the current GitHub REST merge API documents only a head-SHA precondition,
which does not lock the target branch. Metadata reads or a local lock cannot
guarantee against external retargeting before merge. This patch refuses
nonmatching conditional merges rather than permit that race. Editor, summary
and AI explanation disclose this behavior. Broad bans and number-only merge
restrictions retain their previous behavior.

The app's existing MCP connection reads metadata using get-PR with validated
owner/repo/number. Responses must identify that PR and repository and provide
valid head/base references. Agent-supplied branch values are ignored. Lookups
have a 15-second timeout and suppress private errors; broad bans need no lookup.
No remote metadata or policy values are added to execution traces.

Completing selective merges needs a verified upstream/repository-side enforcement
capability. Do not bypass refusal with a flag, infer target atomicity from SHA
checks or silently configure GitHub repositories. This is an explicit remaining
product/deployment limitation, not a completed allowed-merge capability.

Primary reference: [GitHub merge API](https://docs.github.com/en/rest/pulls/pulls#merge-a-pull-request).

## Legacy conversion rehearsal

scripts/convert_branch_policies.py recognizes only reviewed source-not-X-to-Y and
any-source-to-Y phrases. It preserves exact branch names without guessing aliases.
Unknown extra conditions and ambiguous wording do not convert automatically.
The supplied definitions 181, 182, 192, 193 and 209 fit the reviewed patterns.

Default invocation prints help without connecting. Explicit --database produces
a manifest with approvals off. Fingerprints cover complete definitions, resolved
metadata and assignment scope/labels. Edit only approval decisions after reviewing
proposed conditions. Manifest preview is read-only; apply validates every entry
before one transactional mutation. IDs, enabled flags, descriptions and assignment
labels are preserved. Versions increment and converted artifacts refresh.
Changed, duplicate or tampered manifests reject. Converted rows disappear from a
fresh inventory; old manifests must not be blindly replayed.

Writes require --apply-rehearsal on a PostgreSQL database whose name starts with
nemo_restore_check_. Production conversion is excluded. Use the verified rehearsal
PowerShell DATABASE_URL override; keep the work .env on local PostgreSQL. Save
manifests under ignored .waylog/ as UTF-8 without BOM and never print connection URLs.

After verifying the rehearsal connection:

```powershell
python scripts/convert_branch_policies.py --database
python scripts/convert_branch_policies.py --manifest .waylog/branch-conversion-review.json
python scripts/convert_branch_policies.py --manifest .waylog/branch-conversion-review.json --apply-rehearsal
python scripts/inventory_resource_conditions.py --database
```

Save the first output to the review file before editing approvals. Other legacy
issue-title, prefix, contradictory and read-action definitions remain separate
rollout work. Full recompilation still requires all enabled definitions to be
reconciled. Model grants and app authorization are unchanged.

## Verification

- All 32 offline diagnostics passed on Windows and Linux with credentials stripped
  and external sockets disabled. Existing equality, app/global scope, shared-policy
  edits and constant-revision warm-cache invalidation remain covered.
- Real guarded-tool tests cover create truth tables, case, qualified heads,
  malformed arguments, forged merge branches, lookup errors, broad-block precedence
  and zero conditional merge invocations. OR and unsupported fields still reject.
- SQLite HTTP tests cover canonical format 2, order-independent reuse, safe edits,
  compiled rules, snapshots and atomic/preview conversion.
- Disposable PostgreSQL 18.6 verified stale-assignment rejection, rollback after
  an actual partial write, all five legacy conversion patterns, preserved labels
  and assignments, and scoped snapshots. Synthetic data, internal networking,
  tmpfs and no published ports were used; test resources were removed afterward.
- Rendered branch-control handlers passed select/type/operator/edit/remove round
  trips, intermediate empty states, legacy preservation and notice checks through
  scripts/check_branch_editor.cjs. Full lint and TypeScript passed. Browser visual
  layout/event QA was not performed in a connected browser.
- The approved plain-English presentation follow-up passed the existing
  branch-editor check with formatting/fallback/incomplete-input assertions,
  whole-project TypeScript and full lint. It changed no database records or
  backend code; no new browser visual verification was performed.
- Both Linux AMD64 production images built; frontend non-root port-80, six pages,
  encoded proxy paths, fake credential forwarding, body caps and redirect checks
  passed. The final backend passed non-root imports, pip check, actual offline
  MCP catalogue validation and the focused Linux branch/contract/runtime suite.

Safe checks:

```powershell
python scripts/run_security_checks.py
node scripts/check_branch_editor.cjs
npm.cmd --prefix frontend run lint
```

scripts/check_branch_conversion_postgres.py is a separate opt-in fixture test.
It requires dotenv disabled and an empty isolated reviewdb/nemo_restore_check_patch019
database and is excluded from default regression execution. Never target an
existing environment with that harness.

No Azure database, model, live GitHub tool, production policy or repository setting
was changed by this implementation. No images were published or deployed.
