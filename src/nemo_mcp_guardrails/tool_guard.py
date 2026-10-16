from dataclasses import dataclass, field
from time import perf_counter
from typing import Any

from langchain_core.tools import StructuredTool, ToolException

from nemo_mcp_guardrails.database.policy_loader import LoadedInputPolicy, load_input_policy_entries
from nemo_mcp_guardrails.github_resource_bindings import GithubBranchBinding, InvalidResourceArguments
from nemo_mcp_guardrails.github_tool_contract import GithubExecutionRule, compile_github_execution_rule
from nemo_mcp_guardrails.policy_compiler import (
    DEFAULT_INPUT_POLICY_OBJECTS,
    compile_blocked_tools,
)
from nemo_mcp_guardrails.runtime_events import record_runtime_event

STATIC_BLOCKED_GITHUB_MCP_TOOLS: frozenset[str] = frozenset()

TOOL_GUARD_REFUSAL = (
    "I can inspect GitHub information, but I cannot perform write actions "
    "or reveal credentials."
)


class ToolGuardViolation(ToolException):
    """Raised before an MCP tool executes when a GMS policy matches."""

    def __init__(self, tool_name: str, rule: "ToolGuardRule | None" = None) -> None:
        """Attach only metadata from the rule that actually matched this call."""

        self.tool_name = tool_name
        self.policy_id = rule.policy_id if rule else None
        self.policy_name = rule.policy_name if rule else None
        super().__init__(TOOL_GUARD_REFUSAL)


TOOL_GUARD_EVALUATION_RESPONSE = "The connector request could not be checked against its resource policy."


class ToolGuardEvaluationError(ToolException):
    """Stop an unobservable or malformed call without asserting a policy match."""

    def __init__(self, tool_name: str) -> None:
        """Retain only the reviewed tool name and a generic explanation."""

        self.tool_name = tool_name
        super().__init__(TOOL_GUARD_EVALUATION_RESPONSE)


@dataclass(frozen=True)
class ToolGuardRule:
    """Describe one unconditional or resource-specific tool restriction."""

    tool_names: frozenset[str]
    custom_resource: str | None = field(default=None, repr=False)
    execution: GithubExecutionRule | None = field(default=None, repr=False)
    policy_id: int | None = None
    policy_name: str | None = None

    def __post_init__(self) -> None:
        """Refuse legacy conditional wrappers and inconsistent reporting sets."""

        if self.custom_resource and self.execution is None:
            raise ValueError("Conditional guards require an executable field binding.")
        if self.execution is not None and self.tool_names != self.execution.tool_names:
            raise ValueError("Tool guard reporting names do not match its executable rule.")


def compile_tool_guard_rules(entries: tuple[LoadedInputPolicy, ...]) -> tuple[ToolGuardRule, ...]:
    """Compile supplied immutable policies without another database read."""

    rules = [ToolGuardRule(STATIC_BLOCKED_GITHUB_MCP_TOOLS)] if STATIC_BLOCKED_GITHUB_MCP_TOOLS else []
    for entry in entries:
        policy = entry.policy
        execution = compile_github_execution_rule(policy)
        rules.append(ToolGuardRule(
            execution.tool_names, policy.custom_resource, execution, entry.source_id,
            f"GitHub {policy.action} {policy.resource.replace('_', ' ')}",
        ))
    return tuple(rules)


def tool_guard_rules_for_app(app_id: int | None = None) -> tuple[ToolGuardRule, ...]:
    """Compile validated enabled policies for a diagnostic's optional app scope."""

    return compile_tool_guard_rules(load_input_policy_entries(app_id=app_id))


def blocked_tool_names_for_app(
    app_id: int | None = None,
) -> frozenset[str]:
    """Return tool names covered by broad or conditional app guard rules."""

    return frozenset(
        tool_name
        for rule in tool_guard_rules_for_app(app_id=app_id)
        for tool_name in rule.tool_names
    )


# Compatibility summary for offline diagnostics; importing never reads the database.
BLOCKED_GITHUB_MCP_TOOLS = compile_blocked_tools(DEFAULT_INPUT_POLICY_OBJECTS)


