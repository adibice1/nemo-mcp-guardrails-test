from typing import Any

from langchain_core.tools import StructuredTool


BLOCKED_GITHUB_MCP_TOOLS = {
    "issue_write",
    "add_issue_comment",
    "create_pull_request",
    "update_pull_request",
    "merge_pull_request",
    "pull_request_review_write",
    "create_branch",
    "create_or_update_file",
    "delete_file",
    "push_files",
    "create_repository",
    "fork_repository",
}

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
