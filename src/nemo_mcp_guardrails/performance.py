import logging
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from time import perf_counter
from uuid import uuid4

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from nemo_mcp_guardrails.runtime_events import record_runtime_event

_LOGGER = logging.getLogger("uvicorn.error.gms.performance")
_STAGE_TIMINGS: ContextVar[list[tuple[str, float]] | None] = ContextVar(
    "gms_stage_timings", default=None
)


@contextmanager
def measure_stage(name: str) -> Iterator[None]:
    """Record timings and observed call boundaries without request content."""
    timings = _STAGE_TIMINGS.get()
    stage = {
        "input_rail": "input",
        "agent_tools": "agent",
        "output_rail": "output",
        "output_phrase_check": "output",
    }.get(name)
    started = perf_counter()

    if stage:
        record_runtime_event(f"{name}.started", stage, "started")
    try:
        yield
    except BaseException:
        if stage:
            record_runtime_event(
                f"{name}.raised", stage, "raised",
                duration_ms=(perf_counter() - started) * 1000,
            )
        raise
    else:
        if stage:
            record_runtime_event(
                f"{name}.returned", stage, "returned",
                duration_ms=(perf_counter() - started) * 1000,
            )
    finally:
        if timings is not None:
            timings.append((name, (perf_counter() - started) * 1000))


class RequestTimingMiddleware:
    """Time HTTP requests without buffering bodies or logging their contents."""

    def __init__(self, app: ASGIApp) -> None:
        """Wrap the next ASGI application."""

        self.app = app

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        """Attach a response-start duration and log completed request timings."""

        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = uuid4().hex
        scope.setdefault("state", {})["gms_request_id"] = request_id
        timings: list[tuple[str, float]] = []
        token = _STAGE_TIMINGS.set(timings)
        started = perf_counter()
        status_code = 500

        async def send_with_timing(message: Message) -> None:
            """Add timing metadata when response headers become available."""

            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = MutableHeaders(scope=message)
                headers.append(
                    "Server-Timing",
                    f"gms;dur={(perf_counter() - started) * 1000:.1f}",
                )
                headers["X-GMS-Request-ID"] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_timing)
        finally:
            _STAGE_TIMINGS.reset(token)
            route = getattr(scope.get("route"), "path", "<unmatched>")
            stage_text = ",".join(
                f"{name}:{duration:.1f}" for name, duration in timings
            ) or "-"
            _LOGGER.info(
                "gms_timing request_id=%s method=%s route=%s status=%s "
                "total_ms=%.1f stages_ms=%s",
                request_id,
                scope["method"],
                route,
                status_code,
                (perf_counter() - started) * 1000,
                stage_text,
            )
