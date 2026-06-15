# Policy Schema Design

## Target Terminology Update

The confirmed production meaning of `app` has changed:

```text
app       = client application consuming the GMS
connector = external integration such as GitHub MCP, SharePoint, or Outlook
```

The terminology migration is complete:

```text
apps                    = client applications consuming the GMS
connectors              = external integrations
connector_actions       = actions supported by connectors
connector_resources     = resources supported by connectors
connector_tool_mappings = concrete connector tool mappings
```

The target schema must also introduce:

```text
users
apps
app_users
app_connectors
llm_configs
policy_rules
app_policy_assignments
global_policy_assignments
```

See `docs/target-architecture.md` for the authoritative confirmed target
design. Some SQL examples below record the historical pre-rename schema and are
labelled accordingly.

## Purpose

This document defines the next normalized database shape for the guardrails
management system.

The goal is to support many apps, each with its own actions, resources, tools,
policy rules, test cases, and compiled NeMo prompt rules without hardcoding all
policy data in Python files.

## Current Working Flow

The current runtime flow is:

```text
Postgres policies
-> policy_loader.py
-> policy_compiler.py
-> compiled_policy_rules
-> prompt_rule_loader.py
-> prompt_rule_compiler.py
-> config/prompts.yml template
-> NeMo input/output rails
-> scripts/test_nemo_mcp.py terminal output
```

This is now DB-backed, but the main `policies` table is still flat:

```text
policy_type
connector
action
resource
category
description
effect
enabled
```

That flat shape works for the GitHub prototype, but it will become difficult to
maintain when the system supports Slack, Jira, Google Drive, databases, or other
apps with different actions/resources/tools.

## Normalization Goals

The normalized model should:

- store each connector once
- store valid actions per connector
- store valid resources per connector
- map connector/action/resource combinations to concrete tool names
- keep policies as the source of truth
- keep compiled NeMo rules as generated artifacts
- keep allowed test cases separate from block policies
- support future argument and workflow conditions
- avoid duplicating strings such as `github`, `pull_request`, and `merge`

## Proposed Core Tables

### connectors

One row per supported external connector.

