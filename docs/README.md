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
- `tests/test_nemo_mcp.py` prints DB prompt-rule counts, DB-loaded runtime policies, and DB allowed test cases before running generated tests.
- `tests/test_policy_loader.py` verifies legacy and `--app-id` scoped
  Postgres policy loading without Azure OpenAI or GitHub MCP.
- `tests/test_app_policy_scope.py` proves real temporary app assignments
  scope NeMo rules and tool blocking, then cleans up its rows.
- `tests/test_nemo_mcp.py --app-id ...` passes a testing-only app scope
  through the full read-only runner; it does not enforce HTTP authentication.
- `src/nemo_mcp_guardrails/app_auth.py` verifies authorized client ID/API-key
  pairs using stored hashes and constant-time comparison.
- `tests/test_app_auth.py` proves valid authentication and generic rejection
  of wrong-key, unknown-client, and unauthorized-app cases, then cleans up.
- `src/nemo_mcp_guardrails/api/auth.py` provides reusable `X-App-ID` and
  `X-API-Key` HTTP authentication with a generic `401` for invalid requests.
- `GET /v1/guardrails/auth-check` is the first protected runtime proof
  endpoint; `tests/test_app_auth_http.py` verifies it and cleans up.
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
- App connector CRUD exists under `/apps/{app_id}/connectors` and
  `/apps/by-client-id/{client_id}/connectors`, so apps can be linked to GitHub
  without manual SQL.
- `credential_reference="env:VAR_NAME"` is executable for GitHub connector
  PAT selection; blank references fall back to `GITHUB_PERSONAL_ACCESS_TOKEN`.
- Management CRUD requires JWT authentication and enforces system-admin or
  app-developer permissions. Production secrets-manager credential resolution
  remains future work.
- `scripts/seed_normalized_policy_metadata.py` seeds normalized connector/action/resource/tool metadata and backfills allowed-test expected-tool links.
- Normalized metadata tables now include `connectors`, `connector_actions`, `connector_resources`, `connector_tool_mappings`, and `allowed_test_case_expected_tools`.
- Input/output diagnostic scripts now distinguish Azure `content_filter`
  blocks from completed NeMo classifications.
- The Next.js 13 frontend scaffold exists in `frontend/`. Its `/policies` page
  has a FastAPI adapter that uses real app/global/effective policy
  assignment data when `frontend/.env.local` sets
  `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000`; otherwise it uses mock data
  for static demos.
- The production frontend image listens directly on port `80` as a non-root
  process and proxies `/api/gms` to private backend port `8000`. ACI exposes
  only frontend `80`; local npm development remains on `3000`.

Start here for current project context:

- `file-map.md`: one-line backend/frontend file index and symptom lookup
- `work-computer-handoff.md`: exact 2026-08-21 deployment continuation point
- `open-work-backlog.md`: active unfinished work tracker
- `project-context.md`: current architecture and implementation state
- `frontend-api-map.md`: endpoint map for the Next.js frontend
- `frontend-screen-plan.md`: proposed screens and component structure
- `frontend-demo-flow.md`: presentation-ready GitHub MCP demo flow
- `containerisation.md`: Docker image, Compose, health-check, and local MCP notes
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
