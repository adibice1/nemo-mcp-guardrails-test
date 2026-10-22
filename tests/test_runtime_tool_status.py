"""Verify guard status from actual decisions rather than agent messages."""

import asyncio
from types import SimpleNamespace
import unittest

from _bootstrap import bootstrap_src

bootstrap_src()

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import ToolException
from nemoguardrails.rails.llm.options import RailStatus

from nemo_mcp_guardrails.guarded_execution import execute_guarded_message
from nemo_mcp_guardrails.runtime_events import (
    capture_runtime_events, observe_tool_guard, record_runtime_event,
)
from nemo_mcp_guardrails.tool_guard import guard_mcp_tool


class FakeTool:
    """Run a synthetic connector without network access."""

    name = "list_branches"
    description = "Synthetic read-only branch list."
    args_schema = {"type": "object", "properties": {}}

    def __init__(self, fail: bool = False) -> None:
        """Optionally simulate a connector failure after its guard passes."""
        self.fail = fail

    async def ainvoke(self, arguments):
        """Return fixture data or raise the connector's controlled error."""
        if self.fail:
            raise ToolException("synthetic connector failure")
        return "main"


class FakeRails:
    """Accept fixture messages or block the input before agent execution."""

    def __init__(self, block: bool = False) -> None:
        """Choose a deterministic input decision."""
        self.block = block

    async def check_async(self, messages, rail_types):
        """Return a deterministic classifier result."""
        return SimpleNamespace(status=RailStatus.BLOCKED if self.block else RailStatus.PASSED,
                               content="")


class FakeAgent:
    """Simulate current tools, old history, text-only replies and filtering."""

    def __init__(self, mode: str = "text") -> None:
        """Choose which real wrapper paths the fake agent will exercise."""
        self.mode = mode

    async def ainvoke(self, payload):
        """Invoke only fixture tools, keeping history separate from execution."""
        if self.mode == "filter":
            raise ValueError("Azure has not provided the response due to a content filter being triggered")
        if self.mode == "error_without_guard":
            raise ToolException("synthetic connector failure")
        if self.mode in {"tool", "tool_error", "blocked"}:
            tool = guard_mcp_tool(FakeTool(self.mode == "tool_error"),
                                  blocked_tool_names=frozenset({"list_branches"})
                                  if self.mode == "blocked" else frozenset())
            await tool.ainvoke({})
        messages = [AIMessage(content="Fixture answer.")]
        if self.mode in {"history", "tool", "filtered_metadata"}:
            messages = [AIMessage(content="", tool_calls=[{
                "name": "list_branches", "args": {}, "id": "fixture-call",
            }]), ToolMessage(content="main", name="list_branches", tool_call_id="fixture-call"),
                        *messages]
        if self.mode == "filtered_metadata":
            messages[-1] = AIMessage(content="", response_metadata={"finish_reason": "content_filter"})
        return {"messages": messages}


class ToolStatusTests(unittest.IsolatedAsyncioTestCase):
    """Exercise runtime statuses with no credentials, database or model calls."""

    async def run_agent(self, mode="text", *, captured=False, block=False, phrases=()):
        """Run the same guarded executor used by authenticated requests."""
        if captured:
            with capture_runtime_events() as events:
                result = await execute_guarded_message(FakeRails(block), FakeAgent(mode),
                                                       "Synthetic request.", True,
                                                       blocked_output_phrases=phrases)
            return result, events
        return await execute_guarded_message(FakeRails(block), FakeAgent(mode),
                                             "Synthetic request.", True,
                                             blocked_output_phrases=phrases)

    async def test_text_only_is_not_run(self):
        """Keep plain successful answers neutral with or without HTTP capture."""
        result = await self.run_agent()
        self.assertEqual((result.status, result.tool_guard_status), ("passed", "not run"))
        captured, events = await self.run_agent(captured=True)
        self.assertEqual(captured.tool_guard_status, "not run")
        self.assertTrue(any(item["event"] == "tool_guard.skipped" for item in events))

    async def test_history_does_not_claim_current_execution(self):
        """Ignore tool names and results present only in returned old history."""
        result = await self.run_agent("history")
        self.assertIn("list_branches", result.tool_names)
        self.assertEqual(result.tool_guard_status, "not run")

    async def test_real_wrapper_passes(self):
        """Report passed only after the actual tool wrapper checks a call."""
        result, events = await self.run_agent("tool", captured=True)
        self.assertEqual(result.tool_guard_status, "passed")
        self.assertTrue(any(item["event"] == "tool_guard.completed" and
                            item["outcome"] == "passed" for item in events))

    async def test_controlled_errors_preserve_actual_guard_outcome(self):
        """Distinguish connector errors after a check from unobserved errors."""
        for mode, expected in (("tool_error", "passed"), ("error_without_guard", "not run")):
            result = await self.run_agent(mode)
            self.assertEqual(result.status, "tool_error")
            self.assertEqual(result.tool_guard_status, expected)
        result = await self.run_agent("blocked")
        self.assertEqual((result.status, result.tool_guard_status), ("blocked", "blocked"))

    async def test_filtered_or_blocked_without_tools_is_not_run(self):
        """Cover early input, thrown/returned Azure filtering and phrase blocks."""
        for mode in ("filter", "filtered_metadata"):
            result = await self.run_agent(mode)
            self.assertEqual((result.status, result.tool_guard_status), ("blocked", "not run"))
        self.assertEqual((await self.run_agent(block=True)).tool_guard_status, "not run")
        result = await self.run_agent(phrases=("Fixture answer",))
        self.assertEqual((result.status, result.tool_guard_status), ("blocked", "not run"))

    async def test_observer_ignores_trace_limit_and_retains_failures(self):
        """Observe decisions even after HTTP metadata is capped."""
        with capture_runtime_events(), observe_tool_guard() as observation:
            for _ in range(300):
                record_runtime_event("probe", "agent", "started")
            record_runtime_event("tool_guard.started", "tool_guard", "started")
            self.assertEqual(observation.status, "not run")
            for outcome in ("passed", "blocked", "passed", "error", "passed"):
                record_runtime_event("tool_guard.completed", "tool_guard", outcome)
            self.assertEqual(observation.status, "error")

    async def test_concurrent_and_nested_observers_are_isolated(self):
        """Keep tool decisions from leaking into text-only requests."""
        async def run(mode):
            """Yield while an independent request observation is active."""
            with observe_tool_guard() as observation:
                await asyncio.sleep(0)
                if mode:
                    record_runtime_event("tool_guard.completed", "tool_guard", "passed")
            return observation.status

        self.assertEqual(await asyncio.gather(run(True), run(False)), ["passed", "not run"])
        with observe_tool_guard() as outer:
            with observe_tool_guard() as inner:
                record_runtime_event("tool_guard.completed", "tool_guard", "passed")
            self.assertEqual(inner.status, "passed")
            self.assertEqual(outer.status, "not run")

    async def test_late_callback_cannot_change_finished_observation(self):
        """Seal task-inherited state after the agent invocation ends."""
        release = asyncio.Event()

        async def late():
            """Attempt a decision after the originating invocation closes."""
            await release.wait()
            record_runtime_event("tool_guard.completed", "tool_guard", "passed")

        with observe_tool_guard() as first:
            task = asyncio.create_task(late())
        with observe_tool_guard() as second:
            release.set()
            await task
        self.assertEqual((first.status, second.status), ("not run", "not run"))


if __name__ == "__main__":
    unittest.main()
