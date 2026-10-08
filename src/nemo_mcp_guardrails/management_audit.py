import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from anyio import CancelScope
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import Headers
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from nemo_mcp_guardrails.database.connection import SessionLocal
from nemo_mcp_guardrails.database.models import ManagementAuditLogRecord


_LOGGER = logging.getLogger("uvicorn.error.gms.management_audit")
_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
_ENTITY_PREFIXES = {
    "apps": "app",
    "policies": "policy",
    "global-policy-assignments": "global_policy_assignment",
    "management-users": "user",
    "llm-configs": "llm_config",
    "allowed-test-cases": "allowed_test_case",
}


def classify_management_action(
    method: str,
    path: str,
) -> tuple[str, str] | None:
    """Return a standardized action without reading request content."""

    normalized_path = path.rstrip("/") or "/"
    if method not in _MUTATING_METHODS:
        return None
    if normalized_path in {
        "/management-auth/login",
        "/management-auth/signup",
        "/policies/compile-preview",
        "/v1/guardrails/run",
    }:
        return None
    if normalized_path == "/management-auth/me" and method == "PUT":
        return "profile.updated", "profile"
    if normalized_path == "/policies/compile-rules" and method == "POST":
        return "policy_rules.compiled", "policy_rules"

    segments = normalized_path.strip("/").split("/")
    entity = _ENTITY_PREFIXES.get(segments[0])
    if entity is None:
        return None

    if "/api-key" in normalized_path:
        return "app.api_key_regenerated", "app"
    if "/connectors" in normalized_path:
        entity = "app_connector"
    elif "/policy-assignments" in normalized_path:
        entity = "app_policy_assignment"
    elif "/password" in normalized_path:
        return "user.password_reset", "user"
    elif (
        normalized_path.startswith("/management-users/")
        and "/apps" in normalized_path
    ):
        entity = "user_app_access"

    verb = {
        "POST": "created",
        "PUT": "updated",
        "PATCH": "updated",
        "DELETE": "deleted",
    }.get(method)
    return (f"{entity}.{verb}", entity) if verb else None


def _persist_management_audit(values: dict[str, Any]) -> None:
    """Save one sanitized audit record independently of endpoint transactions."""

    try:
        with SessionLocal.begin() as db:
            db.add(ManagementAuditLogRecord(**values))
    except Exception as error:
        _LOGGER.error(
            "%s",
            json.dumps(
                {
                    "schema_version": "1.0",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event": "management_audit.write_failed",
                    "severity": "ERROR",
                    "error_type": type(error).__name__,
                    "audit": values,
                },
                default=str,
            ),
        )


class ManagementAuditMiddleware:
    """Record successful and rejected GMS management mutations."""

    def __init__(self, app: ASGIApp) -> None:
        """Wrap the downstream ASGI application."""

        self.app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        """Persist mutation metadata without reading request or response bodies."""

        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        operation = classify_management_action(scope["method"], scope["path"])
        if operation is None:
            await self.app(scope, receive, send)
            return

        http_status = 500

        async def capture_status(message: Message) -> None:
            """Observe the response status while forwarding it unchanged."""

            nonlocal http_status
            if message["type"] == "http.response.start":
                http_status = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, capture_status)
        finally:
            state = scope.setdefault("state", {})
            actor = state.get("gms_management_actor") or {}
            client = scope.get("client")
            headers = Headers(scope=scope)
            action, entity_type = operation
            outcome = (
                "failed"
                if http_status >= 500
                else "rejected"
                if http_status >= 400
                else "succeeded"
            )
            values = {
                "id": uuid4().hex,
                "request_id": state.get("gms_request_id") or uuid4().hex,
                "occurred_at": datetime.now(timezone.utc),
                "actor_user_id": actor.get("user_id"),
                "actor_email": actor.get("email"),
                "actor_role": actor.get("role"),
                "action": action,
                "entity_type": entity_type,
                "target_path": scope["path"][:500],
                "http_method": scope["method"],
                "http_status": http_status,
                "outcome": outcome,
                "client_ip": client[0][:64] if client else None,
                "user_agent": (headers.get("user-agent") or "")[:500] or None,
            }
            with CancelScope(shield=True):
                await run_in_threadpool(_persist_management_audit, values)
