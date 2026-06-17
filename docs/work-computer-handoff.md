# Work Computer Handoff - 2026-06-16

## Read This First

This file records the exact home-computer project state to continue from on the
work computer.

Also follow the repository-level rules in `AGENTS.md`, especially the
requirement to preview exact non-doc code diffs and wait for approval.

Before starting new implementation:

```powershell
git pull
docker compose up -d postgres
python scripts/test_app_auth_http.py
python scripts/test_app_policy_scope.py
python scripts/test_tool_guard.py
python scripts/test_nemo_mcp.py
```

Before leaving the home computer, make sure this milestone is committed and
pushed. The work computer cannot see unpushed local files:

```powershell
git status
git add .
git commit -m "Add authenticated app-scoped runtime foundation"
git push
```

Review `git status` before committing and confirm `.env` is not staged.

The work computer may use Postgres host port `5432`. The home computer uses
host port `5433` because Windows PostgreSQL already owns `5432`. Keep each
computer's local `.env` correct and never commit it.

## Current Milestone

The authenticated, app-scoped runtime foundation is implemented:

```text
X-App-ID + X-API-Key
-> require_authenticated_app
-> authenticated AppRecord
-> app-scoped global + app policy assignments
-> app-scoped compiled NeMo prompt rules
-> app-scoped blocked MCP tool names
```

`POST /v1/guardrails/run` now builds that runtime context and executes the
submitted message through the reusable guarded flow. It also supports hybrid
conversation history: stored turns for `(app_id, conversation_id)` are loaded
when available, client-supplied `conversation_history` bootstraps a new
conversation, and older turns are trimmed by `NEMO_MAX_RUNTIME_CONTEXT_CHARS`
before the agent sees them.

Reusable single-request guardrail coordination is also implemented:

```text
execute_guarded_message()
-> NeMo input rail
-> stop before action execution when blocked
-> otherwise run LangChain agent with guarded MCP tools
-> return status=tool_error when a connector tool raises ToolException
-> NeMo output rail
-> return controlled blocked response when Azure filters output self-check
-> GuardedExecutionResult
```

`scripts/test_nemo_mcp.py` calls this reusable function and still prints the
same detailed terminal workflow. The full read-only NeMo + GitHub MCP run
passed after the extraction.

## Important Current Files

- `src/nemo_mcp_guardrails/app_auth.py`: API-key hashing and app verification.
- `src/nemo_mcp_guardrails/api/auth.py`: `require_authenticated_app`.
- `src/nemo_mcp_guardrails/api/runtime.py`: protected auth-check and run endpoints.
- `src/nemo_mcp_guardrails/api/runtime_schemas.py`: runtime request/execution response models.
- `src/nemo_mcp_guardrails/database/conversation_store.py`: conversation history load/append helpers.
- `src/nemo_mcp_guardrails/database/models.py`: includes `conversation_messages`.
- `src/nemo_mcp_guardrails/runtime_factory.py`: Azure, NeMo, MCP, and agent construction. It uses the authenticated app's `guardrail_llm_config_id` for NeMo rails and `main_llm_config_id` for the LangChain agent, with `.env` Azure fallback when either ID is missing.
- `src/nemo_mcp_guardrails/guarded_execution.py`: reusable single-request guardrail workflow.
- `src/nemo_mcp_guardrails/tool_guard.py`: app-scoped execution-level MCP tool guard.
- `scripts/test_nemo_mcp.py`: full read-only integration runner and terminal display.
- `scripts/test_app_auth_http.py`: protected HTTP boundary and runtime-execution reachability test.
- `scripts/test_app_policy_scope.py`: real temporary app-assignment scope test.

## Verified Current Results

```text
service app authentication: passed
HTTP app authentication: passed
authenticated runtime execution reachability: passed
runtime LLM selection: passed
conversation history storage/reload/truncation: passed
oversized latest-message rejection: passed
controlled connector tool-error responses: passed
controlled Azure output-filter responses: passed
temporary authentication rows cleanup: passed
temporary app policy-scope rows cleanup: passed
App A issue_write blocked / App B issue_write allowed: passed
tool guard isolated checks: passed
full read-only NeMo + GitHub MCP test: passed
Python compilation: passed
git diff --check: passed
```

The full runner still displays:

```text
NEMO INPUT RAIL RESULT
REQUEST STOPPED BEFORE ACTION EXECUTION, when blocked
MCP TOOLS CALLED, when allowed
NEMO OUTPUT RAIL RESULT
FINAL RESPONSE
```

The output looks unchanged because only coordination moved from the test loop
into `execute_guarded_message()`.

## Exact Next Implementation Step

Read `docs/open-work-backlog.md` first. It is the source of truth for
unfinished plans and prevents half-completed ideas from being lost between
machines.

Immediate top priority: make `config/prompts.yml` a generic self-check shell
instead of hardcoding GitHub/credential-specific behavior. Active policy
behavior should come from Postgres policies and `compiled_policy_rules`.

After that, add end-to-end HTTP coverage for real
`POST /v1/guardrails/run` execution.

Recommended incremental slice:

```text
1. Make self-check templates generic and DB-rule driven.
2. Confirm harmless assistant output passes the output rail.
3. Create a temporary authorized app.
4. Assign one GitHub input policy to that app.
5. Call POST /v1/guardrails/run with an allowed read prompt.
6. Call POST /v1/guardrails/run with a blocked write prompt.
7. Include a `conversation_id` and verify stored history is available on the
   next request.
8. Run `python scripts/test_runtime_llm_selection.py` to verify main/guardrail
   LLM selection behavior.
9. Assert response status, rail statuses, called tools, history metadata, and
   cleanup.
```

Keep `GITHUB_READ_ONLY=1`. Do not add write-capable endpoint testing to the
normal harness.

## Boundaries Not Yet Implemented

- Admin CRUD endpoints are not authenticated.
- User login and role authorization are not implemented.
- Automatic policy compilation/invalidation is not implemented.
- Argument-level and workflow-state policies are not implemented.
- Connector credentials and LLM credentials are not managed through a secrets
  manager yet.

## Editing Rules

- Preview exact non-doc code diffs and wait for user approval.
- Docs-only updates can be applied directly.
- Add short docstrings to new Python functions/classes.
- Update relevant docs after every completed change.
- Never commit `.env`, real API keys, PATs, or plaintext connector credentials.
