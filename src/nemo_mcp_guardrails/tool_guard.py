from typing import Any

from langchain_core.tools import StructuredTool

from nemo_mcp_guardrails.database.policy_loader import load_input_policy_objects
from nemo_mcp_guardrails.policy_compiler import compile_blocked_tools

STATIC_BLOCKED_GITHUB_MCP_TOOLS: frozenset[str] = frozenset()

BLOCKED_GITHUB_MCP_TOOLS = STATIC_BLOCKED_GITHUB_MCP_TOOLS | compile_blocked_tools(
    load_input_policy_objects()
)

TOOL_GUARD_REFUSAL = (
    "I can inspect GitHub information, but I cannot perform write actions "
    "or reveal credentials."
)


def guard_mcp_tool(tool: Any) -> Any:
    """Wrap an MCP tool so restricted tool names cannot execute."""

    async def guarded_coroutine(**kwargs: Any) -> Any:
        """Block restricted tools and forward allowed calls to the real MCP tool."""

        if tool.name in BLOCKED_GITHUB_MCP_TOOLS:
            return f"Tool call blocked by guard: {TOOL_GUARD_REFUSAL}"

        return await tool.ainvoke(kwargs)

    return StructuredTool.from_function(
        coroutine=guarded_coroutine,
        name=tool.name,
        description=getattr(tool, "description", ""),
        args_schema=getattr(tool, "args_schema", None),
    )
