import asyncio
import os
from collections import OrderedDict
from dataclasses import dataclass, field
from time import monotonic
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from nemoguardrails import LLMRails
from openai import DefaultAsyncHttpxClient, DefaultHttpxClient
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from nemo_mcp_guardrails.connector_credentials import resolve_github_credential
from nemo_mcp_guardrails.classifier_model import StrictClassifierModel
from nemo_mcp_guardrails.database.connection import SessionLocal
from nemo_mcp_guardrails.database.policy_errors import PolicyLoadError
from nemo_mcp_guardrails.database.models import (
    AppConnectorRecord,
    AppPolicyAssignmentRecord,
    AppRecord,
    CompiledPolicyRuleRecord,
    ConnectorActionRecord,
    ConnectorRecord,
    ConnectorResourceRecord,
    ConnectorToolMappingRecord,
    GlobalPolicyAssignmentRecord,
    LlmConfigRecord,
    PolicyRecord,
)
from nemo_mcp_guardrails.database.policy_loader import (
    LoadedInputPolicy,
    default_policy_source_requested,
)
from nemo_mcp_guardrails.database.runtime_policy_snapshot import RuntimePolicySnapshot, read_runtime_policy_snapshot
from nemo_mcp_guardrails.database.prompt_rule_loader import LoadedPromptRule
from nemo_mcp_guardrails.policy_compiler import InputPolicyObject, OutputPolicyObject
from nemo_mcp_guardrails.llm_access import LlmAccessError, require_llm_grant
from nemo_mcp_guardrails.llm_credentials import (
    LlmCredentialError, resolve_llm_credential, validate_llm_credential_reference,
)
from nemo_mcp_guardrails.llm_security import validate_llm_endpoint
from nemo_mcp_guardrails.llm_profiles import COMPATIBLE_PROVIDER, validate_profile_metadata
from nemo_mcp_guardrails.model_credentials import (
    credential_key_version, decrypt_model_key, validate_owned_profile,
)
from nemo_mcp_guardrails.github_tool_contract import (
    REVIEWED_MCP_IMAGE, REVIEWED_NATIVE_BINARY, select_reviewed_github_tools,
)
from nemo_mcp_guardrails.output_guard import compile_blocked_output_phrases
from nemo_mcp_guardrails.prompt_rule_compiler import (
    PromptRuleConfig,
    build_rails_config_with_prompt_rules,
)
from nemo_mcp_guardrails.tool_guard import (
    ToolGuardRule,
    guard_mcp_tool,
    compile_tool_guard_rules,
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
    credential_reference: str | None
    enabled: bool
    owner_app_id: int | None = None
    encrypted_api_key: str | None = field(default=None, repr=False)
    credential_key_version: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class RuntimeLlmSelection:
    """Main-agent and guardrail LLM config choices for one app."""

    main_llm_config: RuntimeLlmConfig | None
    guardrail_llm_config: RuntimeLlmConfig | None
    grant_ids: tuple[int, int]


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
    input_policy_entries: tuple[LoadedInputPolicy, ...]
    blocked_tools: frozenset[str]
    rails: LLMRails
    agent: Any
    output_rail_enabled: bool
    blocked_output_phrases: tuple[str, ...]
    tool_bundle: McpToolBundle


RuntimeRevision = tuple[Any, ...]


@dataclass(frozen=True)
class RuntimeCacheEntry:
    """Store one reusable app runtime and its database revision."""

    revision: RuntimeRevision
    expires_at: float
    parts: GuardrailsRuntimeParts


_RUNTIME_PARTS_CACHE: OrderedDict[int, RuntimeCacheEntry] = OrderedDict()
_RUNTIME_BUILD_LOCKS: dict[int, asyncio.Lock] = {}


def _runtime_cache_ttl_seconds() -> float:
    """Return the configured non-negative runtime cache lifetime."""

    try:
        value = float(os.getenv("NEMO_RUNTIME_CACHE_TTL_SECONDS", "300"))
    except ValueError as error:
        raise RuntimeError(
            "NEMO_RUNTIME_CACHE_TTL_SECONDS must be a number"
        ) from error
    if value < 0:
        raise RuntimeError("NEMO_RUNTIME_CACHE_TTL_SECONDS cannot be negative")
    return value


def _runtime_cache_max_apps() -> int:
    """Return the maximum number of app runtimes retained in memory."""

    try:
        value = int(os.getenv("NEMO_RUNTIME_CACHE_MAX_APPS", "32"))
    except ValueError as error:
        raise RuntimeError(
            "NEMO_RUNTIME_CACHE_MAX_APPS must be an integer"
        ) from error
    if value < 1:
        raise RuntimeError("NEMO_RUNTIME_CACHE_MAX_APPS must be at least 1")
    return value


def _revision_pair(model: Any, *conditions: Any) -> tuple[Any, Any]:
    """Return count and latest-update subqueries for one runtime table."""

    return (
        select(func.count(model.id)).where(*conditions).scalar_subquery(),
        select(func.max(model.updated_at)).where(*conditions).scalar_subquery(),
    )


def load_runtime_revision(app_id: int) -> RuntimeRevision:
    """Return one query fingerprint covering runtime-relevant state."""

    columns = [
        select(AppRecord.updated_at)
        .where(AppRecord.id == app_id)
        .scalar_subquery(),
        *_revision_pair(
            AppConnectorRecord,
            AppConnectorRecord.app_id == app_id,
        ),
        *_revision_pair(
            AppPolicyAssignmentRecord,
            AppPolicyAssignmentRecord.app_id == app_id,
        ),
        *_revision_pair(GlobalPolicyAssignmentRecord),
        *_revision_pair(PolicyRecord),
        *_revision_pair(CompiledPolicyRuleRecord),
        *_revision_pair(ConnectorRecord),
        *_revision_pair(ConnectorActionRecord),
        *_revision_pair(ConnectorResourceRecord),
        *_revision_pair(ConnectorToolMappingRecord),
        *_revision_pair(LlmConfigRecord),
    ]
    with SessionLocal() as db:
        return tuple(db.execute(select(*columns)).one())


def clear_guardrails_runtime_cache() -> None:
    """Clear reusable runtime objects, primarily for tests."""

    _RUNTIME_PARTS_CACHE.clear()
    _RUNTIME_BUILD_LOCKS.clear()


def load_runtime_environment(
    github_credential_reference: str | None = None,
    *, llm_selection: RuntimeLlmSelection | None = None,
) -> RuntimeEnvironment:
    """Load connector settings and optional Azure defaults; validate models when selected."""

    load_dotenv()
    validate_llm_credential_reference(None)

    values = {
        "AZURE_OPENAI_API_KEY": os.getenv("AZURE_OPENAI_API_KEY"),
        "AZURE_OPENAI_ENDPOINT": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "AZURE_OPENAI_API_VERSION": os.getenv("AZURE_OPENAI_API_VERSION"),
        "AZURE_OPENAI_DEPLOYMENT": os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    }
    selected = (llm_selection.main_llm_config, llm_selection.guardrail_llm_config) if llm_selection else (None,)
    legacy_azure = any(config is None or (
        config.provider.strip().lower() in SUPPORTED_AZURE_PROVIDERS
        and getattr(config, "owner_app_id", None) is None
    ) for config in selected)
    if legacy_azure and any(not value for value in values.values()):
        raise LlmCredentialError("Runtime Azure environment is unavailable.")
    if any(config is not None and config.provider.strip().lower() in SUPPORTED_AZURE_PROVIDERS
           for config in selected) and not values["AZURE_OPENAI_API_VERSION"]:
        raise LlmCredentialError("Runtime Azure environment is unavailable.")

    azure_api_key = values["AZURE_OPENAI_API_KEY"] or ""
    github_pat = resolve_github_credential(github_credential_reference)
    github_mcp_read_only = os.getenv("GITHUB_MCP_READ_ONLY", "1").strip()
    if github_mcp_read_only not in {"0", "1"}:
        raise RuntimeError("GITHUB_MCP_READ_ONLY must be 0 or 1")

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
        credential_reference=config.credential_reference,
        enabled=config.enabled,
        owner_app_id=getattr(config, "owner_app_id", None),
        encrypted_api_key=getattr(config, "encrypted_api_key", None),
        credential_key_version=(credential_key_version()
                                if getattr(config, "owner_app_id", None) is not None else None),
    )


