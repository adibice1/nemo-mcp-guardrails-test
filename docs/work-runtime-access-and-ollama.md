# Work Runtime Access And Ollama - 2026-10-21

Latest checkpoint: the user verified Azure / nemo_restore_check_20261016 and
installed/selected qwen2.5:1.5b for Test app 3. Follow the
[acceptance results and manual checklist](work-acceptance-2026-10-21.md).
The findings below describe the earlier inspection, before those user actions.

## Read-Only Findings

- Backend listens on 127.0.0.1:8000; frontend listens on port 3000.
- The backend PostgreSQL socket's destination matches the resolved Azure server
  guardrails-postgresql.postgres.database.azure.com. This establishes the server,
  not the selected database. No database-name verification was possible from the
  agent's separate environment.
- Root .env selects 127.0.0.1:5432/nemo_mcp_guardrails. The agent's shell has no
  DATABASE_URL override. Do not use it for presumed Azure rehearsal commands.
- Ollama 0.40.4 is installed and /api/tags responds on 127.0.0.1:11434. Installed
  models are llama3.2:latest and gemma4:latest. qwen2.5:1.5b is not installed here.
- Browser inventory is empty; an attempt to open the built-in browser returned
  "Browser is not available: iab". No authenticated GMS session is available to
  the agent. No login credential or app key has been requested in chat.

No database mutation, model download, credential/configuration change or GitHub
write ran during these checks. Production cutover remains unperformed.

## Verify The Backend Database

In the PowerShell window running scripts/run_api.py, stop the backend with Ctrl+C.
Stay in that same window, at the project root, so its process environment override
is retained. Run:

```powershell
@'
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

load_dotenv(".env")
url = make_url(os.environ["DATABASE_URL"])
assert url.host == "guardrails-postgresql.postgres.database.azure.com", "Wrong server; do not start tests."
assert url.database == "nemo_restore_check_20261016", "Wrong database; do not start tests."
engine = create_engine(url)
try:
    with engine.connect() as connection:
        actual = connection.scalar(text("SELECT current_database()"))
    assert actual == "nemo_restore_check_20261016", "Unexpected connected database."
    print("Host:", url.host)
    print("Database:", actual)
    print("Verified rehearsal target.")
finally:
    engine.dispose()
'@ | .\.venv\Scripts\python.exe -B -
```

Restart from that same window only after success:

```powershell
$env:GITHUB_MCP_READ_ONLY = "1"
.\.venv\Scripts\python.exe -B scripts/run_api.py
```

The snippet reads environment overrides ahead of .env and does not print a URL,
password or key. Failure is a reason to restore the private rehearsal override,
not to migrate whichever database .env happens to name. A query run in DBeaver
verifies that DBeaver session, not the backend. Frontend requests use the backend
selected by GMS_API_BASE_URL; the frontend does not choose a database directly.
For this local pair its proxy target should be http://127.0.0.1:8000. Verify in
the frontend's own startup environment; the agent has not inspected that running
process's environment.

## Shared Browser And Test Inputs

In the ChatGPT desktop app, open a built-in browser tab to
http://localhost:3000/login, sign in privately, then reference @Browser in this
conversation. Its profile is separate from an ordinary Chrome login. If the
built-in browser is unavailable, the official browser extension and @Chrome are
the alternative where supported by the workspace. Do not expose the local app
publicly just to make it reachable to a cloud browser.

Needed inputs/access:

1. The safe verification result above (host and database only).
2. A connected browser with the admin/dev test identities already provided;
   the user enters passwords and handles any MFA privately. Test roles in separate
   sessions or switch explicitly; a developer session cannot perform admin checks.
3. The test app identity: Test app 3, client ID
   f496bd22-bdfc-417d-85ac-f25ec53bd599, unless the user chooses another app.
4. That app's runtime key entered privately in Runtime Test. A runtime key alone
   does not authorize management/profile mutations. If direct HTTP testing is
   chosen instead, establish scoped private test-auth storage first; never put
   keys/JWTs in chat, docs, URLs or shell history.
5. Existing GMS GitHub connector credentials capable of the approved repository
   operations. Test existing access first; no replacement PAT is needed unless
   access fails. The ChatGPT GitHub connector's access is a separate identity.

The repository adibice1/nemo-mcp-guardrails-test and closing created test PRs are
already authorized. No further repository choice or blanket permission is needed.
Use GMS for enforcement evidence. No pushes, merges or new branches are implied.
Keep normal tests read-only; any controlled write window is limited to the
authorized PR test and followed by cleanup/restoring read-only mode.

## Local Ollama Main-Agent Setup

Installation/server startup is already complete here. On another Windows machine,
install from the official Windows download and launch Ollama. Its normal server
runs in the background; only use ollama serve if no server is already running.

For the same small main-agent candidate previously tested at home, run:

```powershell
ollama pull qwen2.5:1.5b
ollama list
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```

This download has not been executed by the agent. Existing llama3.2/gemma4 models
are available but have not passed this project's main-agent/tool tests here.
Further local classifier downloads/evaluations remain postponed; retain Azure
classification.

Merge these values into the backend's private configuration, preserving existing
allowlist entries and Azure settings. The allowlists are comma-separated:

```dotenv
GMS_ALLOWED_COMPATIBLE_LLM_ENDPOINTS=http://127.0.0.1:11434/v1
GMS_ALLOWED_LLM_CREDENTIAL_ENV_VARS=OLLAMA_LOCAL_KEY
OLLAMA_LOCAL_KEY=ollama-local-placeholder
```

The dummy local key satisfies the client/profile validation; local Ollama ignores
its value. These settings are backend approval metadata, not an app grant. Restart
the backend in the verified rehearsal PowerShell window after configuration edits.

Current admin UI: Apps > test app > Models > Add model profile. Select
openai_compatible, model qwen2.5:1.5b, endpoint
http://127.0.0.1:11434/v1 and credential environment variable OLLAMA_LOCAL_KEY
(API reference env:OLLAMA_LOCAL_KEY). Approve the profile for that app's Main
agent purpose, select it and save; leave the Azure classifier selected. The
requested developer registration UI is pending and cannot be used yet.

Validate a fresh runtime conversation with an actual GitHub read and its tool
call/result trace, then switch the main selection back to Azure and compare.
An HTTP 200 or a plausible answer alone does not establish working tool calling.
Loopback works for the current Windows source backend; a container's loopback
is different and requires a separately reviewed network configuration. Do not
expose Ollama publicly or disable endpoint restrictions to connect it.

References: [OpenAI browser guide](https://learn.chatgpt.com/docs/browser),
[Ollama Windows](https://docs.ollama.com/windows), and
[Ollama OpenAI compatibility](https://docs.ollama.com/api/openai-compatibility).
