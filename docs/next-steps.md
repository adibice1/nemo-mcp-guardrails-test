# Next Steps

## Current Milestone

The current prototype is now DB-backed through the main guardrail path:

```text
Postgres policies
-> policy_loader.py
-> policy_compiler.py
-> compiled_policy_rules
-> prompt_rule_loader.py
-> prompt_rule_compiler.py
-> config/prompts.yml template
-> NeMo input/output rails
-> scripts/test_nemo_mcp.py terminal output
```

Completed pieces:

- The additive client-app foundation migration has created empty `users`,
  `llm_configs`, and `apps` tables.
- The connector terminology migration has renamed the former connector-shaped
  `apps` metadata to `connectors`, including related actions, resources, tool
  mappings, policy fields, and allowed-test joins.
- `app_users` and `app_connectors` now model user ownership/roles and
  app-specific connector access.
- `app_policy_assignments` and `global_policy_assignments` now reference the
  reusable policy definitions already stored in `policies`.
- FastAPI now exposes client-app CRUD, nested app-policy-assignment CRUD, and
  global-policy-assignment CRUD.
- GitHub MCP full-run tests stay read-only with `GITHUB_READ_ONLY=1`.
- NeMo input and output rails are enabled.
- `scripts/test_nemo_mcp.py` injects DB compiled prompt rules into NeMo config.
- Runtime input policies come from Postgres through `policy_loader.py`.
- `tool_guard.py` blocks DB-derived restricted tool names before execution.
- Allowed read tests come from `allowed_test_cases`, with fallback defaults.
- Blocked tests are generated from enabled DB policies.
- FastAPI exposes policy CRUD, allowed-test CRUD, compile-preview, compile-rules, and compiled-rules endpoints.
- Normalized metadata tables now exist in SQLAlchemy models.
- `scripts/seed_normalized_policy_metadata.py` seeds:
  ```text
  connectors: global, github
  connector_actions: 11
  connector_resources: 10
  connector_tool_mappings: 33
  allowed_test_case_expected_tools: 3
  ```

Home-laptop setup warning:

```text
DBeaver does not read .env and needs no VS Code extension.
Postgres Docker volumes retain their original database password.
Changing POSTGRES_PASSWORD in .env does not update an existing volume.
```

If DBeaver rejects the correct-looking password on another laptop, read
`docs/troubleshooting.md` under **Home Laptop: DBeaver Password Fails** before
changing project code.

## Current Verification Commands

Run these from the repo root:

```powershell
.\.venv\Scripts\python.exe scripts\migrate_client_app_foundation.py
.\.venv\Scripts\python.exe scripts\migrate_connector_terminology.py
.\.venv\Scripts\python.exe scripts\migrate_app_relationships.py
.\.venv\Scripts\python.exe scripts\migrate_policy_assignments.py
.\.venv\Scripts\python.exe -m py_compile src\nemo_mcp_guardrails\policy_compiler.py src\nemo_mcp_guardrails\tool_guard.py src\nemo_mcp_guardrails\database\models.py src\nemo_mcp_guardrails\database\policy_loader.py src\nemo_mcp_guardrails\database\test_case_loader.py src\nemo_mcp_guardrails\database\prompt_rule_loader.py src\nemo_mcp_guardrails\prompt_rule_compiler.py scripts\seed_normalized_policy_metadata.py scripts\test_nemo_mcp.py scripts\test_tool_guard.py scripts\test_policy_loader.py scripts\debug_nemo_self_check.py scripts\debug_nemo_output_check.py
.\.venv\Scripts\python.exe scripts\seed_normalized_policy_metadata.py
.\.venv\Scripts\python.exe scripts\test_policy_loader.py
.\.venv\Scripts\python.exe scripts\test_tool_guard.py
.\.venv\Scripts\python.exe scripts\test_nemo_mcp.py
```

Expected `scripts/test_nemo_mcp.py` proof lines:

```text
NeMo prompt policy rules loaded
- input rules from compiled_policy_rules: 14
- output rules from compiled_policy_rules: 1

Runtime input policies loaded
- DB policy #...

Allowed test cases loaded
- DB allowed test #...
```

Expected seed counts:

```text
Normalized policy metadata seeded.
- connectors: global, github
- github connector actions: 11
- github connector resources: 10
- github connector tool mappings: 33
- allowed test expected-tool links: 3
```

## Recommended Next Step

Make runtime policy loading and management assignment-aware.

Recommended slice:

```text
1. Update `policy_loader.py` to accept an app ID and load:
   enabled global assignments
   + enabled assignments for the requesting app

2. Update `prompt_rule_loader.py` to apply the same app-specific policy scope,
   so NeMo rails and the tool guard enforce the same rules.

3. Keep the current no-app test runner on the legacy all-enabled-policy path
   until an app-aware integration harness exists.

4. Add app credential verification for `client_id` and API key.

5. Design `POST /v1/guardrails/run` for the full-proxy runtime.

6. Automate policy compilation/invalidation when rules or assignments change.
```

The normalized policy-reference migration is complete:

```text
policies.connector_id/action_id/resource_id backfilled
policy_loader.py prefers normalized relationships
compiled_policy_rules tracks policy_version and stale
policy create/update accepts readable names and resolves normalized IDs
policy create/update validates combinations against enabled tool mappings
allowed-test create/update accepts readable tool-name lists and maintains joins
users, llm_configs, and apps foundation tables exist
connector terminology migration complete
app_users and app_connectors relationship tables exist
app_policy_assignments and global_policy_assignments exist
app and assignment CRUD endpoints exist
```

Current assignment counts:

```text
app policy assignments: 0
global policy assignments: 1
```

The global assignment points to the connector-independent credential output
policy. Existing GitHub write policies remain unassigned.

Latest foundation migration result:

```text
Client-app foundation migration complete.
- users: 0
- llm configs: 0
- apps: 0
```

The empty counts are expected. The migration establishes the schema only; seed
records and authentication endpoints belong to later slices.

Do not remove the old `policies.app`, `policies.action`, or
`policies.resource` columns yet. They remain the compatibility fallback while
policy creation and update flows are moved fully onto normalized IDs.

Metadata endpoints can now distinguish client apps from external connectors.

## After That

Once normalized policy loading is stable:

- Move more GitHub metadata out of hardcoded compiler constants and into DB metadata tables.
- Remove legacy policy text columns only after all policy writes use normalized IDs.
- Add argument-policy and workflow-policy schema slices.
- Keep write-capable MCP tests separate, opt-in, and pointed at a throwaway repo with a limited token.

## Files To Read First On Another Machine

- `AGENTS.md`
- `docs/runtime-flow-map.md`
- `docs/project-context.md`
- `docs/policy-schema-design.md`
- `docs/testing-notes.md`
- `docs/troubleshooting.md`
- `scripts/test_nemo_mcp.py`
- `scripts/seed_normalized_policy_metadata.py`
- `src/nemo_mcp_guardrails/policy_compiler.py`
- `src/nemo_mcp_guardrails/database/policy_loader.py`
- `src/nemo_mcp_guardrails/prompt_rule_compiler.py`
