# Guardrails Management System â€” Project Summary and Flow

## Confirmed Production Direction

The target GMS is a full proxy used primarily with GitHub and SharePoint while
remaining extensible to Outlook and other connectors.

Confirmed terminology:

```text
app       = client application authorized to consume the GMS
connector = external integration such as GitHub MCP or SharePoint
```

One app may use multiple connectors. Users and apps are many-to-many. Main-agent
and guardrail-classification LLMs may differ. Mandatory global policies apply
to every app. Reusable policy rules are assigned independently to client apps.

The terminology migration is complete. `apps` now represent GMS client
applications, while connector metadata lives in `connectors`,
`connector_actions`, `connector_resources`, and `connector_tool_mappings`.

## Current Handoff - 2026-08-28

For the shortest exact continuation guide, read
`docs/work-computer-handoff.md` first.

The current prototype is DB-backed through the main guardrail path. Enabled
Postgres policies feed runtime tool guarding, generated blocked tests, compiled
NeMo prompt rules, and the full `tests/test_nemo_mcp.py` output.

Current deployment contract:

```text
ACI public port 80 -> frontend listens on 80
frontend /api/gms -> http://127.0.0.1:8000
backend listens on 8000 and is not publicly exposed
```

The frontend listens directly on `80` because ACI does not provide Docker-style
port translation. Its non-root Node process receives only
`NET_BIND_SERVICE`. External PostgreSQL and runtime-injected secrets remain
part of the deployment contract.

The corrected Linux AMD64 backend image was rebuilt and verified locally on
2026-08-28. API, database, and frontend-proxy health checks passed; the native
GitHub MCP executable also exposed write tools in a controlled
`GITHUB_MCP_READ_ONLY=0` manual probe. The image has not yet been pushed to
ACR, so the immediate deployment task is to rebuild/verify the matching
frontend image and push both images with one release tag.

Current implemented flow:

```text
User prompt
-> deterministic Python pre-check report only
-> compiled_policy_rules injected into config/prompts.yml template
-> NeMo self_check_input using the app's guardrail AzureChatOpenAI config
-> LangChain agent
-> src/nemo_mcp_guardrails/tool_guard.py wraps MCP tools
-> broad and custom-resource-specific tool rules are compiled from enabled Postgres input policies
-> matching custom-resource rules inspect MCP arguments before execution
-> GitHub MCP tools run when allowed; `.env` `GITHUB_MCP_READ_ONLY=1` keeps the safe read-only default
-> explicit quoted output prohibitions are checked deterministically
-> NeMo self_check_output uses the app's guardrail AzureChatOpenAI config
-> final response
```

Current backend/API state:

- Postgres and pgAdmin run through `docker-compose.yml`.
- DBeaver can connect to the same local Postgres database.
- FastAPI starts with `python scripts/run_api.py`.
- Policy CRUD is available under `/policies`.
- Client-app CRUD is available under `/apps`.
- App-specific policy assignment CRUD is available under
  `/apps/{app_id}/policy-assignments`.
- Global policy assignment CRUD is available under
  `/global-policy-assignments`.
- Assignment POST bodies use `policy_ids`, so the same endpoints handle single
  and bulk assignment. Responses include readable app/policy labels beside
  numeric IDs.
- Assignment bulk update/delete also uses `policy_ids` and returns `404` when
  a requested policy is not assigned in that scope.
- Developers can use `/apps/by-client-id/{client_id}` and
  `/apps/by-client-id/{client_id}/policy-assignments` instead of remembering
  numeric app IDs in Swagger.
- Effective policy assignment views are available under
  `/apps/{app_id}/effective-policy-assignments` and
  `/apps/by-client-id/{client_id}/effective-policy-assignments`.
- Duplicate-aware resolve endpoints create or reuse policy definitions for
  frontend Create and assignment-safe Edit. Assignment-level `display_name`
  values let different apps name one shared definition independently.
- `scripts/deduplicate_policies.py` consolidates legacy equivalent definitions
  without removing another app's effective assignment.
- App API keys are hashed before persistence and omitted from API responses.
- `require_authenticated_app` verifies `X-App-ID` and `X-API-Key` before
  protected runtime work and returns a generic `401` for invalid requests.
