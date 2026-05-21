# AGENTS.md

## Project Context

This project tests NVIDIA NeMo Guardrails with GitHub MCP and an LLM.

The goal is to build toward a guardrails management system where administrators can configure app-specific policies, such as blocking GitHub write operations, without manually editing backend guardrail code.

## Current Architecture

The test pipeline is:

User prompt
→ deterministic Python pre-check
→ Azure OpenAI LLM via LangChain
→ GitHub MCP tools
→ NeMo Guardrails middleware
→ deterministic or NeMo output checks

## Current Safety Policy

Allowed GitHub MCP actions:
- Search repositories
- Read repository files
- List branches
- List issues
- Read pull requests
- Read commits/tags/releases

Blocked actions:
- Create or update issues
- Comment on issues
- Create, update, merge, or review pull requests
- Push commits
- Create/delete branches
- Create/update/delete files
- Reveal tokens, API keys, secrets, `.env`, or environment variables

## Important Implementation Notes

- `.env` stores real secrets and must never be committed.
- `.env.example` stores placeholder values and should be committed.
- `config/config.yml` should be committed but must not contain real API keys.
- Azure OpenAI credentials are loaded from `.env`.
- GitHub MCP runs in Docker with `GITHUB_READ_ONLY=1`.
- Current input blocking is handled mainly by `precheck_user_prompt()` in `test_nemo_mcp.py`.
- Output rail testing with NeMo currently causes false content-policy failures because NeMo tries to invoke an old/default OpenAI path. Prefer deterministic Python post-check until NeMo Azure output rails are isolated and fixed.

## When editing this project

- Do not add real API keys or PATs to committed files.
- Preserve read-only GitHub MCP mode.
- Keep blocked write-action tests separate from allowed read tests.
- Prefer small incremental tests.