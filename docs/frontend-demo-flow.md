# Frontend Demo Flow

This is the recommended GitHub MCP demo path for the first Next.js 13 frontend.
It assumes the backend is running locally and the database has seeded connector
metadata.

## Demo Objective

Show that a developer can configure a client app to use the Guardrails
Management System, connect it to GitHub MCP, assign policies, and verify that
the runtime allows safe read actions while blocking restricted write actions.

## Backend Setup

Start Postgres:

```powershell
docker compose up -d
```

Seed connector metadata:

```powershell
.\.venv\Scripts\python.exe scripts\seed_normalized_policy_metadata.py
```

Start API:

```powershell
.\.venv\Scripts\python.exe scripts\run_api.py
```

Open Swagger if needed:

```text
http://127.0.0.1:8000/docs
```

## Demo Data

Example app:

```json
{
  "name": "GitHub Demo Bot",
  "client_id": "github-demo-bot",
  "api_key": "github-demo-bot-api-key-123",
  "authorized": true,
  "main_llm_config_id": null,
  "guardrail_llm_config_id": null
}
```

Example app-specific PAT env var:

```env
GITHUB_DEMO_BOT_PAT=github_pat_your_demo_token
```

Example GitHub connector link:

```json
{
  "connector_name": "github",
  "credential_reference": "env:GITHUB_DEMO_BOT_PAT",
  "enabled": true
}
```

Example policy:

```json
{
  "policy_type": "input",
  "connector": "github",
  "action": "create",
  "resource": "issue",
  "description": "Block GitHub issue creation",
  "effect": "block",
  "priority": 100,
  "conditions": {},
  "enabled": true
}
```

## Flow 1: Create A Client App

Screen:

```text
/apps
```

User action:

```text
Click "New App"
-> enter app name, client ID, API key, authorized=true
-> save
```

Backend:

```text
POST /apps
```

What to show:

- app appears in app table
- app has a readable `client_id`
- API key is not shown again after creation

Presentation line:

```text
This app represents a product team's AI agent that wants to consume the GMS.
```

## Flow 2: Link The App To GitHub MCP

Screen:

```text
/apps/github-demo-bot
```

Tab:

```text
Connectors
```

User action:

```text
Click "Link GitHub"
-> set credential reference env:GITHUB_DEMO_BOT_PAT
-> enabled=true
-> save
```

Backend:

```text
POST /apps/by-client-id/github-demo-bot/connectors
```

What to show:

- GitHub connector enabled badge
- credential reference visible as `env:GITHUB_DEMO_BOT_PAT`
- no actual PAT value is displayed

Presentation line:

```text
The app can use its own GitHub token without storing the token in the policy table.
```

## Flow 3: Create Or Select A GitHub Write Policy

Screen:

```text
/policies
```

User action:

```text
Create or find "Block GitHub Create Issue"
```

Backend:

```text
POST /policies
GET /policies
```

What to show:

- policy type: input
- connector: GitHub
- action: Create
- resource: Issue
- effect: Block
- enabled: true

Presentation line:

```text
Policies are reusable. The same policy definition can be assigned to one app, many apps, or globally.
```

## Flow 4: Assign The Policy To The App

Screen:

```text
/apps/github-demo-bot
```

Tab:

```text
Policies
```

User action:

```text
Select "Block GitHub Create Issue"
-> click "Assign"
```

Backend:

```text
POST /apps/by-client-id/github-demo-bot/policy-assignments
```

Body:

```json
{
  "policy_ids": [12],
  "enabled": true
}
```

What to show:

- policy appears in assigned app policy table
- effective policy summary count increases
- global policies are shown separately from app policies

Presentation line:

```text
App A can block issue creation while App B can allow it, even if both use GitHub MCP.
```

## Flow 5: Test An Allowed Read Request

Screen:

```text
/apps/github-demo-bot
```

Tab:

```text
Runtime Tester
```

Headers used by frontend:

```text
X-App-ID: github-demo-bot
X-API-Key: github-demo-bot-api-key-123
```

Prompt:

```text
Use GitHub MCP to list branches for owner github and repo github-mcp-server.
```

Backend:

```text
POST /v1/guardrails/run
```

Expected result:

```text
status: passed
input_rail_status: passed
output_rail_status: passed
tool_names: includes a read/list tool when real MCP is used
```

What to show:

- green passed badge
- final response
- rail statuses
- tools used
- active policy/rule counts

Presentation line:

```text
Read-only GitHub activity passes through the same guardrail pipeline.
```

## Flow 6: Test A Blocked Write Request

Prompt:

```text
Use GitHub MCP to create an issue titled "test mcp" and description "hello" under github/github-mcp-server.
```

Expected result:

```text
status: blocked
input_rail_status: blocked
tool_names: []
```

What to show:

- red blocked badge
- safe refusal response
- no tool call executed
- policy/rule counts

Presentation line:

```text
The request stops before the GitHub MCP write tool can run.
```

## Flow 7: Disable The App Policy And Retest

Screen:

```text
Policies tab
```

User action:

```text
Disable assigned issue-creation block policy
```

Backend:

```text
PUT /apps/by-client-id/github-demo-bot/policy-assignments
```

Body:

```json
{
  "policy_ids": [12],
  "enabled": false
}
```

Retest the blocked write prompt.

Expected result:

- If backend `GITHUB_MCP_READ_ONLY=1`, the input rail may pass but GitHub MCP
  write action remains unavailable/read-only.
- If backend `GITHUB_MCP_READ_ONLY=0` and the PAT has issue write permission,
  the write action can execute.

Presentation note:

```text
Keep normal scripted tests read-only. Use write mode only for intentional manual demos with a throwaway repo/token.
```

## Figma Frames To Create

Recommended frames:

```text
1. Dashboard
2. Apps list
3. New app modal
4. App detail - overview
5. App detail - connectors
6. App detail - policies
7. Runtime tester - passed state
8. Runtime tester - blocked state
9. Policy library
10. Global policies / admin view
```

## UI States To Design

For each table/card, design:

- loading
- empty
- success
- error
- disabled
- destructive confirmation

Important badges:

```text
Authorized / Unauthorized
Connector enabled / disabled
Policy enabled / disabled
Input policy / Output policy
Global / App-specific
Passed / Blocked / Tool error
```

## What Not To Build First

Do not block the MVP on:

- real management login
- role-based admin protection
- SharePoint or Outlook
- visual drag-and-drop policy builder
- audit logs
- secrets manager UI

Those are later improvements. The first frontend should prove the GitHub MCP
guardrail management loop end to end.
