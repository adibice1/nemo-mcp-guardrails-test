import os
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import AzureChatOpenAI
from nemoguardrails import LLMRails
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from nemo_mcp_guardrails.database.connection import SessionLocal
from nemo_mcp_guardrails.database.models import (
    AppConnectorRecord,
    AppRecord,
    ConnectorRecord,
    LlmConfigRecord,
)
from nemo_mcp_guardrails.database.policy_loader import load_input_policy_entries
from nemo_mcp_guardrails.prompt_rule_compiler import (
    PromptRuleConfig,
    build_rails_config_with_prompt_rules,
)
from nemo_mcp_guardrails.tool_guard import (
    blocked_tool_names_for_app,
    guard_mcp_tool,
)


SUPPORTED_AZURE_PROVIDERS = {"azure", "azure_openai"}


class ConnectorAccessError(RuntimeError):
    """Raised when an app is not allowed to use a connector."""


@dataclass(frozen=True)
class RuntimeEnvironment:
    """Store environment values needed for one guarded runtime request."""

    azure_api_key: str
    azure_endpoint: str
    azure_api_version: str
    azure_deployment: str
    github_pat: str
    github_mcp_read_only: str


@dataclass(frozen=True)
class RuntimeConnectorConfig:
    """Detached connector settings selected from the database."""

    name: str
    credential_reference: str | None


@dataclass(frozen=True)
class RuntimeLlmConfig:
    """Detached LLM config selected from the database."""

    name: str
    provider: str
    model_name: str
    endpoint: str | None
    enabled: bool


@dataclass(frozen=True)
class RuntimeLlmSelection:
    """Main-agent and guardrail LLM config choices for one app."""

    main_llm_config: RuntimeLlmConfig | None
    guardrail_llm_config: RuntimeLlmConfig | None


@dataclass(frozen=True)
class McpToolBundle:
    """Keep the MCP client alive with the tools it created."""

    client: Any
    tools: tuple[Any, ...]


@dataclass(frozen=True)
class GuardrailsRuntimeParts:
    """Store runtime objects prepared for one authenticated app request."""

    prompt_rule_config: PromptRuleConfig
    input_policy_count: int
    blocked_tools: frozenset[str]
    rails: LLMRails
    agent: Any
    output_rail_enabled: bool
    tool_bundle: McpToolBundle


def resolve_connector_credential(
    credential_reference: str | None,
    *,
    default_env_var: str,
) -> str:
    """Resolve one connector credential reference into a secret value."""

    reference = (credential_reference or "").strip()
    if not reference:
        env_var = default_env_var
    elif reference.startswith("env:"):
        env_var = reference.removeprefix("env:").strip()
        if not env_var:
            raise RuntimeError(
                "Connector credential reference env: is missing a variable name"
            )
    else:
        raise RuntimeError(
            "Unsupported connector credential reference: "
            f"{credential_reference}. Only env:VAR_NAME is wired in this prototype."
        )

    value = os.getenv(env_var)
    if not value:
        raise RuntimeError(f"Missing connector credential environment value: {env_var}")

    return value


def load_runtime_environment(
    github_credential_reference: str | None = None,
) -> RuntimeEnvironment:
    """Load required Azure OpenAI and GitHub MCP environment settings."""

    load_dotenv()

    values = {
        "AZURE_OPENAI_API_KEY": os.getenv("AZURE_OPENAI_API_KEY"),
        "AZURE_OPENAI_ENDPOINT": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "AZURE_OPENAI_API_VERSION": os.getenv("AZURE_OPENAI_API_VERSION"),
        "AZURE_OPENAI_DEPLOYMENT": os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    }
    missing = [name for name, value in values.items() if not value]

    if missing:
        raise RuntimeError("Missing runtime environment values: " + ", ".join(missing))

    azure_api_key = values["AZURE_OPENAI_API_KEY"] or ""
    github_pat = resolve_connector_credential(
        github_credential_reference,
        default_env_var="GITHUB_PERSONAL_ACCESS_TOKEN",
    )
    github_mcp_read_only = os.getenv("GITHUB_MCP_READ_ONLY", "1").strip()
    if github_mcp_read_only not in {"0", "1"}:
        raise RuntimeError("GITHUB_MCP_READ_ONLY must be 0 or 1")

    os.environ["OPENAI_API_KEY"] = azure_api_key
    os.environ["AZURE_OPENAI_API_KEY"] = azure_api_key

    return RuntimeEnvironment(
        azure_api_key=azure_api_key,
        azure_endpoint=values["AZURE_OPENAI_ENDPOINT"] or "",
        azure_api_version=values["AZURE_OPENAI_API_VERSION"] or "",
        azure_deployment=values["AZURE_OPENAI_DEPLOYMENT"] or "",
        github_pat=github_pat,
        github_mcp_read_only=github_mcp_read_only,
    )


def load_app_connector_config(
    app_id: int,
    connector_name: str,
) -> RuntimeConnectorConfig:
    """Return enabled connector config for one app or raise."""

    with SessionLocal() as db:
        connector_link = db.scalar(
            select(AppConnectorRecord)
            .join(
                ConnectorRecord,
                ConnectorRecord.id == AppConnectorRecord.connector_id,
            )
            .where(
                AppConnectorRecord.app_id == app_id,
                AppConnectorRecord.enabled.is_(True),
                ConnectorRecord.name == connector_name,
                ConnectorRecord.enabled.is_(True),
            )
        )

    if connector_link is None:
        raise ConnectorAccessError(
            f"App {app_id} is not linked to enabled connector: {connector_name}"
        )

    return RuntimeConnectorConfig(
        name=connector_name,
        credential_reference=connector_link.credential_reference,
    )