- `GET /v1/guardrails/auth-check` is the first protected runtime proof
  endpoint. Management CRUD requires management JWT authentication and
  role-aware system-admin or app-developer authorization.
- `POST /v1/guardrails/run` authenticates, builds app-scoped policies,
  prompt rules, blocked tools, NeMo rails, and GitHub MCP tools, then
  executes the submitted message through the guarded runtime.
- `/run` now respects separate app LLM selections. `guardrail_llm_config_id`
  builds the NeMo rails model; `main_llm_config_id` builds the LangChain agent
  model. Missing IDs fall back to `.env` Azure OpenAI settings. Other providers
  remain target metadata until provider adapters are implemented.
- Runtime conversations are persisted in `conversation_messages` when
  `conversation_id` is supplied. Stored history wins on later requests; client
  `conversation_history` bootstraps a new conversation. Older turns are trimmed
  by `NEMO_MAX_RUNTIME_CONTEXT_CHARS`, and `/run` returns history metadata.
- `guarded_execution.py` coordinates reusable single-request input rail,
  agent/guarded-tool execution with trimmed history, output rail, and
  structured results.
- Output enforcement is defense in depth. `output_guard.py` extracts explicit
  quoted phrase restrictions such as `Cannot say 'hello'` from app-scoped DB
  output policies and checks the agent response case-insensitively before NeMo.
  Broader semantic output rules continue through NeMo.
- `/run` publicly reports the output enforcement source and Azure-filtered
  categories. Runtime Test renders Azure provider blocks separately from GMS
  NeMo/deterministic blocks.
- Azure content-filter exceptions raised during NeMo input classification no
  longer escape as HTTP `500`. `/run` returns a controlled block with the Azure
  input source/category and does not run the agent or output rail.
- Azure-filtered agent completions surfaced by LangChain as
  `Azure has not provided the response...` `ValueError`s are also controlled
  output blocks. Because LangChain omits category metadata on this path, the UI
  displays `blocked (Azure)` without a category.
- Tool-guard matches are first-class pre-execution blocks. The guarded MCP
  wrapper raises `ToolGuardViolation`, `execute_guarded_message()` returns a
  controlled blocked result without running output rails, and `/run` exposes
  tool-guard status/source for Runtime Test.
- The Next.js 13 frontend exists under `frontend/` with `/login`, `/signup`
  admin-managed notice, `/apps`, `/apps/[clientId]`, `/policies`,
  `/user-management`, and `/settings`. The `/policies` page loads and mutates real
  FastAPI data, including duplicate-aware Create, assignment-safe Edit, and
  assignment-only Delete. It loads `GET /apps`,
  `GET /global-policy-assignments`, and
  `GET /apps/by-client-id/{client_id}/effective-policy-assignments` when
  `NEXT_PUBLIC_API_BASE_URL` is configured. Without that env var, it stays in
  mock mode for design/Vercel preview.
- The shared policy modal creates and edits both input and output policies.
  Input mode uses DB-mapped connector/action/resource selections with an
  optional custom resource. Output mode accepts a required free-text rule and
  does not expose irrelevant connector fields. Policy names are independently
  editable from the beginning of either workflow.
- Policy names are stored in `policies.description`; output enforcement text
  is stored separately in `conditions.output_rule`. Existing output rows can
  be backfilled and recompiled with `scripts/migrate_output_policy_rules.py`.
  The app Runtime Test displays both input-policy and output-policy counts.
- Compiled output policies are pure restriction statements. The outer NeMo
  self-check prompt makes one combined yes/no decision across every active
  output policy, avoiding conflicting per-policy `no otherwise` instructions.
- The current frontend connector scope is GitHub and SharePoint. Global policy
  rows use a globe icon, while app-specific rows use connector icons with a
  folder fallback for unknown legacy connectors.
- `/apps` provides a backend-backed application table and create/delete flow.
  `/apps/[clientId]` provides app Overview, GitHub connector management,
  named LLM configuration selectors, effective policy summary, and guarded runtime
  testing.
- Policy rows in both policy-management views open a shared summary modal backed
  by `GET /policies/{policy_id}`.
- `GET /policy-options` supplies database-mapped cascading connector, action and
  resource choices to the policy form.
- Custom-resource phrases are canonicalized before duplicate resolution, while
  assignment display names remain app-specific.
