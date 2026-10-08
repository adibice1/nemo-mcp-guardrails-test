import asyncio
import unittest

from _bootstrap import bootstrap_src

bootstrap_src()

from nemo_mcp_guardrails.performance import measure_stage
from nemo_mcp_guardrails.runtime_events import (
    capture_runtime_events,
    record_runtime_event,
)


class RuntimeEventTests(unittest.TestCase):
    """Verify bounded, isolated traces without external services."""

    def test_returned_call_and_blocked_decision(self) -> None:
        """Distinguish a returned classifier call from its blocked verdict."""
        with capture_runtime_events() as events:
            with measure_stage("input_rail"):
                pass
            record_runtime_event(
                "rail.completed", "input", "blocked",
                reason_code="nemo_blocked",
            )
        input_events = [event for event in events if event["stage"] == "input"]
        self.assertEqual(
            [event["outcome"] for event in input_events],
            ["started", "returned", "blocked"],
        )
        self.assertEqual(
            {event["stage"] for event in events if event["outcome"] == "not_run"},
            {"agent", "tool_guard", "tool", "output"},
        )
        self.assertTrue(all(
            event["timestamp"].utcoffset().total_seconds() == 0
            for event in events
        ))

    def test_exception_content_is_not_recorded(self) -> None:
        """Record an interrupted call without storing its exception text."""
        with capture_runtime_events() as events:
            with self.assertRaises(ValueError):
                with measure_stage("agent_tools"):
                    raise ValueError("private-exception-canary")
        self.assertTrue(any(
            event["event"] == "agent_tools.raised"
            and event["outcome"] == "raised"
            for event in events
        ))
        self.assertNotIn("private-exception-canary", repr(events))

    def test_bounded_metadata(self) -> None:
        """Cap events without falsely marking a truncated stage as skipped."""
        with capture_runtime_events() as events:
            for _ in range(1000):
                record_runtime_event(
                    "rail.completed", "input", "passed",
                    tool_name="token=private-canary",
                    reason_code="private-canary",
                )
            record_runtime_event("rail.completed", "output", "passed")
        self.assertLessEqual(len(events), 262)
        self.assertEqual(
            sum(event["event"] == "events.truncated" for event in events), 1
        )
        self.assertFalse(any(
            event["event"] == "output.skipped" for event in events
        ))
        self.assertEqual(events[0]["reason_code"], "unclassified")
        self.assertNotIn("private-canary", repr(events))

    def test_concurrent_requests_are_isolated(self) -> None:
        """Keep overlapping request events in their own buffers."""
        async def run(stage: str):
            """Yield while one request's capture remains active."""
            with capture_runtime_events() as events:
                record_runtime_event("probe.started", stage, "started")
                await asyncio.sleep(0)
                record_runtime_event("probe.returned", stage, "returned")
            return events

        async def run_both():
            """Run two independent captures concurrently."""
            return await asyncio.gather(run("input"), run("output"))

        first, second = asyncio.run(run_both())
        for events, expected in ((first, "input"), (second, "output")):
            self.assertEqual(
                {event["stage"] for event in events
                 if event["outcome"] != "not_run"},
                {expected},
            )

    def test_nested_capture_restores_parent(self) -> None:
        """Restore the outer capture and ignore events outside a capture."""
        record_runtime_event("outside", "input", "started")
        with capture_runtime_events() as outer:
            record_runtime_event("outer.before", "input", "started")
            with capture_runtime_events() as inner:
                record_runtime_event("inner", "agent", "returned")
            record_runtime_event("outer.after", "input", "returned")
        self.assertEqual(
            [event["event"] for event in outer
             if event["outcome"] != "not_run"],
            ["outer.before", "outer.after"],
        )
        self.assertNotIn("outside", repr(outer))
        self.assertFalse(any(
            event["event"].startswith("outer.") for event in inner
        ))

    def test_late_callback_cannot_mutate_finished_trace(self) -> None:
        """Ignore child-task events after their originating capture closes."""
        async def run():
            """Release a child callback during a different request capture."""
            release = asyncio.Event()

            async def late():
                """Attempt to record through an inherited, closed capture."""
                await release.wait()
                record_runtime_event("late.callback", "agent", "returned")

            with capture_runtime_events() as first:
                task = asyncio.create_task(late())
            with capture_runtime_events() as second:
                release.set()
                await task
            return first, second

        first, second = asyncio.run(run())
        self.assertNotIn("late.callback", repr(first))
        self.assertNotIn("late.callback", repr(second))


if __name__ == "__main__":
    unittest.main()
