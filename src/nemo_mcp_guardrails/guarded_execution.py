from dataclasses import dataclass
from collections.abc import Mapping, Sequence
from typing import Any

from langchain_core.tools import ToolException
from nemoguardrails import LLMRails
from nemoguardrails.exceptions import LLMCallException
from nemoguardrails.rails.llm.options import RailStatus, RailType
from openai import BadRequestError

from nemo_mcp_guardrails.tool_guard import TOOL_GUARD_REFUSAL


ChatMessage = dict[str, str]
TOOL_ERROR_RESPONSE = (
    "I could not complete the connector request. "
    "Please check that the requested repository, branch, issue, pull request, "
    "file, commit, tag, or release exists, then try again with the exact owner, "
    "repository, and identifier."
)
OUTPUT_FILTER_RESPONSE = (
    "I could not return that response because it was blocked by the output safety check."
)


@dataclass(frozen=True)
class SyntheticRailResult:
    """Small rail-result substitute for controlled runtime failures."""

    status: RailStatus
    content: str


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


def build_agent_messages(
    message: str,
    conversation_history: Sequence[Mapping[str, str]] | None = None,
) -> list[ChatMessage]:
    """Return prior conversation messages followed by the current user message."""

    messages: list[ChatMessage] = []

    for item in conversation_history or []:
        messages.append(
            {
                "role": str(item["role"]),
                "content": str(item["content"]),
            }
        )

    messages.append({"role": "user", "content": message})
    return messages


def is_azure_content_filter_error(error: BaseException) -> bool:
    """Return whether an exception came from Azure content filtering."""

    inner_error = (
        error.inner_exception
        if isinstance(error, LLMCallException)
        else error
    )

    if not isinstance(inner_error, BadRequestError):
        return False

    body = inner_error.body if isinstance(inner_error.body, dict) else {}
    error_details = body.get("error", body)
    return error_details.get("code") == "content_filter"


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

    try:
        result = await rails.check_async(
            [
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": response},
            ],
            rail_types=[RailType.OUTPUT],
        )
    except LLMCallException as error:
        if not is_azure_content_filter_error(error):
            raise

        return OUTPUT_FILTER_RESPONSE, SyntheticRailResult(
            status=RailStatus.BLOCKED,
            content=OUTPUT_FILTER_RESPONSE,
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
    conversation_history: Sequence[Mapping[str, str]] | None = None,
) -> GuardedExecutionResult:
    """Execute one runtime request through rails, agent, tools, and output rails."""

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

    try:
        agent_result = await agent.ainvoke(
            {
                "messages": build_agent_messages(
                    prompt_for_agent,
                    conversation_history,
                )
            }
        )
    except ToolException:
        response = TOOL_ERROR_RESPONSE
        output_result = None

        if output_rail_enabled:
            response, output_result = await apply_output_rail(
                rails,
                prompt_for_agent,
                response,
            )

        return GuardedExecutionResult(
            status="tool_error",
            response=response,
            input_rail_status=input_result.status,
            output_rail_status=output_result.status if output_result else None,
            tool_names=(),
            agent_result=None,
            input_rail_result=input_result,
            output_rail_result=output_result,
        )

    response = str(agent_result["messages"][-1].content)
    output_result = None

    if output_rail_enabled:
        response, output_result = await apply_output_rail(
            rails,
            prompt_for_agent,
            response,
        )

    status = (
        "blocked"
        if output_result and output_result.status == RailStatus.BLOCKED
        else "passed"
    )

    return GuardedExecutionResult(
        status=status,
        response=response,
        input_rail_status=input_result.status,
        output_rail_status=output_result.status if output_result else None,
        tool_names=extract_tool_names(agent_result),
        agent_result=agent_result,
        input_rail_result=input_result,
        output_rail_result=output_result,
    )