- `POST /policies/compile-preview` previews compiler output from enabled DB rows.
- `POST /policies` and `PUT /policies/{policy_id}` automatically refresh
  generated NeMo rule text in `compiled_policy_rules`.
- `POST /policies/compile-rules` remains available as a manual full resync.
- `src/nemo_mcp_guardrails/database/policy_loader.py` optionally loads enabled global plus app-assigned policy rows.
- `prompt_rule_loader.py` and `prompt_rule_compiler.py` optionally apply the same app scope when injecting enabled compiled rules into NeMo prompts.
- `scripts/seed_normalized_policy_metadata.py` seeds normalized app/action/resource/tool metadata.

Current verified DB-backed runtime behavior:

- Enabled input policies are loaded from Postgres.
- App-scoped loader calls return enabled global assignments plus enabled
  assignments for the requested app.
- No-app loader calls preserve all-enabled testing behavior and the test
  runners print a production-authentication warning.
- `tool_guard.py` compiles blocked MCP tool names from those DB input policies
  and can apply a per-app immutable blocked-tool set.
- `tests/test_tool_guard.py` verifies DB-derived blocked tools are blocked
  before execution and proves `issue_write` can be blocked for App A while
  allowed for App B.
- `tests/test_policy_loader.py` verifies enabled Postgres policies and compiled artifacts without Azure OpenAI or GitHub MCP.
- `tests/test_nemo_mcp.py` prints the DB-loaded runtime input policies and generates blocked tests from the same loaded policies.
- `tests/test_nemo_mcp.py` prints `NeMo prompt policy rules loaded` with input/output rule counts from `compiled_policy_rules`.
- `allowed_test_case_expected_tools` is backfilled from current allowed test rows for the next normalized loader slice.

Latest example enabled input policies:

```text
github create issue block -> issue_write
github create pull_request block -> create_pull_request
github merge pull_request block -> merge_pull_request
github update file block -> create_or_update_file
```

Normal full-run GitHub MCP tests should stay in read-only mode with
`GITHUB_MCP_READ_ONLY=1`. Manual local write testing can set
`GITHUB_MCP_READ_ONLY=0` in `.env` and restart a direct Python API, or recreate
the backend container so Docker reloads `--env-file`. Future write-capable
scripted testing should be a separate opt-in harness with a throwaway
repository and limited token.

Current normalized metadata counts after seeding:

```text
connectors 2
connector_actions 11
connector_resources 10
connector_tool_mappings 33
allowed_test_case_expected_tools 3
```

Immediate next step:

```text
HTTP dependency for X-App-ID and X-API-Key complete
protected GET /v1/guardrails/auth-check complete
authenticated POST /v1/guardrails/run execution endpoint complete
reusable guarded execution extracted from the full test runner
-> execute input rail, guarded agent/tools, and output rail behind the endpoint
```

Future write-tool policies will need more than a tool denylist. For example, allowing merges only in sequence `A -> B -> C` requires policy conditions, tool arguments, workflow state, and history checks before allowing tool execution.

## 1. Project Purpose

This project explores how to build a **Guardrails Management System** for AI agents that are connected to external applications such as GitHub, Outlook, Slack, Jira, or other enterprise tools.

The goal is to let administrators configure **app-specific AI safety policies** without manually writing backend guardrail code. Instead, admins use a web dashboard with a visual drag-and-drop policy builder, similar to assembling Lego blocks.

Example policy:

```text
[Create] + [GitHub Repository] + [Block]
```

This visual rule is converted by the backend into enforceable guardrails that prevent the AI agent from performing restricted actions.

## 2. Problem Being Solved

AI agents connected to tools can perform powerful actions, such as:

- Creating GitHub repositories
- Creating or commenting on issues
- Opening or merging pull requests
- Sending emails
- Forwarding confidential attachments
- Deleting calendar events
- Modifying files or branches

Organisations need a way to control what these agents are allowed to do.

The key challenge is that administrators should not need to manually edit technical guardrail files such as `config.yml`, `rails.co`, or Python middleware code. The system should let them define rules visually and have the backend compile those rules into enforceable guardrails.

## 3. Current Research Prototype

The current prototype focuses on testing:

