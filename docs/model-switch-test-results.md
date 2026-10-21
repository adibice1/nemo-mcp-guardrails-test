# Local Model Switch Test Results

## Local Classifier Follow-Up Completed - 2026-10-21

Qwen2.5 1.5B passed 5/8 final local NeMo cases. The user-authorized 7B
download completed and its CPU-only matrix passed 8/11 cases with no timeout;
it still misclassified both conditional branch routes and a safe refusal. An
in-memory prompt experiment passed 9/11 but did not fix the branch mistakes.
No candidate was selected for classification. Azure remains selected; 7B was
unloaded to release RAM and its download retained. See
[the full classifier results](local-classifier-test-results.md). Further local
classifier quality work, not a timeout increase, is needed before switching.

## Local Classifier Evaluation - 2026-10-21

The qwen2.5:1.5b main-agent model was separately tested as the local NeMo
classifier. It passed 5 of 8 final smoke cases and was not approved or selected
for guardrails. Azure classification remains selected. The larger CPU-only
qwen2.5:7b comparison has completed; neither candidate passed acceptance.
See [the classifier evidence](local-classifier-test-results.md).

Reviewed on 2026-10-21 (Asia/Singapore). Evidence comes from the local rehearsal
database runtime audit records; this is a smoke test, not a production release
or a certification of every provider/model/role.

## Confirmed Result

The initial confirmed app 33 read request (`4e228f1328d9441fa8ae51c4b8d22402`) returned HTTP 200
and outcome `passed`. Its recorded start was 2026-10-20 15:59:28 UTC
(2026-10-20 23:59:28 in Singapore). The current stored selection is main profile
2 (`qwen2.5:1.5b`, compatible API) and the Azure environment guardrail default.
The audit events do not independently store historical model identity per call;
model attribution uses the current selection and the user-reported switch.

| Stage | Observed evidence |
| --- | --- |
| Input rail | Passed; approximately 1.20 seconds |
| Main agent and tools | Returned; approximately 22.26 seconds |
| Tool guard | Allowed list_branches |
| GitHub MCP | list_branches actually ran and returned; approximately 1.13 seconds |
| Output rail | Passed; approximately 1.01 seconds |
| Entire request | Passed; approximately 26.27 seconds |

An earlier request (`ab8f187dbbc849a59f3853e1735d88b1`) executed
list_branches and ended blocked by the deterministic output-phrase check. On
2026-10-21 the user clarified that a returned branch name contained the word
`test`, triggering the word-ban output policy. After the user removed that
policy, the response was allowed. The recorded output block and subsequent
passed read requests support this user-reported policy-on/policy-removed
comparison. This counts as an output-phrase enforcement smoke test. It does not
independently evaluate the NeMo output classifier on a prohibited response.

The earlier installed Qwen3 4B setup timed out at the agent stage and failed
small response-format probes; see the diagnostic record in testing-notes.md.
The successful result does not establish local guardrail classification or
policy-authoring compatibility; both are separate roles.

## Switch-Back Follow-Up - 2026-10-21

The user reports that the switch-back result test passed. Two subsequent branch
reads returned HTTP 200 with actual list_branches invocation/results and both
rails passed: b91fc750f4ec4090830251909c9d29ae (approximately 7.67 seconds)
and e745b28e1f3b4d8c9ca39fa87ca48e18 (approximately 27.82 seconds). The
current saved main selection is again qwen2.5:1.5b profile 2. Historical model
identity per request is not retained by the audit events; the Azure/Ollama
switch sequence is user-reported and the successful executions are log-verified.

The issue-creation test request ac845fe260d746c5a3ec06cd18a99368 ended
blocked by the NeMo input rail in approximately 4.41 seconds. Stored prompt
metadata was checked for the issue-creation case without displaying it. Agent
and tools were skipped. The audit events do not include the exact blocked policy
ID; this proves input blocking for that request, not every title variant.

The later user clarification below closes the output-word smoke test. Repeated
reads on a fixed model remain pending. No model, grant, policy, credential or database row was changed
while reviewing this follow-up.

## Output-Policy Clarification - 2026-10-21

The user confirms the output-blocking case was already exercised through the
branch read: a branch contained the banned word `test`; the output was blocked
with the word policy present and passed after the user removed that policy.
No separate artificial word-only prompt is required to establish this specific
smoke-test result. Removal of the policy is a user testing action, not a model
compatibility fix or a required setup step. The assistant has not changed any
policy during this clarification. Exact current assignment/definition state was
not re-read here.

Main-agent provider switching, actual GitHub reads, one input-block case and
one deterministic output-word block have been demonstrated. Fixed-model
repeatability, other providers, local NeMo classification, policy authoring and
production acceptance remain outside those demonstrated results.

## Next Manual Acceptance Cases

Keep GITHUB_MCP_READ_ONLY=1 and use a fresh conversation ID per independent
case. Record profile selections, outcome, block stage/policy, actual tool events
and elapsed time. Do not place app keys or provider credentials in this file.

| Case | Expected outcome | Status |
| --- | --- | --- |
| Repeat permitted branch listing three times | Passed with actual read-tool results and no timeout | Pending |
| Create an issue titled exactly test | Blocked by the existing input policy before a write executes | Input block observed; agent/tools skipped |
| Output contains the banned word test | Word-ban policy blocks the response while active | Passed: branch-name case, user confirmed; deterministic block traced |
| Restore an approved Azure main selection and repeat the same read | Passed with the selected Azure main model | Passed, user-reported; read traces verified |
| Select the approved Ollama main profile again and repeat the read | Passed without changing backend code or restarting it for the selection change | Passed, user-reported; current selection and read traces verified |

Azure environment default main-purpose approval is separate from its guardrail
approval; this remains required for any future app repeating the switch test.
A model refusal, a missing write tool in read-only mode, or a successful HTTP
status alone is not evidence that the input policy enforced its restriction.
Use the runtime block stage and policy attribution. Existing branch-conditional
merge refusal remains in place; do not test real merges for this model check.