def load_runtime_llm_selection(app_id: int) -> RuntimeLlmSelection:
    """Require live grants for both purposes and detach their exact model state."""

    try:
        with SessionLocal() as db:
            app = db.get(AppRecord, app_id)
            if app is None or not app.authorized:
                raise LlmAccessError("Runtime model selection is unavailable.")
            main_grant, main = require_llm_grant(db, app_id, "main", app.main_llm_config_id)
            guardrail_grant, guardrail = require_llm_grant(
                db, app_id, "guardrail", app.guardrail_llm_config_id,
            )
            return RuntimeLlmSelection(
                main_llm_config=_to_runtime_llm_config(main),
                guardrail_llm_config=_to_runtime_llm_config(guardrail),
                grant_ids=(main_grant.id, guardrail_grant.id),
            )
    except (SQLAlchemyError, ValueError, TypeError, AttributeError) as error:
        raise LlmAccessError("Runtime model selection is unavailable.") from error


def _check_llm_selection(app_id: int, expected: RuntimeLlmSelection) -> None:
    """Reject a build if its selected grants or model metadata changed."""

    if load_runtime_llm_selection(app_id) != expected:
        raise LlmAccessError("Runtime model selection changed during construction.")


def build_chat_model(
    environment: RuntimeEnvironment,
    config: RuntimeLlmConfig | None,
    purpose: str,
) -> BaseChatModel:
    """Build the chat model for guardrails or main-agent execution."""

    owned = config is not None and config.owner_app_id is not None
    if owned and purpose not in {"main", "main agent"}:
        raise LlmAccessError("App-owned profiles cannot classify guardrails.")
    if config is not None and config.provider.strip().lower() == COMPATIBLE_PROVIDER:
        if not config.enabled or not config.model_name.strip():
            raise RuntimeError("Compatible LLM configuration is unavailable.")
        if owned:
            endpoint = validate_owned_profile(config)
            api_key = decrypt_model_key(config)
        else:
            endpoint, reference = validate_profile_metadata(
                config.provider, config.endpoint, config.credential_reference,
            )
            api_key = resolve_llm_credential(reference)
        model = ChatOpenAI(
            model=config.model_name, base_url=endpoint, api_key=api_key,
            http_client=DefaultHttpxClient(follow_redirects=False),
            http_async_client=DefaultAsyncHttpxClient(follow_redirects=False),
            timeout=60, max_retries=0, use_responses_api=False,
            # Provider-specific generation options belong to reviewed gateway profiles.
        )
        return StrictClassifierModel(wrapped=model) if purpose == "guardrail" else model

    if config is None:
        deployment = environment.azure_deployment
        endpoint = environment.azure_endpoint
    else:
        provider = config.provider.strip().lower()
        if provider not in SUPPORTED_AZURE_PROVIDERS:
            raise RuntimeError(
                f"Unsupported {purpose} LLM provider: {config.provider}. "
                "Use azure_openai or an approved openai_compatible gateway."
            )
        if not config.enabled:
            raise RuntimeError(f"{purpose} LLM config is disabled: {config.name}")

        deployment = config.model_name or environment.azure_deployment
        endpoint = config.endpoint or environment.azure_endpoint
    endpoint = validate_llm_endpoint(endpoint, default_endpoint=environment.azure_endpoint)
    reference = validate_llm_credential_reference(config.credential_reference if config else None)
    api_key = (decrypt_model_key(config) if owned else
               resolve_llm_credential(reference) if reference else environment.azure_api_key)
    if not api_key or not environment.azure_api_version or not deployment:
        raise LlmCredentialError("Azure LLM configuration is unavailable.")

    return AzureChatOpenAI(
        azure_deployment=deployment,
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version=environment.azure_api_version,
        http_client=DefaultHttpxClient(follow_redirects=False),
        http_async_client=DefaultAsyncHttpxClient(follow_redirects=False),
        temperature=0,
    )


