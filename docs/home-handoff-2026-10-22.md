# Home continuation - 22 October 2026, after presentation

Read this first on the home laptop, then the
[complete test results](post-presentation-verification-2026-10-22.md) and
[current deployment checklist](deployment-checklist-2026-10-22.md).
This supersedes the pending work-policy/grant/timing items in the 21 October
handoff. The presentation is finished and testing has resumed.

## Completed at work

- All **38 offline checks pass** after installing the approved aiohttp 3.14.5,
  certifi 2026.10.19 and yarl 1.25.1. All **120** work-venv constraints match;
  `pip check` passes. No application source or source pins changed in this run.
- Actual Azure rehearsal database verified:
  `guardrails-postgresql.postgres.database.azure.com` /
  `nemo_restore_check_20261016`. Owned-model schema, exact effective compiled
  policy content, selected-model grants, auth boundaries and persisted logs were
  checked. Four real branch reads passed, including one after package alignment;
  actual `list_branches` events and timing evidence are captured. No-tool and
  existing blocked/no-tool behavior also verified.
- **Test app 3 = app 221**, client ID
  `f496bd22-bdfc-417d-85ac-f25ec53bd599`. Azure environment defaults remain
  selected for main and classifier. The user explicitly retained the unused
  Qwen classifier approval. Do not revoke it or switch models as housekeeping.
- **Test App Two = app 214**: user approved assignment **190** reusing policy
  **212**, replacing its reference to **210**. Assignment ID/label/enabled state
  preserved; definitions and compiled rows unchanged. Actual snapshot and six
  matcher cases pass. This replaces the earlier in-place-policy-210 repair plan;
  do not apply that old plan as a second repair. Azure data changes do not appear
  in a Git pull or automatically update a home-local database.
- Six synthetic checks of the saved work encryption key pass. No owned model
  profiles currently exist in the rehearsal, so actual stored-profile decryption
  was not exercised. The temporary private access file was deleted; root `.env`
  and its saved work key were preserved.
- Prior home/CI acceptance remains valid: 38 offline checks, 16 isolated
  PostgreSQL diagnostics, frontend lint/TypeScript/build, Linux image acceptance,
  real proxy smoke and synthetic database/key recovery. Do not repeat the whole
  suite simply because this is a different computer.

## What can continue at home

1. Pull the updated documentation through the normal Git workflow and read the
   current results/checklist. These latest doc changes are local until committed
   and pushed; this handoff did not commit or push them.
2. Preserve home-local configuration. Home Docker PostgreSQL uses host port
   **5433**, not the work machine's local 5432 default. The home laptop still
   cannot access the online Azure database. Use local data for local work; a
   successful local test is not an actual Azure/production acceptance result.
3. Keep the **home encryption key** with its own encrypted home data. The work
   key is separate. Do not replace one key with the other, regenerate keys for
   testing, or transfer `.env`, keys, API keys or `.waylog` logs through Git.
4. Continue offline review of the known Pillow/FastEmbed compatibility finding
   and development-only braces finding, or prepare the production configuration/
   recovery plan with the supervisor. See the [dependency review](python-dependency-review-2026-10-22.md).
   A compatible remediation still needs its own code review and validation;
   passing tests have not resolved these findings.
5. For a new code change, run the relevant focused diagnostics and update the
   docs. `python scripts/run_security_checks.py` is the safe full offline runner
   when a change warrants it; the exact 38-script catalogue is in the results.
   Live/database diagnostic scripts remain deliberate opt-in operations.

No new code patch is required merely to complete this handoff. Selective PR
merging remains unavailable and fails closed; do not try to enable it through
configuration or weaken its checks.

## Requires work access or a user decision

| Item | Next action |
| --- | --- |
| App 214 HTTP/input acceptance, if in release scope | Use its existing key privately or manually run the exact-title/nonmatching Runtime Test cases documented in the results, keeping GitHub read-only. Matcher/snapshot checks already pass; do not create a real issue or regenerate its key for testing. |
| App 208, finance bot | Decide whether its missing approvals for both selected default models are intentional. Do not automatically enable grants. |
| App 222, adsf | It selects Qwen profile 21 for both roles. Earlier Qwen classifier quality matrices did not pass acceptance. Decide its intended classifier/release scope; do not interpret app 221's retained approval as quality acceptance for app 222. |
| Browser rendering, only if not covered in presentation | Inspect the latest recorded Traffic request and an existing Audit action. Backend persistence and proxy timing are complete. Literal browser durations need a DevTools capture only if wanted. Browser automation was unavailable. |
| Work key custody | Back up the existing work key privately using the agreed protected storage. Do not paste it into chat/docs. |

There are then **three production verification groups**: exact target schema/
configuration, actual target backup/key recovery/rollback, and deployed image-pair
acceptance. They require the intended target, release/recovery ownership and
authorized access. Production migration/publication/deployment has not run.
New-provider acceptance is conditional on actually adding a provider/gateway.

## Work computer left in this state

At the last verification, frontend was preserved and the backend was running
hidden on `127.0.0.1:8000`, PID **31988**, against the Azure rehearsal with
`GITHUB_MCP_READ_ONLY=1`. Output is in
`.waylog/post-presentation-20261022/backend-after-update.log`. The private access
handoff file is gone. These are work-machine details, not startup settings for
home; a PID is not portable and may no longer identify that server later.

At work, verify process ownership before stopping/restarting it. Root `.env`
still has a local database default; the backend uses a verified process override.
Restart from the verified rehearsal PowerShell environment and recheck actual
database identity. Do not assume a healthy login proves the correct target.
No production changes, application-source edits or Git commit/push were made by
the post-presentation testing/handoff sessions.
