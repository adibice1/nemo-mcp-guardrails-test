import logging
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from time import perf_counter
from uuid import uuid4

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send


_LOGGER = logging.getLogger("uvicorn.error.gms.performance")
_STAGE_TIMINGS: ContextVar[list[tuple[str, float]] | None] = ContextVar(
    "gms_stage_timings", default=None
)


@contextmanager
def measure_stage(name: str) -> Iterator[None]:
    """Record an internal stage duration without inspecting request data."""

    timings = _STAGE_TIMINGS.get()
    if timings is None:
        yield
        return

    started = perf_counter()
    try:
        yield
    finally:
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