async def build_guarded_github_tools(
    environment: RuntimeEnvironment,
    blocked_tool_names: frozenset[str],
    guard_rules: tuple[ToolGuardRule, ...],
) -> McpToolBundle:
    """Build GitHub MCP tools wrapped with the tool guard."""

    client = MultiServerMCPClient(
        {"github": github_mcp_client_config(environment)}
    )
    raw_tools = await client.get_tools()
    try:
        raw_tools = select_reviewed_github_tools(raw_tools)
    except (ValueError, TypeError, AttributeError):
        raise PolicyLoadError("GitHub MCP tool contract is unavailable.") from None
    from nemo_mcp_guardrails.github_pr_state import pr_branch_reader
    branch_reader = pr_branch_reader(raw_tools)
    guarded_tools = tuple(
        guard_mcp_tool(
            tool,
            blocked_tool_names=blocked_tool_names,
            guard_rules=guard_rules,
            branch_reader=branch_reader,
        )
        for tool in raw_tools
    )

    return McpToolBundle(client=client, tools=guarded_tools)


def github_mcp_client_config(environment: RuntimeEnvironment) -> dict[str, Any]:
    """Build the local-Docker or native-container GitHub MCP configuration."""

    github_read_only = environment.github_mcp_read_only
    shared_config: dict[str, Any] = {
        "transport": "stdio",
        "env": {
            "GITHUB_PERSONAL_ACCESS_TOKEN": environment.github_pat,
            "GITHUB_READ_ONLY": github_read_only,
            "GITHUB_TOOLSETS": "repos,issues,pull_requests",
        },
    }
    launch_mode = os.getenv("GITHUB_MCP_LAUNCH_MODE", "docker").strip().lower()

    if launch_mode == "native":
        binary_path = os.getenv("GITHUB_MCP_BINARY_PATH", REVIEWED_NATIVE_BINARY)
        if binary_path != REVIEWED_NATIVE_BINARY:
            raise RuntimeError("Native GitHub MCP requires the bundled reviewed executable.")
        return {
            **shared_config,
            "command": binary_path,
            "args": ["stdio"],
        }

    if launch_mode == "docker":
        return {
            **shared_config,
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
                REVIEWED_MCP_IMAGE,
            ],
        }

    raise RuntimeError(
        "GITHUB_MCP_LAUNCH_MODE must be either 'native' or 'docker'"
    )