def guard_mcp_tool(
    tool: Any,
    blocked_tool_names: frozenset[str] | None = None,
    guard_rules: tuple[ToolGuardRule, ...] | None = None,
    branch_reader: Any = None,
) -> Any:
    """Wrap an MCP tool so matching broad or conditional rules block execution."""

    effective_rules = guard_rules
    if effective_rules is None:
        effective_rules = (
            tool_guard_rules_for_app()
            if blocked_tool_names is None
            else (ToolGuardRule(blocked_tool_names),)
        )

    async def guarded_coroutine(**kwargs: Any) -> Any:
        """Record guard decisions and invocation metadata without arguments."""
        guard_started = perf_counter()
        record_runtime_event(
            "tool_guard.started", "tool_guard", "started",
            tool_name=tool.name,
        )
        try:
            branch_state = None
            merge_branch_rules = tool.name == "merge_pull_request" and any(
                rule.execution is not None and any(
                    isinstance(binding, GithubBranchBinding) and binding.tool_name == tool.name
                    for binding in rule.execution.bindings
                ) for rule in effective_rules
            )
            # Broad bans need no metadata. Keep their attribution and event path.
            ordered_rules = sorted(effective_rules, key=lambda rule: bool(rule.execution and rule.execution.bindings)) if merge_branch_rules else effective_rules
            broad_match = merge_branch_rules and any(
                tool.name in rule.tool_names and (rule.execution is None or not rule.execution.bindings)
                and (rule.execution is None or rule.execution.matches(tool.name, kwargs))
                for rule in ordered_rules
            )
            if merge_branch_rules and not broad_match:
                if branch_reader is None:
                    raise InvalidResourceArguments("No trusted PR reader is available.")
                branch_state = await branch_reader(kwargs)
            for rule in ordered_rules:
                if tool.name not in rule.tool_names:
                    continue
                if rule.execution is None or rule.execution.matches(tool.name, kwargs, branch_state=branch_state):
                    record_runtime_event(
                        "tool_guard.completed", "tool_guard", "blocked",
                        duration_ms=(perf_counter() - guard_started) * 1000,
                        tool_name=tool.name, reason_code="gms_tool_guard",
                    )
                    raise ToolGuardViolation(tool.name, rule)
            if merge_branch_rules:
                # GitHub's merge precondition pins the head SHA, not the base ref.
                # A second read or local lock cannot close a remote retarget race.
                raise InvalidResourceArguments("Atomic branch-conditional merging is unavailable.")
        except InvalidResourceArguments:
            record_runtime_event(
                "tool_guard.completed", "tool_guard", "error",
                duration_ms=(perf_counter() - guard_started) * 1000,
                tool_name=tool.name, reason_code="gms_tool_guard_evaluation",
            )
            raise ToolGuardEvaluationError(tool.name) from None
        except ToolGuardViolation:
            raise
        except BaseException:
            record_runtime_event(
                "tool_guard.raised", "tool_guard", "raised",
                duration_ms=(perf_counter() - guard_started) * 1000,
                tool_name=tool.name,
            )
            raise

        record_runtime_event(
            "tool_guard.completed", "tool_guard", "passed",
            duration_ms=(perf_counter() - guard_started) * 1000,
            tool_name=tool.name, reason_code="gms_tool_guard",
        )
        tool_started = perf_counter()
        record_runtime_event(
            "tool.started", "tool", "started", tool_name=tool.name,
        )
        try:
            result = await tool.ainvoke(kwargs)
        except BaseException:
            record_runtime_event(
                "tool.raised", "tool", "raised",
                duration_ms=(perf_counter() - tool_started) * 1000,
                tool_name=tool.name, reason_code="tool_invocation_error",
            )
            raise
        record_runtime_event(
            "tool.returned", "tool", "returned",
            duration_ms=(perf_counter() - tool_started) * 1000,
            tool_name=tool.name,
        )
        return result

    return StructuredTool.from_function(
        coroutine=guarded_coroutine,
        name=tool.name,
        description=getattr(tool, "description", ""),
        args_schema=getattr(tool, "args_schema", None),
    )
