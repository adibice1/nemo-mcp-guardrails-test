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
  apps: global, github
  app_actions: 11
  app_resources: 5
  tool_mappings: 17
  allowed_test_case_expected_tools: 3
  ```

## Current Verification Commands

Run these from the repo root:

```powershell
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
- apps: global, github
- github actions: 11
- github resources: 5
- github tool mappings: 17
- allowed test expected-tool links: 3
```

## Recommended Next Step

Add normalized policy foreign-key columns and backfill them while keeping the old flat text columns as fallback.

Recommended slice:

```text
1. Add nullable columns to policies:
   - app_id
   - action_id
   - resource_id
   - priority
   - conditions
   - policy_version

2. Add stale/version columns to compiled_policy_rules:
   - stale
   - policy_version

3. Backfill existing policies:
   policies.app/action/resource
   -> apps/app_actions/app_resources IDs

4. Update policy_loader.py:
   prefer normalized FK joins
   fallback to flat app/action/resource strings

5. Rerun:
   seed_normalized_policy_metadata.py
   POST /policies/compile-rules
   test_policy_loader.py
   test_tool_guard.py
   test_nemo_mcp.py
```

Do not remove the old `policies.app`, `policies.action`, or `policies.resource` columns yet. They are still the compatibility fallback for the current API and loader.

## After That

Once normalized policy loading is stable:

- Update `test_case_loader.py` to prefer `allowed_test_case_expected_tools` joins, with fallback to comma-separated `expected_tools`.
- Move more GitHub metadata out of hardcoded compiler constants and into DB metadata tables.
- Add stale/version handling for `compiled_policy_rules` when policies are edited.
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