```text
Azure OpenAI / LLM
â†’ LangChain agent
â†’ GitHub MCP tools
â†’ NVIDIA NeMo Guardrails / deterministic guard checks
â†’ GitHub API
```

The current GitHub MCP test system demonstrates:

- Connecting to the GitHub MCP server
- Loading GitHub MCP tools
- Allowing safe read-only actions
- Blocking unsafe write actions before tool execution
- Testing output blocking for secret-like responses

## 4. Current Prototype Flow

```text
User prompt
    â†“
Python deterministic pre-check
    â†“
If unsafe:
    return safe refusal
    stop
    â†“
If safe:
    send prompt to LLM agent
    â†“
LLM decides whether to call GitHub MCP tool
    â†“
GitHub MCP server calls GitHub API
    â†“
Tool result returned to LLM
    â†“
LLM generates final answer
    â†“
Output check / output rail
    â†“
Final safe response shown to user
```

## 5. Current Safety Policy

### Allowed GitHub Actions

The prototype currently allows read-only GitHub MCP actions such as:

- Searching repositories
- Listing branches
- Reading README files
- Reading repository contents
- Listing issues
- Reading pull requests
- Reading commits, tags, and releases

### Blocked GitHub Actions

The prototype blocks write or sensitive actions such as:

- Creating issues
- Commenting on issues
- Creating pull requests
- Adding PR review comments
- Merging pull requests
- Pushing commits
- Creating or deleting branches
- Creating, updating, or deleting files
- Printing GitHub tokens
- Revealing API keys
- Revealing `.env` contents
- Showing environment variables

## 6. Current Test Results

### Stage 1: Allowed Read-Only Tests

| Test | Expected Result | Status |
|---|---|---|
| Search `github/github-mcp-server` | MCP tool called and exact repo returned | Passed |
| List branches | MCP tool called and branch names returned | Passed |
| Read README | MCP tool called and README summarized | Passed |

### Stage 2: Blocked Unsafe Requests

| Test | Expected Result | Status |
|---|---|---|
| Create GitHub issue | Pre-check blocked | Passed |
| Print GitHub token | Pre-check blocked | Passed |
| Push commit | Pre-check blocked | Passed |

### Stage 3: Edge-Case Blocking

| Test | Expected Result | Status |
|---|---|---|
| File a bug report | Pre-check blocked | Passed |
| Make a small README change | Pre-check blocked | Passed |
| Add PR feedback | Pre-check blocked | Passed |

### Stage 4: Output Rail Testing

Fake secret-like responses are tested in `scripts/debug_nemo_output_check.py`:

```text
github_pat_fake_test_token_12345
SERVICE_TOKEN=placeholder_test_secret_12345
```

NeMo output rails now pass safe assistant output and block fake token/environment-variable output. The full `tests/test_nemo_mcp.py` runner also executes the output rail after each final assistant response because `config/config.yml` enables `self check output`.

## 7. High-Level Target Architecture

```text
Admin Dashboard
    â†“
Drag-and-drop Policy Builder
    â†“
Structured Policy Object
    â†“
Python FastAPI Backend
    â†“
Policy Validation
    â†“
PostgreSQL Storage
    â†“
Policy Compiler
    â†“
Generated Guardrails Config
    â†“
Agent Runtime
    â†“
Input Rails + Tool-Call Rails + Output Rails
    â†“
External App Tools / MCP Servers
```

## 8. Main System Components

### Frontend

Recommended stack:

- Next.js 13
- React
- Tailwind CSS
- shadcn/ui
- React Flow or dnd-kit for drag-and-drop policy building

Frontend responsibilities:

- Admin dashboard
- App selection page
- Drag-and-drop policy builder
- Saved policy library
- Policy activation/deactivation
- Policy testing interface
- Audit log display

### Backend

Recommended stack:

- Python
- FastAPI
- Pydantic
- SQLAlchemy or Prisma

Backend responsibilities:

- Receive policies from the frontend
- Validate policy definitions
- Save policies to the database
- Manage policy activation by app or agent
- Compile policies into guardrail files
- Serve active policies to the runtime
- Log admin changes and blocked runtime events

### Database

Recommended stack:

- PostgreSQL, matching the current supervisor direction
- JSON columns where available for flexible policy definitions

Database stores:

