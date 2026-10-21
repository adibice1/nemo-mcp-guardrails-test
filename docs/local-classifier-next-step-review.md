# Local Classifier Follow-Up Review

Reviewed on 2026-10-21 (Asia/Singapore). All changes below were experiments
in memory. No runtime source/prompt file, database policy, app grant, model
selection or .env setting was changed. Existing exact conditions still apply
in NeMo and in the execution-level tool guard. No GitHub action or Azure model
call was made.

## User Requirement

The user explicitly chose to KEEP exact conditions in NeMo too. Do not resolve
the local-model errors by removing or delegating those conditions solely to
tool execution. Existing selective branch-merge refusal remains mandatory.

## Experiments

| Experiment | Result | Decision |
| --- | --- | --- |
| Qwen2.5 7B with generated branch exemptions and clearer task guidance | 10/11 original cases | Missed a restricted branch route |
| Generated condition table | 10/11 original; 7/9 new wording/case checks | Not sufficient |
| Typed intent extraction plus existing deterministic comparison | 9/10 branch cases | Injection falsified operation to other; do not integrate |
| Separate trusted system instructions and classified user text | 10/11 original | Exempt route still blocked |
| Roles plus condition table | 11/11 original, but 8/12 new/adversarial cases | Do not apply a patch on the original score alone |
| Qwen3 4B, roles and 512-token reasoning budget | First two checks each hit the 45-second diagnostic timeout | Stopped remaining cases |
| Qwen3 4B, roles, reasoning_effort none, 32-token budget | First two checks each hit the 45-second diagnostic timeout | Stopped remaining cases |

For the combined 7B candidate, fresh checks exposed false positives for target
branch capitalization, read-only PR inspection and a different issue title.
An instruction asking the classifier to pretend the source was staging also
produced a missed restriction. Structured extraction is not an authorization
boundary without additional validation: schema-valid fields can still be false.

The Qwen3 limits above were isolated diagnostic deadlines, not changes to the
GMS 60-second model-client or 120-second outer-runtime budgets. They do not
prove the model can never complete with different resources/settings.

## Current State And Next Candidate

Azure remains the guardrail classifier. Qwen2.5 1.5B remains the main-agent
selection. Qwen3 was unloaded after the timed checks to release memory; model
downloads remain installed. There is no production-ready prompt/code patch to
approve from these experiments. Do not apply a partial candidate or silently
weaken/remove policies to obtain a passing local test.

A different local model family, llama3.1:8b, was proposed for the same acceptance
cases. Its official Ollama listing gives a download size of about 4.9 GB. The
user postponed further downloads/tests on 2026-10-21 before moving to the work
computer. Llama was not downloaded; do not start it automatically. Continue with
the [work-computer checklist](work-computer-model-test-checklist.md). If classifier
work is resumed later, start with unchanged prompts before experimental variants.

Reference: [Ollama Llama 3.1 8B listing](https://ollama.com/library/llama3.1:8b).
