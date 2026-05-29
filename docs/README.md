# nemo-mcp-guardrails-test
testing nemo on github mcp

Current handoff status:

- NeMo input and output rails are enabled through `config/config.yml`.
- GitHub MCP stays in read-only mode for normal full-run tests.
- Postgres stores prototype input/output policy rows.
- FastAPI exposes policy CRUD plus `POST /policies/compile-preview`.
- `src/nemo_mcp_guardrails/database/policy_loader.py` loads enabled DB policies for runtime code.
- `src/nemo_mcp_guardrails/tool_guard.py` now compiles blocked tools from enabled DB input policies.
- `scripts/test_nemo_mcp.py` prints the DB-loaded runtime input policies before running generated tests.

Start here for current project context:

- `project-context.md`: current architecture and implementation state
- `testing-notes.md`: verified tests and commands
- `next-steps.md`: recommended next work item
- `PROJECT_SUMMARY.md`: broader product/architecture summary and handoff notes
- `troubleshooting.md`: known setup and NeMo/GitHub MCP issues
