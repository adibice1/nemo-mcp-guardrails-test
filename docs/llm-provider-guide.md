# LLM Provider Guide

This guide explains how an application developer selects an LLM for a GMS
application and how maintainers add support for a new provider.

## Runtime Model

Each GMS application can select two independent models:

- **Main Agent LLM:** interprets the user request, selects connector tools, and
  produces the response. Linked app developers can select this model.
- **Guardrail LLM:** runs NeMo input and output policy classifications. Only a
  GMS administrator should select this model.

```text
Client application
-> GMS input rails using the guardrail LLM
-> LangChain agent using the main-agent LLM
-> guarded connector tools
-> GMS output rails using the guardrail LLM
-> client application
```

The client application's GMS API key only authenticates calls to
`POST /v1/guardrails/run`. It does not configure or authenticate an LLM.
Model endpoints and credentials must be available to the GMS backend.

## Current Support

The runtime currently supports:

- Azure OpenAI using provider `azure` or `azure_openai`.
- A separate Azure deployment for the main agent and guardrail classifier.
- Backend credential references in the form `env:VARIABLE_NAME`.
- Environment-default Azure settings when an app has no selected configuration.

The runtime does not yet execute Ollama, Gemini, Anthropic, or generic
OpenAI-compatible configurations. `runtime_factory.py` deliberately rejects
these providers until their adapters and tests are implemented.

## Select Another Azure Deployment

### 1. Provision the credential

Add the deployment key to the GMS backend environment, not the frontend:

```env
APP_A_AZURE_KEY=replace-with-the-real-key
```

Restart the backend after changing its environment. For deployed containers,
configure the variable through the deployment platform rather than committing
it to `.env`.

### 2. Create the configuration

In the GMS:

```text
Applications
-> select the application
-> LLM Configuration
-> Add Configuration
```

Enter:

```text
Configuration Name: App A GPT-4o
Deployment Name: the Azure deployment name
Azure Endpoint: https://<resource>.openai.azure.com
Credential Environment Variable: APP_A_AZURE_KEY
```

The browser sends only `env:APP_A_AZURE_KEY`; it never sends or reads the key.

### 3. Assign it

Select the new configuration under **Main Agent LLM** and save. Administrators
may independently select it under **Guardrail LLM**.

Selecting **Environment default** uses `AZURE_OPENAI_DEPLOYMENT`,
`AZURE_OPENAI_ENDPOINT`, and `AZURE_OPENAI_API_KEY`.

### 4. Verify it

Run an app Runtime Test and confirm:

- Input, tool guard, and output stages complete.
- The selected model can perform required tool calls.
- Existing input and output policies still block expected test prompts.

## Add A Local Or Non-Azure Provider

Adding a provider is a backend feature, not only a configuration change.
The repository already installs `langchain-ollama` and
`langchain-google-genai`, but runtime construction is still Azure-only.

Implement the provider in these locations:

1. `runtime_factory.py`: import its LangChain chat adapter and add a provider
   branch to `build_chat_model()`.
2. Change the model return type from `AzureChatOpenAI` to LangChain's common
   chat-model interface.
3. Require Azure environment values only when an Azure model is selected.
4. `app_schemas.py`: add the provider to the accepted provider values and
   validate its required endpoint and credential reference.
5. `create-llm-config-modal.tsx`: add a provider selector and provider-specific
   field labels.
6. `api-client.ts`: extend the provider payload type.
7. `test_runtime_llm_selection.py`: test model construction, missing settings,
   disabled configurations, and unsupported providers.

Example Ollama metadata after the adapter is implemented:

```json
{
  "name": "Local Llama",
  "provider": "ollama",
  "model_name": "llama3.1:8b",
  "endpoint": "http://host.docker.internal:11434",
  "credential_reference": null,
  "enabled": true
}
```

Use `http://127.0.0.1:11434` when the backend runs directly on the same host.
From a Docker container, use a container-reachable hostname such as
`host.docker.internal`. In an Azure Container Instances group, a model sidecar
can be reached through `http://127.0.0.1:<port>`.

## Provider Requirements

Before enabling a model, confirm that:

- Main-agent models support the tool-calling behavior required by LangChain.
- Guardrail models reliably follow NeMo's classification prompts.
- Endpoints are private or explicitly allowlisted to reduce SSRF risk.
- API keys remain in backend environment variables or a production secrets
  manager and never enter the database or browser.
- Requests use timeouts and do not expose the local model port publicly.
- Input, output, and tool-guard tests pass before production assignment.

After changing a provider implementation, run:

```powershell
.\.venv\Scripts\python.exe tests\test_runtime_llm_selection.py
.\.venv\Scripts\python.exe tests\test_guardrails_run_http.py
```

Then restart the backend and perform one authenticated Runtime Test.
