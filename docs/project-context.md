# Project Context: NeMo Guardrails + GitHub MCP

## Goal

Research NVIDIA NeMo Guardrails and test how guardrails can sit around an LLM that uses GitHub MCP tools.

Long-term project idea: build a web app for administrators to drag and drop app-specific policy blocks, such as "block create GitHub repo" or "block GitHub issue creation", which are then parsed into backend guardrail rules.

## Current Stack

- Python
- LangChain
- Azure OpenAI
- GitHub MCP Server via Docker
- NVIDIA NeMo Guardrails
- `.env` for secrets
- `.env.example` for shareable placeholders

## Current Working Result

The system successfully:

- Connects to GitHub MCP
- Loads MCP tools
- Uses Azure OpenAI to call MCP read tools
- Reads GitHub repositories, branches, and README files
- Runs NeMo `self check input` before the LangChain agent can call MCP tools
- Blocks unsafe write/credential prompts through NeMo input rails
- Keeps deterministic Python pre-checks only as a comparison/safety fallback

## Current Runtime Flow

```text
User prompt
-> Python pre-check report only
-> NeMo self_check_input using AzureChatOpenAI injected into LLMRails
-> if blocked: safe refusal and no MCP tool call
-> if passed: LangChain agent
-> GitHub MCP read-only tools
-> final answer
```

## Important Implementation Detail

NeMo input rails work when the project creates rails like this:

```python
rails_config = RailsConfig.from_path("config")
rails = LLMRails(rails_config, llm=model)
```

This matters because stock `GuardrailsMiddleware(config_path="config")` constructs its own internal NeMo LLM. In this environment, that path previously tried to use an old OpenAI/LangChain client and failed with `openai.ChatCompletion` / `APIRemovedInV1`.

## Prompt Design Status

`config/prompts.yml` currently defines `self_check_input` as a yes/no classifier:

- `no` means the request is allowed
- `yes` means the request asks for a restricted operation and should be blocked

This matches NeMo's default parser, where `yes` maps to unsafe/block and `no` maps to safe/allow.

## Known Issues

### NeMo Output Rails

Output rails are disabled for now.

Earlier NeMo output rail attempts caused false blocking because NeMo tried to invoke an old/default OpenAI path. Output rails should be debugged separately after input rails and tool-call rails are stable.

### Tool-Call Guarding Not Yet Implemented

Input rails catch user intent before the agent runs. The next major safety layer is tool-call guarding, where proposed MCP tool calls are checked before execution.

This matters because an ambiguous user prompt could still cause an LLM to choose a write-capable tool if such tools are ever available.
