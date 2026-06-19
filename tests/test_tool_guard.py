import asyncio
import os
from typing import Any

from _bootstrap import bootstrap_src

os.environ.setdefault("NEMO_POLICY_SOURCE", "defaults")

bootstrap_src()

from nemo_mcp_guardrails.tool_guard import (
    BLOCKED_GITHUB_MCP_TOOLS,
    TOOL_GUARD_REFUSAL,
    guard_mcp_tool,
)


class FakeTool:
    """Minimal async tool used to test tool_guard.py without GitHub MCP."""

    def __init__(self, name: str) -> None:
        """Create a fake tool and record future calls for assertions."""

        self.name = name
        self.description = "Fake MCP tool for guard testing."
        self.args_schema = None
        self.calls: list[dict[str, Any]] = []

    async def ainvoke(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Record the call and return a simple fake tool result."""

        self.calls.append(kwargs)
        return {
            "tool": self.name,
            "called": True,
        }


async def main() -> None:
    """Verify restricted tools are blocked and allowed tools still execute."""

    blocked_tools = [FakeTool(tool_name) for tool_name in BLOCKED_GITHUB_MCP_TOOLS]
    allowed_tool = FakeTool("search_repositories")

    guarded_allowed_tool = guard_mcp_tool(allowed_tool)
    allowed_result = await guarded_allowed_tool.ainvoke({})

    expected_blocked_result = f"Tool call blocked by guard: {TOOL_GUARD_REFUSAL}"

    for blocked_tool in blocked_tools:
        guarded_blocked_tool = guard_mcp_tool(blocked_tool)
        blocked_result = await guarded_blocked_tool.ainvoke({})

        assert blocked_result == expected_blocked_result
        assert blocked_tool.calls == []

    assert allowed_result == {
        "tool": "search_repositories",
        "called": True,
    }
    assert allowed_tool.calls == [{}]

    app_a_issue_tool = FakeTool("issue_write")
    app_b_issue_tool = FakeTool("issue_write")

    app_a_guard = guard_mcp_tool(
        app_a_issue_tool,
        blocked_tool_names=frozenset({"issue_write"}),
    )
    app_b_guard = guard_mcp_tool(
        app_b_issue_tool,
        blocked_tool_names=frozenset(),
    )

    app_a_result = await app_a_guard.ainvoke({})
    app_b_result = await app_b_guard.ainvoke({})

    assert app_a_result == expected_blocked_result
    assert app_a_issue_tool.calls == []
    assert app_b_result == {
        "tool": "issue_write",
        "called": True,
    }
    assert app_b_issue_tool.calls == [{}]

    print("Tool guard checks passed.")
    for blocked_tool in sorted(BLOCKED_GITHUB_MCP_TOOLS):
        print(f"- Blocked tool was not executed: {blocked_tool}")
    print("- Allowed tool executed normally: search_repositories")
    print("- App A blocked issue_write using its scoped tool set")
    print("- App B allowed issue_write using its scoped tool set")


if __name__ == "__main__":
    asyncio.run(main())
