# Policy Schema Design

## Purpose

This document sketches the next policy model for the guardrails management system before changing the database schema.

## Current Model

The current prototype stores simple policies:

```text
policy_type
app
action
resource
category
description
effect
enabled
```

Example:

```json
{
  "policy_type": "input",
  "app": "github",
  "action": "merge",
  "resource": "pull_request",
  "effect": "block",
  "enabled": true
}
```

This works for broad policies such as blocking all pull request merges.

## Current Limitations

The current model cannot express:

- repo-specific rules
- branch-specific rules
- file-path rules
- PR-number or PR-label rules
- approval/count-based rules
- ordered workflows
- stateful policies
- allow/block conflict priority

Example it cannot express yet:

```text
Allow merges only in order A -> B -> C.
Block B -> A -> C or any other order.
```

## Future Policy Types

```text
input
output
tool
argument
workflow
```

## Proposed Policy Fields

```text
id
policy_type
app
action
resource
effect
priority
enabled
conditions
metadata
created_at
updated_at
```

`conditions` should probably be JSONB in Postgres.

## Allowed Test Cases

Allowed test cases are separate from policies. They are safe prompts that the
test runner should expect to pass. Blocked tests are generated from active
blocking policies, so they do not need to be manually stored as test cases in
the first prototype.

```text
allowed_test_cases
------------------
id
name
prompt
expected_tools
enabled
created_at
updated_at
```

`enabled` means run or skip the test case. It does not mean allow or block.

Example:

```json
{
  "name": "Allowed: search repository",
  "prompt": "Use GitHub MCP to search repositories for github/github-mcp-server.",
  "expected_tools": "search_repositories",
  "enabled": true
}
```

## Compiled Policy Rules

Policies should remain the source of truth. Compiled policy rules are generated
artifacts that turn active policy objects into NeMo-friendly rule text.

This keeps the system split cleanly:

```text
policies
-> admin-created source of truth

compiled_policy_rules
-> generated input/output rail rule text

config/prompts.yml
-> stable NeMo prompt template
```

Proposed table:

```text
compiled_policy_rules
---------------------
id
policy_id
rail_type
rule_text
enabled
generated_at
created_at
updated_at
```

`rail_type` should currently support:

```text
input
output
```

Example input rule:

```json
{
  "policy_id": 12,
  "rail_type": "input",
  "rule_text": "Answer \"yes\" when the user asks to create, open, file, submit, raise, or log a GitHub issue or GitHub bug report.",
  "enabled": true
}
```

Example output rule:

```json
{
  "policy_id": 30,
  "rail_type": "output",
  "rule_text": "Answer \"yes\" when the assistant response reveals credentials, access tokens, API keys, hidden configuration files, .env contents, or environment variables.",
  "enabled": true
}
```

The prompt builder should load enabled compiled rules by rail type:

```sql
SELECT rule_text
FROM compiled_policy_rules
WHERE rail_type = 'input'
AND enabled = true
ORDER BY id;
```

Then it injects those rules into a stable prompt template.

Future `config/prompts.yml` shape:

```yaml
- task: self_check_input
  content: |
    Your task is to decide whether the user request should be blocked.

    Policy:
    {{ input_policy_rules }}

    User message:
    {{ user_input }}

    Answer only "yes" or "no".
```

The same pattern should be used for output rails with
`{{ output_policy_rules }}`.

## Conditions

Possible condition keys:

```text
repo
owner
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

## Enforcement Locations

```text
input policies
-> compiled_policy_rules where rail_type=input
-> NeMo input rail prompt template

output policies
-> compiled_policy_rules where rail_type=output
-> NeMo output rail prompt template

tool policies
-> tool_guard.py tool-name check

argument policies
-> tool_guard.py argument check before calling tool

workflow policies
-> workflow/state guard using database history
```

Compiled rule text should describe what NeMo can classify from language. Tool,
argument, and workflow policies still need Python-side enforcement because they
depend on proposed tool names, tool arguments, and runtime state.

## Example Policies

### Block All Pull Request Merges

```json
{
  "policy_type": "tool",
  "app": "github",
  "action": "merge",
  "resource": "pull_request",
  "effect": "block",
  "priority": 100,
  "enabled": true,
  "conditions": {}
}
```

### Allow Only Docs File Updates

```json
{
  "policy_type": "argument",
  "app": "github",
  "action": "update",
  "resource": "file",
  "effect": "allow",
  "priority": 200,
  "enabled": true,
  "conditions": {
    "file_glob": "docs/**"
  }
}
```

### Allow Merge Order A -> B -> C

```json
{
  "policy_type": "workflow",
  "app": "github",
  "action": "merge",
  "resource": "pull_request",
  "effect": "allow",
  "priority": 300,
  "enabled": true,
  "conditions": {
    "workflow_id": "release-merge-sequence",
    "allowed_sequence": ["A", "B", "C"]
  }
}
```

## Conflict Resolution

Proposed rule:

```text
higher priority wins
explicit block wins over allow at same priority
disabled policies are ignored
more specific conditions should use higher priority
```

## Migration Path

1. Keep the current `policies` table for prototype CRUD.
2. Add `priority` and `conditions` columns.
3. Support `policy_type=tool` and `policy_type=argument`.
4. Add `compiled_policy_rules` for generated NeMo input/output rule text.
5. Build a prompt builder that injects compiled rules into NeMo templates.
6. Add workflow state/history tables later.
7. Add opt-in write-mode tests only after argument/workflow guards exist.