def load_runtime_policy_snapshot(app_id: int) -> RuntimePolicySnapshot:
    """Use a fresh database statement for exact app/global enforcement state."""

    if default_policy_source_requested():
        raise PolicyLoadError("Authenticated runtimes require database policies.")
    try:
        with SessionLocal() as db:
            return read_runtime_policy_snapshot(db, app_id)
    except SQLAlchemyError:
        raise PolicyLoadError("Runtime policy snapshot is unavailable.") from None


def _check_policy_snapshot(app_id: int, expected: RuntimePolicySnapshot) -> None:
    """Reject construction if selected policy or compiler contents changed."""

    if load_runtime_policy_snapshot(app_id) != expected:
        raise PolicyLoadError("Runtime policy configuration changed during construction.")


async def _build_guardrails_runtime_parts_uncached(
    app_id: int,
    llm_selection: RuntimeLlmSelection | None = None,
    policy_snapshot: RuntimePolicySnapshot | None = None,
) -> GuardrailsRuntimeParts:
    """Build uncached rails, agent, and guarded tools for one app."""

    github_connector = load_app_connector_config(app_id, "github")
    try:
        if policy_snapshot is None:
            policy_snapshot = load_runtime_policy_snapshot(app_id)
        if policy_snapshot.app_id != app_id:
            raise PolicyLoadError("Runtime policy scope is invalid.")
        input_policy_entries = tuple(
            LoadedInputPolicy("database", entry.policy_id, entry.policy)
            for entry in policy_snapshot.policies if isinstance(entry.policy, InputPolicyObject)
        )
        prompt_rules = tuple(
            LoadedPromptRule("database", entry.compiled_rule_id, entry.policy_id,
                             "input" if isinstance(entry.policy, InputPolicyObject) else "output", entry.rule_text)
            for entry in policy_snapshot.policies
        )
        prompt_rule_config = build_rails_config_with_prompt_rules(
            "config", app_id=app_id, prompt_rules=prompt_rules,
        )
        guard_rules = compile_tool_guard_rules(input_policy_entries)
        blocked_tools = frozenset(name for rule in guard_rules for name in rule.tool_names)
        blocked_output_phrases = compile_blocked_output_phrases(
            entry.policy.description for entry in policy_snapshot.policies
            if isinstance(entry.policy, OutputPolicyObject)
        )
    except (ValueError, TypeError, AttributeError) as error:
        raise PolicyLoadError("Runtime policy configuration is invalid.") from error

    if llm_selection is None:
        llm_selection = load_runtime_llm_selection(app_id)
    environment = load_runtime_environment(
        github_credential_reference=github_connector.credential_reference,
        llm_selection=llm_selection,
    )
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
    rails = LLMRails(prompt_rule_config.rails_config, llm=guardrail_model)
    tool_bundle = await build_guarded_github_tools(
        environment,
        blocked_tools,
        guard_rules,
    )
    agent = create_agent(model=main_model, tools=list(tool_bundle.tools))
    return GuardrailsRuntimeParts(
        prompt_rule_config=prompt_rule_config,
        input_policy_count=len(input_policy_entries),
        input_policy_entries=input_policy_entries,
        blocked_tools=blocked_tools,
        rails=rails,
        agent=agent,
        output_rail_enabled=bool(prompt_rule_config.rails_config.rails.output.flows),
        blocked_output_phrases=blocked_output_phrases,
        tool_bundle=tool_bundle,
    )


