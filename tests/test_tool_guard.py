import asyncio
import os
from typing import Any

from _bootstrap import bootstrap_src
from pydantic import BaseModel

os.environ.setdefault("NEMO_POLICY_SOURCE", "defaults")

bootstrap_src()

from nemo_mcp_guardrails.tool_guard import (
    BLOCKED_GITHUB_MCP_TOOLS,
    TOOL_GUARD_REFUSAL,
    ToolGuardRule,
    guard_mcp_tool,
)


class FakeIssueArguments(BaseModel):
    """Match the structured title argument exposed by the GitHub issue tool."""

    title: str
    repository: str = "nemo-mcp-guardrails-test"


class FakeTool:
    """Minimal async tool used to test tool_guard.py without GitHub MCP."""

    def __init__(self, name: str, args_schema: type[BaseModel] | None = None) -> None:
        """Create a fake tool and record future calls for assertions."""

        self.name = name
        self.description = "Fake MCP tool for guard testing."
        self.args_schema = args_schema
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

    conditional_issue_tool = FakeTool("issue_write", FakeIssueArguments)
    conditional_issue_guard = guard_mcp_tool(
        conditional_issue_tool,
        guard_rules=(
            ToolGuardRule(
                tool_names=frozenset({"issue_write"}),
                custom_resource='issue named "test"',
            ),
        ),
    )

    matching_result = await conditional_issue_guard.ainvoke({"title": "test"})
    nonmatching_result = await conditional_issue_guard.ainvoke(
        {"title": "another issue"}
    )

    assert matching_result == expected_blocked_result
    assert nonmatching_result == {
        "tool": "issue_write",
        "called": True,
    }
    assert conditional_issue_tool.calls == [
        {
            "title": "another issue",
            "repository": "nemo-mcp-guardrails-test",
        }
    ]

    print("Tool guard checks passed.")
    for blocked_tool in sorted(BLOCKED_GITHUB_MCP_TOOLS):
        print(f"- Blocked tool was not executed: {blocked_tool}")
    print("- Allowed tool executed normally: search_repositories")
    print("- App A blocked issue_write using its scoped tool set")
    print("- App B allowed issue_write using its scoped tool set")
    print('- Conditional rule blocked title "test" and allowed another title')


if __name__ == "__main__":
    asyncio.run(main())