```sql
CREATE TABLE connectors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(200) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Example:

```text
github -> GitHub
jira -> Jira
slack -> Slack
```

### connector_actions

Actions supported by one connector.

```sql
CREATE TABLE connector_actions (
    id SERIAL PRIMARY KEY,
    connector_id INTEGER NOT NULL REFERENCES connectors(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (connector_id, name)
);
```

GitHub examples:

```text
create
update
comment
merge
review
push
fork
delete
```

Slack examples:

```text
send
update
delete
invite
```

### connector_resources

Resources supported by one connector.

```sql
CREATE TABLE connector_resources (
    id SERIAL PRIMARY KEY,
    connector_id INTEGER NOT NULL REFERENCES connectors(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (connector_id, name)
);
```

GitHub examples:

```text
issue
pull_request
branch
file
repository
```

Slack examples:

```text
message
channel
user
```

## Policy Source Of Truth

### policies

The policy row says what should be allowed or blocked. It references normalized
connector/action/resource rows instead of storing repeated strings.

```sql
CREATE TABLE policies (
    id SERIAL PRIMARY KEY,
    policy_type VARCHAR(30) NOT NULL,
    connector_id INTEGER REFERENCES connectors(id) ON DELETE RESTRICT,
    action_id INTEGER REFERENCES connector_actions(id) ON DELETE RESTRICT,
    resource_id INTEGER REFERENCES connector_resources(id) ON DELETE RESTRICT,
    category VARCHAR(100),
    description TEXT,
    effect VARCHAR(20) NOT NULL DEFAULT 'block',
    priority INTEGER NOT NULL DEFAULT 100,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Expected `policy_type` values:

```text
input
output
tool
argument
workflow
```

Expected `effect` values:

```text
allow
block
```

Notes:

- `input` policies describe user intent that NeMo should block before action execution.
- `output` policies describe unsafe assistant responses.
- `tool` policies block/allow tool names before execution.
- `argument` policies inspect tool arguments.
- `workflow` policies depend on stored state/history.
- Output policies may not need `action_id` or `resource_id`; they may use `category` instead, such as `credentials`.

### policy_conditions

Future optional table for structured conditions if JSONB on `policies` becomes
too hard to query or validate.

```sql
CREATE TABLE policy_conditions (
    id SERIAL PRIMARY KEY,
    policy_id INTEGER NOT NULL REFERENCES policies(id) ON DELETE CASCADE,
    condition_key VARCHAR(100) NOT NULL,
    operator VARCHAR(50) NOT NULL DEFAULT 'equals',
    condition_value JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Possible condition keys:

```text
owner
repo
branch
base_branch
head_branch
file_path
file_glob
pr_number
labels
required_approvals
allowed_sequence
current_state
```

Example:

```json
{
  "condition_key": "file_glob",
  "operator": "matches",
  "condition_value": "docs/**"
}
```

## Tool Mapping Tables

### connector_tool_mappings

Maps normalized connector/action/resource concepts to actual connector or MCP tool
names.

```sql
CREATE TABLE connector_tool_mappings (
    id SERIAL PRIMARY KEY,
    connector_id INTEGER NOT NULL REFERENCES connectors(id) ON DELETE CASCADE,
    action_id INTEGER NOT NULL REFERENCES connector_actions(id) ON DELETE CASCADE,
    resource_id INTEGER NOT NULL REFERENCES connector_resources(id) ON DELETE CASCADE,
    tool_name VARCHAR(200) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (connector_id, action_id, resource_id, tool_name)
);
```

GitHub examples:

```text
github create issue        -> issue_write
github update issue        -> issue_write
github comment issue       -> add_issue_comment
github create pull_request -> create_pull_request
github update pull_request -> update_pull_request
github merge pull_request  -> merge_pull_request
github review pull_request -> pull_request_review_write
github create branch       -> create_branch
github update file         -> create_or_update_file
```

This table is the normalized replacement for hardcoded tool mappings in
`policy_compiler.py`.

Policy CRUD also uses enabled rows in this table as the capability catalogue.
After resolving readable app/action/resource names into IDs, the API accepts an
input policy only when at least one enabled mapping exists for that exact
combination.

```text
github + merge + pull_request -> accepted
github + merge + issue        -> rejected
```

This scales with the number of supported capabilities, not every theoretical
combination. Invalid combinations do not need rows.

## Prompt Rule Artifacts

### compiled_policy_rules

Generated NeMo rule text derived from enabled source policies.

```sql
CREATE TABLE compiled_policy_rules (
    id SERIAL PRIMARY KEY,
    policy_id INTEGER NOT NULL REFERENCES policies(id) ON DELETE CASCADE,
    rail_type VARCHAR(20) NOT NULL,
    rule_text TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Expected `rail_type` values:

```text
input
output
```

Important:

- `policies` remain the source of truth.
- `compiled_policy_rules` are generated artifacts.
- `prompt_rule_loader.py` reads this table.
- `prompt_rule_compiler.py` injects enabled rules into `config/prompts.yml`.

## Test Tables

### allowed_test_cases

Allowed test cases are safe prompts expected to pass. They are not allow/block
policies.

```sql
CREATE TABLE allowed_test_cases (
    id SERIAL PRIMARY KEY,
    app_id INTEGER REFERENCES apps(id) ON DELETE SET NULL,
    name VARCHAR(200) NOT NULL,
    prompt TEXT NOT NULL,
    expected_tools TEXT,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### allowed_test_case_expected_tools

Expected tools are a many-to-many relationship:

```text
one allowed test case can expect multiple tools
one tool mapping can be reused by multiple allowed test cases
```

The API now accepts readable expected-tool name lists and maintains this join
table directly. The comma-separated `allowed_test_cases.expected_tools` column
is synchronized temporarily as a compatibility fallback.

```sql
CREATE TABLE allowed_test_case_expected_tools (
    id SERIAL PRIMARY KEY,
    allowed_test_case_id INTEGER NOT NULL REFERENCES allowed_test_cases(id) ON DELETE CASCADE,
    connector_tool_mapping_id INTEGER NOT NULL REFERENCES connector_tool_mappings(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (allowed_test_case_id, connector_tool_mapping_id)
);
```

Blocked test cases are generated from active block policies, so they do not need
to be manually stored in the first normalized version.

## Future Workflow Tables

Workflow policies need state, not only prompt classification.

### workflow_definitions

```sql
CREATE TABLE workflow_definitions (
    id SERIAL PRIMARY KEY,
    app_id INTEGER NOT NULL REFERENCES apps(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (app_id, name)
);
```

### workflow_events

```sql
CREATE TABLE workflow_events (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER NOT NULL REFERENCES workflow_definitions(id) ON DELETE CASCADE,
    policy_id INTEGER REFERENCES policies(id) ON DELETE SET NULL,
    app_id INTEGER NOT NULL REFERENCES apps(id) ON DELETE CASCADE,
    action_id INTEGER REFERENCES connector_actions(id) ON DELETE SET NULL,
    resource_id INTEGER REFERENCES connector_resources(id) ON DELETE SET NULL,
    actor VARCHAR(200),
    event_payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

This is what future policies like `allow merge A -> B -> C only` would use.

## Example Normalized GitHub Policy

Human meaning:

```text
Block GitHub pull request merges.
```

Normalized rows:

```text
connectors
- id=1, name=github

connector_actions
- id=6, connector_id=1, name=merge

connector_resources
- id=2, connector_id=1, name=pull_request

policies
- policy_type=input, connector_id=1, action_id=6, resource_id=2, effect=block

connector_tool_mappings
- connector_id=1, action_id=6, resource_id=2, tool_name=merge_pull_request

compiled_policy_rules
- policy_id=<policy id>, rail_type=input, rule_text=Answer "yes" when...
```

## Loader Behavior After Normalization

`policy_loader.py` should eventually join:

```text
policies
-> connectors
-> connector_actions
-> connector_resources
```

and still return the same compiler object:

```python
InputPolicyObject(
    connector="github",
    action="merge",
    resource="pull_request",
    effect="block",
)
```

This keeps the current compiler/test runner stable while the DB becomes more
normalized underneath.

## Compiler Behavior After Normalization

Short term:

```text
policy_loader.py joins normalized tables
-> policy_compiler.py still uses Python mappings/synonyms
```

Long term:

```text
policy_loader.py joins normalized tables
-> policy_compiler.py reads DB connector_tool_mappings and synonym/template tables
```

So normalization can happen in stages without rewriting the whole compiler at
once.

## Migration Plan

The previous normalization migration is complete for the GitHub prototype.
Before further production-schema work, a new migration plan must separate
client apps from connectors and preserve the existing GitHub metadata during
the rename.

Current migration status:

1. Completed: create normalized metadata tables.
2. Completed: add normalized columns to `policies`.
3. Completed: seed GitHub app/action/resource/tool mapping rows.
4. Completed: backfill existing policy strings into FK IDs.
5. Completed: make `policy_loader.py` prefer normalized relationships.
6. Completed: add `policy_version` and `stale` lifecycle fields.
7. Transitional: keep old string columns as fallback/debug fields.
8. Completed: policy create/update accepts readable names and resolves normalized IDs.
9. Completed: validate action/resource combinations against enabled tool mappings.
10. Completed: add `app_policy_assignments` and `global_policy_assignments`.
11. Completed: add app and policy-assignment CRUD APIs.
12. Completed: make policy and compiled-prompt-rule loading assignment-aware.
13. Completed: make `tool_guard.py` capable of applying per-app blocked-tool sets.
14. Completed: wire testing-only app scope through NeMo rails and the tool guard.
15. Completed: add reusable app credential hashing and verification.
16. Completed: enforce app authentication at the HTTP runtime boundary.
17. Completed: scaffold authenticated `POST /v1/guardrails/run` and pass its
    app ID through prompt-rule, policy, and blocked-tool context loading.
18. Completed: extract reusable one-message guarded execution from the full
    test runner.
19. Next: execute that guarded pipeline behind the run endpoint.
20. Later: remove old string columns after stable verification.

## Proposed Implementation Slices

### Slice 1: Add normalized tables without breaking current runtime

Add new ORM models and create metadata/test join tables. Keep existing flat columns in `policies`.

### Slice 2: Seed normalized GitHub metadata

Seed:

```text
connectors
connector_actions
connector_resources
connector_tool_mappings
```

from the current GitHub policy compiler metadata.

The current prototype also seeds a generic row:

```text
connectors.name = global
```

Generic cross-app output policies such as credentials, secrets, API keys, and
PII currently uses `connector_id=global`. Connector-specific output policies
use the relevant connector ID, such as `github`, `sharepoint`, or `outlook`.

This is transitional prototype behavior. In the confirmed target schema,
mandatory global policies belong in `global_policy_assignments`; they should
not be represented by a fake client app or connector named `global`.

### Slice 3: Backfill policies

Populate `policies.connector_id`, `policies.action_id`, and `policies.resource_id`
from existing text values. Completed by
`scripts/migrate_normalized_policy_references.py`.

### Slice 4: Update loaders

Make `policy_loader.py` read normalized joins when FK columns exist, with
fallback to the current text columns. Completed.

### Slice 5: Move compiler mappings into DB

Once normalized policy loading is stable, gradually replace hardcoded
`policy_compiler.py` mappings with DB-backed `connector_tool_mappings` and later
synonym/template tables.

## Design Decisions

### Client Apps And Connectors

One client app can use multiple connectors, and one connector can be used by
multiple client apps:

```text
apps
-> app_connectors
-> connectors
```

Connector credentials are app-specific because App A and App B may use the
same GitHub or SharePoint connector with different permissions.

### Reusable Rules And App Assignments

Reusable rules should be stored separately from app-specific assignments:

```text
policies
-> app_policy_assignments
-> apps
```

This lets multiple apps share the same rule while enabling or deleting that
rule assignment independently for each app.

Mandatory rules use `global_policy_assignments` and apply to every app.

Current implementation keeps `policies` as the reusable rule-definition table
instead of copying the same definitions into a second `policy_rules` table.
The table can be renamed later if the clearer name becomes worthwhile.

Current management endpoints:

```text
/apps
/apps/{app_id}/policy-assignments
/global-policy-assignments
```

These endpoints manage assignment rows. Policy and compiled-rule loaders now
filter by assignment when an app ID is supplied. The reusable HTTP dependency
authenticates an app before runtime work begins, and the next implementation
slice connects the reusable guarded execution now used by the full test runner
to the authenticated context already prepared by `POST /v1/guardrails/run`.

### Automatic Compilation

The target system should not require administrators to manually call
`POST /policies/compile-rules`.

```text
rule or assignment changes
-> mark compiled artifacts stale
-> compile active rules
-> store current artifacts
-> invalidate runtime cache
```

### Output Policy Scope

Output policies can be assigned to specific client apps when needed, while
mandatory cross-app policies use `global_policy_assignments`:

```text
global credentials block
global PII block
global secret leakage block
```

Use app-specific assignments for output policies that only apply to one client
app. Connector-specific rule definitions can still identify the relevant
connector:

```text
github repository metadata output policy
sharepoint document output policy
outlook email output policy
```

### Allowed Test Expected Tools

Expected tools should become a join table instead of comma-separated text.

Current prototype:

```text
allowed_test_cases.expected_tools = "search_repositories,get_file_contents"
```

Normalized target:

```text
allowed_test_cases
-> allowed_test_case_expected_tools
-> connector_tool_mappings
```

### Policy Conditions

Use a JSONB object on `policies` first:

```sql
conditions JSONB NOT NULL DEFAULT '{}'
```

This matches the policy-object shape and keeps the compiler simple:

```json
{
  "file_glob": "docs/**",
  "branch": "main",
  "required_approvals": 2
}
```

A separate `policy_conditions` table can be added later if the admin UI needs
advanced filtering, validation, or reporting by condition key/operator.

### Generated Blocked Test Cases

Generated blocked tests should be regenerated every test run:

```text
DB policies
-> policy_loader.py
-> policy_compiler.py
-> generated blocked test prompts
```

This keeps test output aligned with the latest enabled policies.

Future optimization can cache generated tests in memory, but only with policy
version or `updated_at` checks so stale tests are not reused.

### Compiled Policy Rule Invalidation

`ON UPDATE CASCADE` is not enough for `compiled_policy_rules`, because it only
updates foreign key values. It does not regenerate derived rule text.

Use explicit stale/version tracking instead:

```text
policies.policy_version
compiled_policy_rules.policy_version
compiled_policy_rules.stale
```

Recommended behavior:

```text
policy create/update/delete
-> mark related compiled_policy_rules stale

POST /policies/compile-rules
-> regenerate compiled rules
-> store current policy_version
-> clear stale flag
```

This gives the admin/API layer a clear signal when compiled prompt rules need
regeneration.