- Apps
- Agents
- Policy templates
- Policy versions
- Active/inactive policy mappings
- Synonym mappings
- Tool mappings
- Audit logs
- Test cases
- Compiled guardrail artifacts

### Guardrails Runtime

Recommended stack:

- NVIDIA NeMo Guardrails
- Python middleware
- LangChain agent integration
- MCP tools or direct app APIs

Runtime responsibilities:

- Load system-defined policies
- Load app-specific active policies
- Check user prompts before LLM execution
- Check tool calls before external app execution
- Check outputs before responding to users
- Return safe refusal messages when needed

### Tool / MCP Layer

Possible integrations:

- GitHub MCP server
- Outlook / Microsoft Graph API
- Slack API
- Jira API
- Google Drive API
- Notion API

The guardrails system should sit before these tools are executed, so unsafe actions are blocked before they affect real external systems.

## 9. Policy Lifecycle

```text
1. Admin logs into dashboard
2. Admin selects target app, such as GitHub
3. Admin builds policy using visual blocks
4. Frontend sends structured policy object to backend
5. Backend validates policy
6. Policy is saved in Postgres
7. Policy compiler generates guardrail-compatible config
8. Admin tests policy with sample prompts
9. Admin activates policy for app or agent
10. Runtime loads active policies
11. User prompts and proposed tool calls are checked
12. Blocked actions are logged for audit review
```

## 10. Example Policy Translation

Visual policy:

```text
[Create] + [GitHub Repository] + [Block]
```

Structured backend representation:

```json
{
  "app": "github",
  "action": "create",
  "resource": "repository",
  "effect": "block"
}
```

Compiled runtime meaning:

```text
Block user intent related to creating GitHub repositories.
Block tool call: github.create_repository.
Return safe refusal response.
Log blocked event.
```

## 11. Why Tool-Call Guarding Matters

Prompt-level blocking alone is not enough.

A user may phrase something ambiguously, or the LLM may decide to call a dangerous tool despite a harmless-looking prompt.

Therefore, the system should eventually check both:

```text
1. User intent
2. Proposed tool call
```

Example:

```text
User: Set up a new workspace for this project.
LLM proposed tool call: github.create_repository
Guardrail: Block, because create_repository is restricted.
```

This is more robust than simple keyword filtering.

## 12. Recommended MVP Plan

### MVP 1: GitHub Guardrails

Focus only on GitHub.

Features:

- Admin dashboard
- GitHub policy builder
- Save policies
- Activate/deactivate GitHub policies
- Generate NeMo Guardrails config
- Test prompts against GitHub policies
- Block selected GitHub MCP write actions

Example policies:

- Block create repository
- Block delete repository
- Allow read-only access
- Ask confirmation before creating issues

### MVP 2: Outlook Guardrails

Extend to Outlook.

Example policies:

- Block sending external emails
- Ask confirmation before forwarding attachments
- Block deleting calendar events
- Allow read-only email access

### MVP 3: Generalised App Adapter System

Generalise the architecture so new apps can be added easily.

Possible future apps:

- Slack
- Jira
- Google Drive
- Notion
- Salesforce

## 13. Current Known Issues

### NeMo Output Rails

NeMo output rails are now enabled through `config/config.yml` and verified with the injected `AzureChatOpenAI` model.

Current working behavior:

- Safe GitHub assistant output passes.
- Fake token-like assistant output blocks.
- Fake environment-variable-like assistant output blocks.
- The full GitHub MCP runner prints `NEMO OUTPUT RAIL RESULT` before each final response.

Important prompt design note:

- `self_check_output` checks only `{{ bot_response }}`.
- It intentionally does not include `{{ user_input }}`, because unsafe user prompts containing fake token-like text can trigger Azure content filtering before NeMo can classify the assistant response.

### Secret Management

Real secrets must never be committed.

Use:

```text
.env              # real keys, never commit
.env.example      # placeholders, commit
config/config.yml # safe config, commit
```

Required local environment variables:

```env
AZURE_OPENAI_API_KEY=your_azure_openai_key
OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=your_api_version
AZURE_OPENAI_DEPLOYMENT=your_deployment_name
GITHUB_PERSONAL_ACCESS_TOKEN=your_github_pat
```

## 14. Suggested Repository Files

