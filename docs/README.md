# nemo-mcp-guardrails-test
testing nemo on github mcp

Start with `target-architecture.md` for the confirmed production direction and
terminology. Target `app` means a client application consuming the GMS, while
target `connector` means GitHub MCP, SharePoint, Outlook, or another external
integration.

Current handoff status:

- NeMo input and output rails are enabled through `config/config.yml`.
- GitHub MCP stays in read-only mode for normal full-run tests.
- Postgres stores prototype input/output policy rows.
- FastAPI exposes policy CRUD, allowed-test CRUD, client-app CRUD,
  app-policy-assignment CRUD, global-policy-assignment CRUD, compile-preview,
  and compiled-rule endpoints.
- `src/nemo_mcp_guardrails/database/policy_loader.py` and
  `prompt_rule_loader.py` optionally load enabled global plus app-assigned
  policies/rules.
- `src/nemo_mcp_guardrails/tool_guard.py` can compile and apply optional
  per-app blocked-tool sets from enabled global plus app-assigned input
  policies.
- `compiled_policy_rules` are injected into `config/prompts.yml` by `prompt_rule_compiler.py` before NeMo rails are created.
- `scripts/test_nemo_mcp.py` prints DB prompt-rule counts, DB-loaded runtime policies, and DB allowed test cases before running generated tests.
- `scripts/test_policy_loader.py` verifies legacy and `--app-id` scoped
  Postgres policy loading without Azure OpenAI or GitHub MCP.
- `scripts/test_app_policy_scope.py` proves real temporary app assignments
  scope NeMo rules and tool blocking, then cleans up its rows.
- `scripts/test_nemo_mcp.py --app-id ...` passes a testing-only app scope
  through the full read-only runner; it does not enforce HTTP authentication.
- `src/nemo_mcp_guardrails/app_auth.py` verifies authorized client ID/API-key
  pairs using stored hashes and constant-time comparison.
- `scripts/test_app_auth.py` proves valid authentication and generic rejection
  of wrong-key, unknown-client, and unauthorized-app cases, then cleans up.
- `src/nemo_mcp_guardrails/api/auth.py` provides reusable `X-App-ID` and
  `X-API-Key` HTTP authentication with a generic `401` for invalid requests.
- `GET /v1/guardrails/auth-check` is the first protected runtime proof
  endpoint; `scripts/test_app_auth_http.py` verifies it and cleans up.
- `POST /v1/guardrails/run` now authenticates, builds app-scoped rules,
  policies, rails, and guarded tools, then executes the submitted message.
  It supports stored conversation history through `conversation_id`, accepts
  `conversation_history` for bootstrapping, trims older turns by
  `NEMO_MAX_RUNTIME_CONTEXT_CHARS`, and returns history metadata.
- `src/nemo_mcp_guardrails/guarded_execution.py` coordinates reusable
  input-rail, agent/tool, and output-rail execution. The full test runner now
  uses it while preserving the same terminal display.
- `src/nemo_mcp_guardrails/runtime_factory.py` respects separate app
  `main_llm_config_id` and `guardrail_llm_config_id` selections for the agent
  and NeMo rails.
- Admin CRUD endpoints remain unprotected. The next cleanup is to make
  `config/prompts.yml` generic so policy behavior comes from database rules,
  followed by real HTTP integration coverage for allowed and blocked
  `/v1/guardrails/run` requests.
- `scripts/seed_normalized_policy_metadata.py` seeds normalized connector/action/resource/tool metadata and backfills allowed-test expected-tool links.
- Normalized metadata tables now include `connectors`, `connector_actions`, `connector_resources`, `connector_tool_mappings`, and `allowed_test_case_expected_tools`.
- Input/output diagnostic scripts now distinguish Azure `content_filter`
  blocks from completed NeMo classifications.

Start here for current project context:

- `work-computer-handoff.md`: exact 2026-06-16 continuation point and next slice
- `open-work-backlog.md`: active unfinished work tracker
- `project-context.md`: current architecture and implementation state
- `testing-notes.md`: verified tests and commands
- `next-steps.md`: recommended next work item
- `runtime-flow-map.md`: concise file/function runtime flow map
- `policy-schema-design.md`: normalized schema design and migration plan
- `PROJECT_SUMMARY.md`: broader product/architecture summary and handoff notes
- `troubleshooting.md`: known setup and NeMo/GitHub MCP issues

Home-computer handoff warning: if DBeaver reports a fatal password error even
with copied `.env` values, read **IMPORTANT HANDOVER: Home Laptop DBeaver Fatal
Password Error** in `troubleshooting.md`. Persistent Docker volumes retain the
password used at first initialization. The confirmed home-computer setup uses
host port `5433` for Docker Postgres and DBeaver because Windows PostgreSQL
already uses host port `5432`.
