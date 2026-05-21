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
- Blocks unsafe write/credential prompts using deterministic Python pre-checks

## Known Issue

NeMo output rails currently fail when enabled because NeMo tries to call `gpt-3.5-turbo` through an old OpenAI path. This causes allowed outputs to be replaced with:

"I cannot provide this response due to content policy."

This is not because the output rail policy is too strict. It is because the NeMo output rail LLM initialization path is failing.