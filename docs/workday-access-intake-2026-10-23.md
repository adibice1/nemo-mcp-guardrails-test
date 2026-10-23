# Workday manual access intake - 23 October 2026

The user authorized automation, but requested collection of missing manual
information before provisioning/deployment starts. This intake prepares access;
it does not create a database, restore a backup, publish or update a deployment.
Existing fresh-release authority and supervisor ownership remain unchanged.

## Work-machine preflight

Azure CLI and Docker are installed here; Docker engine responds. CLI has no
signed-in account. PostgreSQL 18 psql/pg_dump/pg_restore executables exist under
`C:\Program Files\PostgreSQL\18\bin`; the work Python venv exists. Local Docker
currently lists guardrail-be:latest and guardrail-fe:latest; the home machine's
commit-tagged images are not assumed to exist here. The agent can inspect/rebuild
the pair and discover Azure resource names after authentication.

## Required manual actions and answers

Run these in PowerShell on this work computer. Do not paste passwords, device
codes, tokens, connection strings, `.env` or backup contents into chat.

### 1. Sign in to Azure

```powershell
az login --use-device-code
az account show --query "{name:name,id:id}" --output json
```

Complete the browser/MFA step using the account authorized for this deployment.
The device code belongs only in Microsoft's sign-in flow. If device-code login
is blocked by organizational policy, use normal interactive `az login` instead.
See [Microsoft's interactive CLI sign-in guidance](https://learn.microsoft.com/cli/azure/authenticate-azure-cli-interactively).

If multiple subscriptions are available, identify the intended one; the agent
can list them after login. No token export or registry password is needed in chat.
Reply with login readiness and intended subscription name/ID if needed.

### 2. Supply database access privately

```powershell
Set-Location -LiteralPath 'C:\Users\User\Downloads\nemo-mcp-guardrails-test'
.\.venv\Scripts\python.exe -B .waylog\release-access-20261023\capture_database_access.py
```

The operational helper was prepared in this current workspace's ignored folder;
it is not committed or a portable application bootstrap script. It uses an
existing Azure DATABASE_URL from the terminal/private dotenv if available;
otherwise it prompts for the existing DBeaver database/user and a hidden password.
It requires the recorded Azure host and TLS, verifies database identity using a
read-only connection and reports only safe identity/role metadata. No schema/data
is changed. It does not create the proposed fresh database.

After verification it exclusively creates Git-ignored
`.waylog/release-access-20261023/database-access.env`, containing the connection
for the authorized work. Do not open/paste that file. The agent must remove it
after the operations no longer require it. Existing `.env` is not rewritten.
Reply `Database access ready` or the helper's sanitized failure status.

### 3. Choose the fresh database name

Proposed name: `nemo_gms_release_20261023`. Reply with that name or an alternative.
The agent will check that it does not already exist. An existing database must
never be cleared or overwritten to satisfy the fresh-data plan.

### 4. Identify the backup and protected handover destination

Provide the existing backup's full path and the agreed private storage/location
where the supervisor should receive backups/configuration/keys. To print only
backup file metadata:

```powershell
$gmsBackupPath = Read-Host 'Full path of the existing database backup'
Get-Item -LiteralPath $gmsBackupPath | Select-Object FullName,Length,LastWriteTime
```

If the backup's location is unknown, say so; do not copy its contents into chat.
The agent can inspect the archive and restore to a separate controlled target
once access is available. Private destination custody and actual receipt still
need the supervisor; a local file copy alone does not establish handover.

### 5. Identify configuration and credential ownership

State whether the current work `.env` Azure/GitHub credentials are approved for
the supervisor-managed release or must be replaced by supervisor-owned ones.
Give only the location/reference of any existing deployment configuration or
protected secret store, or say `unknown`. Preserve old secret/key configuration
for rollback. Never send secret values in chat. The fresh dataset's signing/
encryption secrets can be generated privately rather than typed by the user.

### 6. Confirm supervisor availability/access

When can the supervisor perform the first password replacement? Their account
identity is already agreed as `admin@gmail.com`; do not ask for a permanent
password. Temporary setup passwords expire after 24 hours. Also report whether
they have independent Azure, registry and PostgreSQL access: yes/no/unknown.
App admin status does not establish those external permissions.

### 7. State the deadline and restart constraints

Give the last available work time in Singapore time and any window when the
existing service must not be interrupted. Deployment is already authorized;
this is scheduling information, not a new approval request.

## Copyable reply

```text
Azure login: ready / blocked
Intended subscription: default / name or ID
Database access: ready / sanitized failure
Fresh database name: nemo_gms_release_20261023 / alternative
Existing backup path:
Protected handover destination:
Current work Azure/GitHub credentials: reuse / replace / unsure
Existing deployment config or secret-store location: path/reference / unknown
Supervisor first-login availability:
Supervisor independent Azure/registry/PostgreSQL access: yes/no/unknown for each
Hard stop today (Singapore time):
Restart constraints: none / times to avoid
```

Once these are supplied, automate guarded discovery, backup/schema checks,
fresh initialization/bootstrap, publication/deployment and narrow acceptance as
access permits. Preserve old databases and keys, use read-only GitHub checks,
record actual results and complete private handover. Do not repeat already
accepted full suites simply to produce another passing result.
