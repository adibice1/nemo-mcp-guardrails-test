import re
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any


_MAX_EVENTS = 256
_STAGES = ("input", "agent", "tool_guard", "tool", "output")
_REASONS = {
    "nemo_passed", "nemo_blocked", "nemo_modified",
    "azure_input_content_filter", "azure_content_filter",
    "azure_agent_content_filter", "azure_content_filter_fallback_passed",
    "deterministic_output_phrase", "gms_tool_guard",
    "tool_invocation_error", "stage_not_reached", "disabled",
    "event_limit_reached",
}


@dataclass
class _EventBuffer:
    """Keep one request's bounded event collection and execution markers."""

    events: list[dict[str, Any]] = field(default_factory=list)
    stages: set[str] = field(default_factory=set)
    closed: bool = False
    lock: Any = field(default_factory=Lock, repr=False)


_BUFFER: ContextVar[_EventBuffer | None] = ContextVar(
    "gms_runtime_event_buffer", default=None
)


def _event(
    event: str,
    stage: str,
    outcome: str,
    *,
    duration_ms: float | None = None,
    tool_name: str | None = None,
    reason_code: str | None = None,
) -> dict[str, Any]:
    """Build an event without accepting prompts, arguments, or responses."""
    return {
        "timestamp": datetime.now(timezone.utc),
        "event": event,
        "stage": stage,
        "outcome": outcome,
        "severity": (
            "ERROR" if outcome == "error"
            else "WARN" if outcome in {"blocked", "raised", "truncated"}
            else "INFO"
        ),
        "duration_ms": duration_ms,
        "tool_name": (
            tool_name
            if isinstance(tool_name, str)
            and re.fullmatch(r"[A-Za-z0-9_.:-]{1,200}", tool_name)
            else None
        ),
        "reason_code": (
            reason_code if reason_code in _REASONS
            else "unclassified" if reason_code is not None
            else None
        ),
    }


def record_runtime_event(
    event: str,
    stage: str,
    outcome: str,
    *,
    duration_ms: float | None = None,
    tool_name: str | None = None,
    reason_code: str | None = None,
) -> None:
    """Append metadata only while an HTTP runtime capture is active."""
    buffer = _BUFFER.get()
    if buffer is None:
        return

    with buffer.lock:
        if buffer.closed:
            return
        buffer.stages.add(stage)
        if len(buffer.events) >= _MAX_EVENTS:
            if len(buffer.events) == _MAX_EVENTS:
                buffer.events.append(_event(
                    "events.truncated", "request", "truncated",
                    reason_code="event_limit_reached",
                ))
            return
        buffer.events.append(_event(
            event, stage, outcome, duration_ms=duration_ms,
            tool_name=tool_name, reason_code=reason_code,
        ))


@contextmanager
def capture_runtime_events() -> Iterator[list[dict[str, Any]]]:
    """Isolate one trace and seal it before database persistence."""
    buffer = _EventBuffer()
    token = _BUFFER.set(buffer)
    try:
        yield buffer.events
    finally:
        with buffer.lock:
            for stage in _STAGES:
                if stage not in buffer.stages:
                    buffer.events.append(_event(
                        f"{stage}.skipped", stage, "not_run",
                        reason_code="stage_not_reached",
                    ))
            buffer.closed = True
        _BUFFER.reset(token)
