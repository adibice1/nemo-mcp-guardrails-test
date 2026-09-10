import json
import logging
from datetime import datetime, timezone
from time import perf_counter
from typing import Any
from uuid import uuid4

from anyio import CancelScope
from starlette.concurrency import run_in_threadpool
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from nemo_mcp_guardrails.runtime_events import capture_runtime_events

_LOGGER = logging.getLogger("uvicorn.error.gms.audit")


def _persist_runtime_log(
    values: dict[str, Any],
    detailed_events: list[dict[str, Any]],
) -> None:
    """Save metadata independently of the runtime transaction."""
    try:
        from nemo_mcp_guardrails.database.connection import SessionLocal
        from nemo_mcp_guardrails.database.models import (
            RuntimeLogEventRecord,
            RuntimeLogRecord,
        )

        severity = (
            "ERROR" if values["outcome"] in {"error", "tool_error"}
            else "WARN" if values["outcome"] in {"blocked", "rejected"}
            else "INFO"
        )
        record = RuntimeLogRecord(**values)
        record.events = [
            RuntimeLogEventRecord(
                sequence=1,
                timestamp=values["started_at"],
                event="request.received",
                severity="INFO",
                stage="request",
                outcome="started",
            ),
            *[
                RuntimeLogEventRecord(sequence=index, **event)
                for index, event in enumerate(detailed_events, start=2)
            ],
            RuntimeLogEventRecord(
                sequence=len(detailed_events) + 2,
                timestamp=values["completed_at"],
                event="request.completed",
                severity=severity,
                stage="request",
                outcome=values["outcome"],
                duration_ms=values["duration_ms"],
                reason_code=f"http_{values['http_status']}",
            ),
        ]
        with SessionLocal.begin() as db:
            db.add(record)
    except Exception as error:
        _LOGGER.error(
            "%s",
            json.dumps(
                {
                    "schema_version": "1.0",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event": "audit.write_failed",
                    "severity": "ERROR",
                    "error_type": type(error).__name__,
                    "request": values,
                    "events": detailed_events,
                },
                default=str,
            ),
        )


class RuntimeLogMiddleware:
    """Record runtime POST requests without reading bodies or credentials."""

    def __init__(self, app: ASGIApp) -> None:
        """Wrap the downstream ASGI application."""
        self.app = app

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        """Persist completed attempts, including rejected and failed requests."""
        if (
            scope["type"] != "http"
            or scope["method"] != "POST"
            or scope["path"].rstrip("/") != "/v1/guardrails/run"
        ):
            await self.app(scope, receive, send)
            return

        state = scope.setdefault("state", {})
        request_id = state.get("gms_request_id") or uuid4().hex
        state["gms_runtime_app_id"] = None
        state["gms_runtime_outcome"] = None
        started_at = datetime.now(timezone.utc)
        started = perf_counter()
        http_status = 500
        completed = False

        async def capture_status(message: Message) -> None:
            """Observe HTTP status while forwarding the response unchanged."""
            nonlocal http_status
            if message["type"] == "http.response.start":
                http_status = message["status"]
            await send(message)

        detailed_events: list[dict[str, Any]] = []
        try:
            with capture_runtime_events() as detailed_events:
                await self.app(scope, receive, capture_status)
            completed = True
        finally:
            if not completed or http_status >= 500:
                outcome = "error"
            elif http_status >= 400:
                outcome = "rejected"
            elif http_status >= 300:
                outcome = "redirected"
            elif state["gms_runtime_outcome"] in {
                "passed", "blocked", "tool_error"
            }:
                outcome = state["gms_runtime_outcome"]
            else:
                outcome = "completed"

            values = {
                "request_id": request_id,
                "schema_version": "1.0",
                "app_id": state["gms_runtime_app_id"],
                "started_at": started_at,
                "completed_at": datetime.now(timezone.utc),
                "http_status": http_status,
                "outcome": outcome,
                "duration_ms": (perf_counter() - started) * 1000,
            }
            with CancelScope(shield=True):
                await run_in_threadpool(
                    _persist_runtime_log, values, detailed_events
                )