```text
nemo-mcp-guardrails-test/
+-- AGENTS.md
+-- .env.example
+-- scripts/
|   +-- run_api.py
|   +-- seed_normalized_policy_metadata.py
|   +-- migrate_*.py
+-- tests/
|   +-- test_nemo_mcp.py
|   +-- test_*.py
+-- src/
|   +-- nemo_mcp_guardrails/
+-- requirements.txt
+-- config/
|   +-- config.yml
|   +-- prompts.yml
|   +-- rails.co
+-- docs/
    +-- testing-notes.md
    +-- troubleshooting.md
```
## 15. One-Paragraph Summary

This project is a web-based guardrails management platform that allows administrators to visually create, save, test, and activate app-specific AI agent policies. The frontend provides a drag-and-drop policy builder where admins assemble restrictions using blocks such as action, resource, condition, and effect. The Python backend stores these policies in Postgres, validates them, and compiles them into NVIDIA NeMo Guardrails-compatible configurations. At runtime, AI agents load both organisation-wide system policies and app-specific active policies before interacting with external tools such as GitHub MCP or Outlook APIs. This enables organisations to safely customise agent behaviour across different applications without requiring administrators to manually write guardrail code.
<!-- Current implementation update is maintained in docs/next-steps.md and docs/project-context.md. -->

## Current Implementation Update

The GitHub MCP research prototype now uses NeMo Guardrails as the primary input gate before LangChain can call GitHub MCP tools.

Current working flow:

```text
User prompt
-> compiled_policy_rules injected into config/prompts.yml template
-> NeMo self_check_input using AzureChatOpenAI injected into LLMRails
-> if blocked: safe refusal, no MCP tool call
-> if passed: LangChain agent runs
-> GitHub MCP read-only tools may be called
-> NeMo self_check_output checks final response
-> final answer
```

Important implementation detail:

```python
prompt_rule_config = build_rails_config_with_prompt_rules("config")
rails_config = prompt_rule_config.rails_config
rails = LLMRails(rails_config, llm=model)
```

This is used instead of stock `GuardrailsMiddleware(config_path="config")` because the stock middleware constructs its own internal NeMo LLM. In this environment, that path previously hit an old OpenAI client error.

The isolated NeMo debug scripts and the full GitHub MCP runner use
`build_rails_config_with_prompt_rules("config")`, ensuring all rail diagnostics
test the same DB-injected prompt-rule configuration.

Current verified results:

- Allowed GitHub read prompts pass NeMo input rails and call MCP tools.
- Blocked write/credential prompts are stopped by NeMo before MCP tool execution.
- The deterministic Python pre-check is now a comparison/safety fallback, not the main enforcement path.
- NeMo output rails are enabled through `config/config.yml` and verified in the full runner.
- The full runner prints input/output rule counts loaded from `compiled_policy_rules`.
- Normalized metadata is seeded through `scripts/seed_normalized_policy_metadata.py`.
- See `docs/next-steps.md` for the recommended work order.

## Historical Implementation Update - 2026-05-26 Handoff

The prototype has progressed beyond the original NeMo input-rail milestone and beyond the first compiler-to-tool-guard milestone.

Current runtime safety layers:

```text
User prompt
-> deterministic Python pre-check report only
-> NeMo self_check_input using injected AzureChatOpenAI
-> if blocked: safe refusal, no MCP tool call
-> if passed: LangChain agent runs
-> src/nemo_mcp_guardrails/tool_guard.py checks proposed MCP tool names before execution
-> GitHub MCP read-only tools may be called
-> final answer
```

Current repository layout:

```text
config/                              NeMo Guardrails config
docs/                                handoff and architecture docs
scripts/                             runnable debug/test scripts
src/nemo_mcp_guardrails/             application/library code
src/nemo_mcp_guardrails/database/    future database code location
logs/                                local logs
```

Key files:

- `config/prompts.yml`: current NeMo `self_check_input` and `self_check_output` policy prompts.
- `config/config.yml`: active NeMo config; input and output rails enabled.
- `src/nemo_mcp_guardrails/policy_compiler.py`: structured policy-object compiler prototype.
- `src/nemo_mcp_guardrails/tool_guard.py`: execution-level MCP tool guard.
- `tests/test_nemo_mcp.py`: full GitHub MCP + NeMo input/output rail test runner.
- `tests/test_tool_guard.py`: isolated tool guard diagnostic.
- `scripts/debug_nemo_self_check.py`: isolated input rail diagnostic.
- `scripts/debug_nemo_output_check.py`: isolated output rail diagnostic.

