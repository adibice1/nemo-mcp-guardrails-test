from dataclasses import dataclass
from typing import Any

from nemoguardrails import LLMRails
from nemoguardrails.rails.llm.options import RailStatus, RailType

from nemo_mcp_guardrails.tool_guard import TOOL_GUARD_REFUSAL


@dataclass(frozen=True)
class GuardedExecutionResult:
    """Represent the result of one guarded message execution."""

    status: str
    response: str
    input_rail_status: RailStatus
    output_rail_status: RailStatus | None
    tool_names: tuple[str, ...]
    agent_result: dict[str, Any] | None
    input_rail_result: Any
    output_rail_result: Any | None


def extract_tool_names(result: dict[str, Any]) -> tuple[str, ...]:
    """Return tool names observed in an agent result."""

    tool_names: list[str] = []

    def add_tool_name(name: str | None) -> None:
        """Append a tool name once while preserving order."""

        if name and name not in tool_names:
            tool_names.append(name)

    for message in result.get("messages", []):
        for tool_call in getattr(message, "tool_calls", None) or []:
            if isinstance(tool_call, dict):
                add_tool_name(tool_call.get("name"))
            else:
                add_tool_name(getattr(tool_call, "name", None))

        add_tool_name(getattr(message, "name", None))

    return tuple(tool_names)


async def apply_output_rail(
    rails: LLMRails,
    user_prompt: str,
    response: str,
) -> tuple[str, Any]:
    """Apply the output rail and return its response and full result."""

    result = await rails.check_async(
        [
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": response},
        ],
        rail_types=[RailType.OUTPUT],
    )

    if result.status == RailStatus.BLOCKED:
        return TOOL_GUARD_REFUSAL, result

    if result.status == RailStatus.MODIFIED and result.content:
        return result.content, result

    return response, result


async def execute_guarded_message(
    rails: LLMRails,
    agent: Any,
    message: str,
    output_rail_enabled: bool,
) -> GuardedExecutionResult:
    """Execute one message through input rails, agent, tools, and output rails."""

    input_result = await rails.check_async(
        [{"role": "user", "content": message}],
        rail_types=[RailType.INPUT],
    )

    if input_result.status == RailStatus.BLOCKED:
        response = TOOL_GUARD_REFUSAL
        output_result = None

        if output_rail_enabled:
            response, output_result = await apply_output_rail(
                rails,
                message,
                response,
            )

        return GuardedExecutionResult(
            status="blocked",
            response=response,
            input_rail_status=input_result.status,
            output_rail_status=output_result.status if output_result else None,
            tool_names=(),
            agent_result=None,
            input_rail_result=input_result,
            output_rail_result=output_result,
        )

    prompt_for_agent = (
        input_result.content
        if input_result.status == RailStatus.MODIFIED
        else message
    )

    agent_result = await agent.ainvoke(
        {
            "messages": [
                {"role": "user", "content": prompt_for_agent},
            ]
        }
    )

    response = str(agent_result["messages"][-1].content)
    output_result = None

    if output_rail_enabled:
        response, output_result = await apply_output_rail(
            rails,
            prompt_for_agent,
            response,
        )

    return GuardedExecutionResult(
        status="passed",
        response=response,
        input_rail_status=input_result.status,
        output_rail_status=output_result.status if output_result else None,
        tool_names=extract_tool_names(agent_result),
        agent_result=agent_result,
        input_rail_result=input_result,
        output_rail_result=output_result,
    )
