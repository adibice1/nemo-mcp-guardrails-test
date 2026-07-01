import re
from dataclasses import dataclass
from typing import Any

from langchain_core.tools import StructuredTool

from nemo_mcp_guardrails.database.policy_loader import load_input_policy_objects
from nemo_mcp_guardrails.policy_compiler import compile_policy

STATIC_BLOCKED_GITHUB_MCP_TOOLS: frozenset[str] = frozenset()

TOOL_GUARD_REFUSAL = (
    "I can inspect GitHub information, but I cannot perform write actions "
    "or reveal credentials."
)


@dataclass(frozen=True)
class ToolGuardRule:
    """Describe one unconditional or resource-specific tool restriction."""

    tool_names: frozenset[str]
    custom_resource: str | None = None


def _normalize_match_text(value: Any) -> str:
    """Normalize a resource value for case-insensitive argument matching."""

    text = str(value).casefold().strip()
    text = re.sub(r"[^a-z0-9._/\-]+", " ", text)
    return re.sub(r"\s+", " ", text).strip(" ._/-")


def _custom_resource_candidates(custom_resource: str) -> frozenset[str]:
    """Extract literal target candidates from an admin-entered restriction."""

    candidates = {_normalize_match_text(custom_resource)}
    candidates.update(
        _normalize_match_text(match)
        for match in re.findall(r'["\']([^"\']+)["\']', custom_resource)
    )

    qualified_match = re.search(
        r"\b(?:named|called|titled|numbered|number|path|branch)\s+(?:is\s+)?(.+)$",
        custom_resource,
        flags=re.IGNORECASE,
    )
    if qualified_match:
        candidates.add(_normalize_match_text(qualified_match.group(1)))

    number_match = re.search(r"#\s*(\d+)", custom_resource)
    if number_match:
        candidates.add(number_match.group(1))

    return frozenset(candidate for candidate in candidates if candidate)


def _flatten_argument_values(value: Any) -> tuple[str, ...]:
    """Flatten nested MCP arguments into normalized scalar values."""

    if isinstance(value, dict):
        return tuple(
            item
            for nested_value in value.values()
            for item in _flatten_argument_values(nested_value)
        )
    if isinstance(value, (list, tuple, set)):
        return tuple(
            item
            for nested_value in value
            for item in _flatten_argument_values(nested_value)
        )
    if value is None or isinstance(value, bool):
        return ()

    normalized = _normalize_match_text(value)
    return (normalized,) if normalized else ()


def custom_resource_matches(
    custom_resource: str,
    tool_arguments: dict[str, Any],
) -> bool:
    """Return whether MCP arguments refer to the restricted custom resource."""

    candidates = _custom_resource_candidates(custom_resource)
    argument_values = _flatten_argument_values(tool_arguments)
    return any(
        candidate == value
        for candidate in candidates
        for value in argument_values
    )


def tool_guard_rules_for_app(
    app_id: int | None = None,
) -> tuple[ToolGuardRule, ...]:
    """Compile executable MCP guard rules for the optional app scope."""

    rules: list[ToolGuardRule] = []
    if STATIC_BLOCKED_GITHUB_MCP_TOOLS:
        rules.append(ToolGuardRule(STATIC_BLOCKED_GITHUB_MCP_TOOLS))

    for policy in load_input_policy_objects(app_id=app_id):
        compiled_policy = compile_policy(policy)
        rules.append(
            ToolGuardRule(
                tool_names=frozenset(compiled_policy.blocked_tools),
                custom_resource=(policy.custom_resource or "").strip() or None,
            )
        )

    return tuple(rules)


def blocked_tool_names_for_app(
    app_id: int | None = None,
) -> frozenset[str]:
    """Return tool names covered by broad or conditional app guard rules."""

    return frozenset(
        tool_name
        for rule in tool_guard_rules_for_app(app_id=app_id)
        for tool_name in rule.tool_names
    )


BLOCKED_GITHUB_MCP_TOOLS = blocked_tool_names_for_app()


def guard_mcp_tool(
    tool: Any,
    blocked_tool_names: frozenset[str] = BLOCKED_GITHUB_MCP_TOOLS,
    guard_rules: tuple[ToolGuardRule, ...] | None = None,
) -> Any:
    """Wrap an MCP tool so matching broad or conditional rules block execution."""

    effective_rules = guard_rules
    if effective_rules is None:
        effective_rules = (ToolGuardRule(blocked_tool_names),)

    async def guarded_coroutine(**kwargs: Any) -> Any:
        """Block restricted tools and forward allowed calls to the real MCP tool."""

        for rule in effective_rules:
            if tool.name not in rule.tool_names:
                continue
            if rule.custom_resource is None or custom_resource_matches(
                rule.custom_resource,
                kwargs,
            ):
                return f"Tool call blocked by guard: {TOOL_GUARD_REFUSAL}"

        return await tool.ainvoke(kwargs)

    return StructuredTool.from_function(
        coroutine=guarded_coroutine,
        name=tool.name,
        description=getattr(tool, "description", ""),
        args_schema=getattr(tool, "args_schema", None),
    )