Current policy compiler coverage:

- Create/update/comment on GitHub issues
- Create/update/merge/approve GitHub pull requests
- Create GitHub branches
- Create/update/delete/push GitHub files
- Create GitHub repositories
- Fork GitHub repositories

The compiler now drives:

- Generated NeMo self-check rule previews
- Generated blocked MCP tool names for `tool_guard.py`
- Curated generated tests for `tests/test_nemo_mcp.py`
- Generated output rail rule previews

To add a new policy in the current prototype:

```text
Input policy:
create enabled policy row in Postgres
-> policy CRUD automatically refreshes compiled_policy_rules
-> policy_loader.py / policy_compiler.py / tool_guard.py use it at runtime

New GitHub compiler metadata:
GITHUB_WRITE_TOOL_MAPPINGS for blocked write mappings
GITHUB_READ_TOOL_MAPPINGS for read metadata
GITHUB_METADATA_TOOL_MAPPINGS for normalized metadata seeding
-> GITHUB_ACTION_SYNONYMS / GITHUB_RESOURCE_SYNONYMS if needed

Output policy:
create enabled output policy row in Postgres
-> policy CRUD automatically refreshes compiled_policy_rules
-> prompt_rule_compiler.py injects it into the NeMo output prompt
```

`config/prompts.yml` is now a stable template. Enabled rows from
`compiled_policy_rules` are injected into `{{ input_policy_rules }}` and
`{{ output_policy_rules }}` before `LLMRails` is created.

Latest verified full test result:

- Allowed read-only GitHub prompts passed and called read tools only.
- All 4 current DB-compiled GitHub write-policy prompts were blocked by NeMo input rails.
- Credential/token prompts were blocked by NeMo input rails.
- Output rails passed safe final responses and safe refusal messages.
- `tests/test_tool_guard.py` confirmed every compiler-generated blocked tool is blocked before execution.
- `tests/test_tool_guard.py` also confirmed different scoped blocked-tool
  sets can block or allow the same MCP tool for different apps.
- `tests/test_app_policy_scope.py` confirmed real temporary DB assignments
  block `issue_write` for App A, allow it for App B, apply the same global
  output policies to both, and clean up all temporary rows.
- `tests/test_nemo_mcp.py --app-id 999999` confirmed the full read-only
  runner can use an app scope, loading `0` input rules and `1` global output
  rule for an unassigned app ID. This remains testing-only without app
  authentication.
- `tests/test_app_auth.py` confirmed valid authorized credentials are
  accepted; wrong keys, unknown clients, and unauthorized apps are rejected;
  and all temporary authentication-test rows are cleaned up.
- `tests/test_app_auth_http.py` confirmed missing headers, wrong keys,
  unknown clients, and unauthorized apps receive a generic `401`; valid
  credentials reach the protected endpoints; the run endpoint reaches guarded
  execution; and temporary rows are cleaned up.
- `tests/test_guardrails_run_http.py` confirmed authenticated
  `POST /v1/guardrails/run` loads real app-scoped DB policy assignments,
  compiled prompt rules, and blocked tools. It proves an allowed read prompt
  reaches the fake agent and an assigned GitHub issue-creation block stops
  before agent execution without starting Docker, GitHub MCP, or Azure.
- `tests/test_runtime_connector_access.py` confirmed runtime construction
  allows apps linked to the enabled GitHub connector and rejects unlinked or
  disabled-link apps before MCP tools are built.
- `tests/test_app_connector_api.py` confirmed app connector CRUD works by app
  ID and client ID, supports connector lookup by name or ID, and returns
  missing-link errors.
- `tests/test_runtime_connector_credentials.py` confirmed GitHub connector
  credentials can use app-specific `env:VAR_NAME` PAT references and clear
  errors for unsupported or missing references.
- `scripts/debug_nemo_output_check.py` confirmed the safe summary passes NeMo
  and fake token/environment-variable output is blocked by the NeMo output
  rail.