async def build_guardrails_runtime_parts(app_id: int) -> GuardrailsRuntimeParts:
    """Reuse an app runtime until its database revision or TTL changes."""

    if default_policy_source_requested():
        raise PolicyLoadError("Authenticated runtimes require database policies.")

    selection = load_runtime_llm_selection(app_id)
    snapshot = load_runtime_policy_snapshot(app_id)
    ttl = _runtime_cache_ttl_seconds()
    if ttl == 0:
        parts = await _build_guardrails_runtime_parts_uncached(app_id, selection, snapshot)
        _check_llm_selection(app_id, selection)
        _check_policy_snapshot(app_id, snapshot)
        return parts

    revision = (selection, snapshot, *load_runtime_revision(app_id))
    now = monotonic()
    cached = _RUNTIME_PARTS_CACHE.get(app_id)
    if cached and cached.revision == revision and cached.expires_at > now:
        _RUNTIME_PARTS_CACHE.move_to_end(app_id)
        return cached.parts

    lock = _RUNTIME_BUILD_LOCKS.setdefault(app_id, asyncio.Lock())
    async with lock:
        selection = load_runtime_llm_selection(app_id)
        snapshot = load_runtime_policy_snapshot(app_id)
        revision = (selection, snapshot, *load_runtime_revision(app_id))
        now = monotonic()
        cached = _RUNTIME_PARTS_CACHE.get(app_id)
        if cached and cached.revision == revision and cached.expires_at > now:
            _RUNTIME_PARTS_CACHE.move_to_end(app_id)
            return cached.parts

        parts = await _build_guardrails_runtime_parts_uncached(app_id, selection, snapshot)
        _check_llm_selection(app_id, selection)
        _check_policy_snapshot(app_id, snapshot)
        _RUNTIME_PARTS_CACHE[app_id] = RuntimeCacheEntry(
            revision=revision,
            expires_at=now + ttl,
            parts=parts,
        )
        _RUNTIME_PARTS_CACHE.move_to_end(app_id)
        while len(_RUNTIME_PARTS_CACHE) > _runtime_cache_max_apps():
            _RUNTIME_PARTS_CACHE.popitem(last=False)
        return parts
