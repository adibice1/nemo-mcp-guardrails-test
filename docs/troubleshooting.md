# Troubleshooting Notes

## GitHub Push Protection

If GitHub blocks push with `GH013` and says an Azure OpenAI key was found, remove the secret from commits.

Recommended:
1. Rotate the exposed Azure key.
2. Run `git reset --soft origin/main`.
3. Remove real keys from committed files.
4. Store real keys only in `.env`.
5. Commit `.env.example` instead.

## Azure OpenAI Key Handling

Use `.env`:

AZURE_OPENAI_API_KEY=...
OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_VERSION=...
AZURE_OPENAI_DEPLOYMENT=...
GITHUB_PERSONAL_ACCESS_TOKEN=...

`OPENAI_API_KEY` is included because some NeMo/LangChain internals still expect it.

## GitHub MCP Connection Closed

If MCP says `Connection closed`, check:
- Docker is running
- `GITHUB_PERSONAL_ACCESS_TOKEN` exists in `.env`
- The PAT starts with `github_pat_` or `ghp_`
- The PAT is valid

## NeMo Output Rail False Blocking

If allowed read requests return:

"I cannot provide this response due to content policy."

Check logs for:

`Error invoking LLM (model=gpt-3.5-turbo, endpoint=APIRemovedInV1Proxy)`

This means NeMo output rail LLM invocation is failing, not that the content is actually unsafe.