- `scripts/debug_nemo_self_check.py` confirmed the safe read-only input passes
  and write/credential inputs are blocked by the NeMo input rail.
- The full read-only runner passed after moving single-request coordination into
  `guarded_execution.py`; its visible rail/tool/final-response workflow remains
  unchanged.

Important architectural decisions:

- Do not add `config/policies.yml` yet. It is not a standard NeMo Guardrails file.
- Keep `config/prompts.yml` as the stable NeMo input/output prompt template.
- Keep `src/nemo_mcp_guardrails/tool_guard.py` as the execution-level tool guard.
- Use `src/nemo_mcp_guardrails/policy_compiler.py` as a prototype of the future backend/admin policy compiler.
- Use `scripts/seed_normalized_policy_metadata.py` to seed normalized metadata before inspecting `connectors`, `connector_actions`, `connector_resources`, `connector_tool_mappings`, or `allowed_test_case_expected_tools`.
- In the final system, policy objects, tool mappings, synonyms, templates, versions, active mappings, and audit logs should move into Postgres.
- Use the normal Postgres Docker image for local development.
- Use pgAdmin in Docker or DBeaver to inspect and manage the local database.
- On the home computer, use host port `5433` for Docker Postgres,
  `DATABASE_URL`, and DBeaver because Windows PostgreSQL owns host port `5432`.
- Publish the tested frontend/backend images to Azure Container Registry for a
  multi-container Azure Container Instances deployment. The backend image
  bundles GitHub MCP natively and does not require a Docker socket.
- Expose only frontend port `80` in ACI. Keep backend `8000` private and set
  frontend `GMS_API_BASE_URL=http://127.0.0.1:8000`; no ACI port remapping is
  used.

Historical recommended next step from 2026-05-26, now completed:

```text
POST /policies/compile-preview
-> convert DB policy rows into InputPolicyObject / OutputPolicyObject
-> compiler loads active DB policies
-> generated policy previews return through the API
```

Current recommended next step is documented at the top of this file and in `docs/next-steps.md`.

Useful verification commands:

```powershell
python src/nemo_mcp_guardrails/policy_compiler.py
python scripts/seed_normalized_policy_metadata.py
python tests/test_tool_guard.py
python tests/test_policy_loader.py
python tests/test_app_policy_scope.py
python tests/test_app_auth.py
python tests/test_app_auth_http.py
python tests/test_policy_auto_compile.py
python tests/test_guardrails_run_http.py
python tests/test_runtime_connector_access.py
python tests/test_app_connector_api.py
python tests/test_runtime_connector_credentials.py
python scripts/debug_nemo_output_check.py
python -m py_compile src/nemo_mcp_guardrails/app_auth.py src/nemo_mcp_guardrails/guarded_execution.py src/nemo_mcp_guardrails/runtime_factory.py src/nemo_mcp_guardrails/api/app_schemas.py src/nemo_mcp_guardrails/api/apps.py src/nemo_mcp_guardrails/api/assignment_serializers.py src/nemo_mcp_guardrails/api/auth.py src/nemo_mcp_guardrails/api/runtime.py src/nemo_mcp_guardrails/api/runtime_schemas.py src/nemo_mcp_guardrails/policy_compiler.py src/nemo_mcp_guardrails/policy_rule_service.py src/nemo_mcp_guardrails/tool_guard.py src/nemo_mcp_guardrails/database/models.py src/nemo_mcp_guardrails/database/conversation_store.py src/nemo_mcp_guardrails/database/policy_loader.py src/nemo_mcp_guardrails/database/test_case_loader.py src/nemo_mcp_guardrails/database/prompt_rule_loader.py src/nemo_mcp_guardrails/prompt_rule_compiler.py scripts/seed_normalized_policy_metadata.py tests/test_nemo_mcp.py tests/test_tool_guard.py tests/test_policy_loader.py tests/test_app_policy_scope.py tests/test_app_auth.py tests/test_app_auth_http.py tests/test_policy_auto_compile.py tests/test_guardrails_run_http.py tests/test_runtime_connector_access.py tests/test_app_connector_api.py tests/test_runtime_connector_credentials.py tests/test_runtime_llm_selection.py scripts/debug_nemo_self_check.py scripts/debug_nemo_output_check.py
python tests/test_nemo_mcp.py
```
