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

`POST /v1/guardrails/run` currently prepares and returns that runtime context.
It validates the submitted message but intentionally does not execute it yet.

Reusable one-message guardrail coordination is also implemented:

```text
execute_guarded_message()
-> NeMo input rail
-> stop before action execution when blocked
-> otherwise run LangChain agent with guarded MCP tools
-> NeMo output rail
-> GuardedExecutionResult
```

`scripts/test_nemo_mcp.py` calls this reusable function and still prints the
same detailed terminal workflow. The full read-only NeMo + GitHub MCP run
passed after the extraction.

## Important Current Files

- `src/nemo_mcp_guardrails/app_auth.py`: API-key hashing and app verification.
- `src/nemo_mcp_guardrails/api/auth.py`: `require_authenticated_app`.
- `src/nemo_mcp_guardrails/api/runtime.py`: protected auth-check and run-context endpoints.
- `src/nemo_mcp_guardrails/api/runtime_schemas.py`: runtime request/context response models.
- `src/nemo_mcp_guardrails/guarded_execution.py`: reusable one-message guardrail workflow.
- `src/nemo_mcp_guardrails/tool_guard.py`: app-scoped execution-level MCP tool guard.
- `scripts/test_nemo_mcp.py`: full read-only integration runner and terminal display.
- `scripts/test_app_auth_http.py`: protected HTTP boundary and context-scaffold test.
- `scripts/test_app_policy_scope.py`: real temporary app-assignment scope test.

## Verified Current Results

```text
service app authentication: passed
HTTP app authentication: passed
authenticated runtime-context preparation: passed
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

Connect `POST /v1/guardrails/run` to `execute_guarded_message()`.

Recommended incremental slice:

```text
1. Extract reusable Azure model and read-only GitHub MCP guarded-tool builders
   from scripts/test_nemo_mcp.py.
2. For the authenticated app, build app-scoped NeMo rails and guarded tools.
3. Call execute_guarded_message() with the request message.
4. Replace the context-preview response with a final JSON execution response:
   status, response, input rail status, output rail status, and tool names.
5. Test an allowed read request and a blocked request through the HTTP endpoint.
```

Keep `GITHUB_READ_ONLY=1`. Do not add write-capable endpoint testing to the
normal harness.

## Boundaries Not Yet Implemented

- `/v1/guardrails/run` does not execute the message yet.
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
