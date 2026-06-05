# nemo-mcp-guardrails-test
testing nemo on github mcp

Current handoff status:

- NeMo input and output rails are enabled through `config/config.yml`.
- GitHub MCP stays in read-only mode for normal full-run tests.
- Postgres stores prototype input/output policy rows.
- FastAPI exposes policy CRUD, allowed-test CRUD, compile-preview, and compiled-rule endpoints.
- `src/nemo_mcp_guardrails/database/policy_loader.py` loads enabled DB policies for runtime code.
- `src/nemo_mcp_guardrails/tool_guard.py` now compiles blocked tools from enabled DB input policies.
- `compiled_policy_rules` are injected into `config/prompts.yml` by `prompt_rule_compiler.py` before NeMo rails are created.
- `scripts/test_nemo_mcp.py` prints DB prompt-rule counts, DB-loaded runtime policies, and DB allowed test cases before running generated tests.
- `scripts/test_policy_loader.py` verifies Postgres policy loading without Azure OpenAI or GitHub MCP.
- `scripts/seed_normalized_policy_metadata.py` seeds normalized app/action/resource/tool metadata and backfills allowed-test expected-tool links.
- Normalized metadata tables now include `apps`, `app_actions`, `app_resources`, `tool_mappings`, and `allowed_test_case_expected_tools`.

Start here for current project context:

- `project-context.md`: current architecture and implementation state
- `testing-notes.md`: verified tests and commands
- `next-steps.md`: recommended next work item
- `runtime-flow-map.md`: concise file/function runtime flow map
- `policy-schema-design.md`: normalized schema design and migration plan
- `PROJECT_SUMMARY.md`: broader product/architecture summary and handoff notes
- `troubleshooting.md`: known setup and NeMo/GitHub MCP issues
