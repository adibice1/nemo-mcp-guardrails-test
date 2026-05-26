import asyncio
from typing import Any

from _bootstrap import bootstrap_src

bootstrap_src()

from nemo_mcp_guardrails.tool_guard import TOOL_GUARD_REFUSAL, guard_mcp_tool


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

    blocked_tool = FakeTool("issue_write")
    allowed_tool = FakeTool("search_repositories")

    guarded_blocked_tool = guard_mcp_tool(blocked_tool)
    guarded_allowed_tool = guard_mcp_tool(allowed_tool)

    blocked_result = await guarded_blocked_tool.ainvoke({})
    allowed_result = await guarded_allowed_tool.ainvoke({})

    expected_blocked_result = f"Tool call blocked by guard: {TOOL_GUARD_REFUSAL}"

    assert blocked_result == expected_blocked_result
    assert blocked_tool.calls == []
    assert allowed_result == {
        "tool": "search_repositories",
        "called": True,
    }
    assert allowed_tool.calls == [{}]

    print("Tool guard checks passed.")
    print("- Blocked tool was not executed: issue_write")
    print("- Allowed tool executed normally: search_repositories")


if __name__ == "__main__":
    asyncio.run(main())