def require_app_connector_access(app_id: int, connector_name: str) -> None:
    """Raise when an app is not linked to an enabled connector."""

    load_app_connector_config(app_id, connector_name)


def _to_runtime_llm_config(
    config: LlmConfigRecord | None,
) -> RuntimeLlmConfig | None:
    """Copy an ORM LLM config into a detached runtime value."""

    if config is None:
        return None

    return RuntimeLlmConfig(
        name=config.name,
        provider=config.provider,
        model_name=config.model_name,
        endpoint=config.endpoint,
        enabled=config.enabled,
    )


def load_runtime_llm_selection(app_id: int) -> RuntimeLlmSelection:
    """Load detached LLM config choices for one app."""

    with SessionLocal() as db:
        app = db.scalar(
            select(AppRecord)
            .options(
                joinedload(AppRecord.main_llm_config),
                joinedload(AppRecord.guardrail_llm_config),
            )
            .where(AppRecord.id == app_id)
        )

        if app is None:
            raise RuntimeError(f"App not found: {app_id}")

        return RuntimeLlmSelection(
            main_llm_config=_to_runtime_llm_config(app.main_llm_config),
            guardrail_llm_config=_to_runtime_llm_config(app.guardrail_llm_config),
        )


def build_chat_model(
    environment: RuntimeEnvironment,
    config: RuntimeLlmConfig | None,
    purpose: str,
) -> AzureChatOpenAI:
    """Build the chat model for guardrails or main-agent execution."""

    if config is None:
        deployment = environment.azure_deployment
        endpoint = environment.azure_endpoint
    else:
        provider = config.provider.strip().lower()
        if provider not in SUPPORTED_AZURE_PROVIDERS:
            raise RuntimeError(
                f"Unsupported {purpose} LLM provider: {config.provider}. "
                "Only Azure OpenAI is wired in this prototype."
            )
        if not config.enabled:
            raise RuntimeError(f"{purpose} LLM config is disabled: {config.name}")

        deployment = config.model_name or environment.azure_deployment
        endpoint = config.endpoint or environment.azure_endpoint

    return AzureChatOpenAI(
        azure_deployment=deployment,
        azure_endpoint=endpoint,
        api_key=environment.azure_api_key,
        api_version=environment.azure_api_version,
        temperature=0,
    )


async def build_guarded_github_tools(
    environment: RuntimeEnvironment,
    blocked_tool_names: frozenset[str],
) -> McpToolBundle:
    """Build GitHub MCP tools wrapped with the tool guard."""

    github_read_only = environment.github_mcp_read_only

    client = MultiServerMCPClient(
        {
            "github": {
                "command": "docker",
                "args": [
                    "run",
                    "-i",
                    "--rm",
                    "-e",
                    "GITHUB_PERSONAL_ACCESS_TOKEN",
                    "-e",
                    f"GITHUB_READ_ONLY={github_read_only}",
                    "-e",
                    "GITHUB_TOOLSETS=repos,issues,pull_requests",
                    "ghcr.io/github/github-mcp-server",
                ],
                "transport": "stdio",
                "env": {
                    "GITHUB_PERSONAL_ACCESS_TOKEN": environment.github_pat,
                    "GITHUB_READ_ONLY": github_read_only,
                    "GITHUB_TOOLSETS": "repos,issues,pull_requests",
                },
            }
        }
    )
    raw_tools = await client.get_tools()
    guarded_tools = tuple(
        guard_mcp_tool(tool, blocked_tool_names=blocked_tool_names)
        for tool in raw_tools
    )

    return McpToolBundle(client=client, tools=guarded_tools)


async def build_guardrails_runtime_parts(app_id: int) -> GuardrailsRuntimeParts:
    """Build rails, agent, and guarded tools for one authenticated app."""

    github_connector = load_app_connector_config(app_id, "github")
    environment = load_runtime_environment(
        github_credential_reference=github_connector.credential_reference,
    )
    llm_selection = load_runtime_llm_selection(app_id)
    guardrail_model = build_chat_model(
        environment,
        llm_selection.guardrail_llm_config,
        "guardrail",
    )
    main_model = build_chat_model(
        environment,
        llm_selection.main_llm_config,
        "main agent",
    )
    prompt_rule_config = build_rails_config_with_prompt_rules(
        "config",
        app_id=app_id,
    )
    rails = LLMRails(prompt_rule_config.rails_config, llm=guardrail_model)
    blocked_tools = blocked_tool_names_for_app(app_id=app_id)
    tool_bundle = await build_guarded_github_tools(
        environment,
        blocked_tools,
    )
    agent = create_agent(model=main_model, tools=list(tool_bundle.tools))

    return GuardrailsRuntimeParts(
        prompt_rule_config=prompt_rule_config,
        input_policy_count=len(load_input_policy_entries(app_id=app_id)),
        blocked_tools=blocked_tools,
        rails=rails,
        agent=agent,
        output_rail_enabled=bool(prompt_rule_config.rails_config.rails.output.flows),
        tool_bundle=tool_bundle,
    )
