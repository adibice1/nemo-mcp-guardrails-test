"""Reject oversized ASGI request bodies before logging, JSON parsing or routing."""

from starlette.responses import JSONResponse


MAX_BODY_BYTES = 512 * 1024
MAX_MESSAGE_CHARS = 16000
MAX_HISTORY_TURNS = 32
MAX_HISTORY_CHARS = 64000


class RequestBodyLimitMiddleware:
    """Buffer at most the byte cap, including chunked or dishonest-length bodies."""

    def __init__(self, app, max_bytes: int = MAX_BODY_BYTES):
        """Set a hard raw-byte cap for every HTTP request."""
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        """Forward a bounded body or stop before the inner application runs."""
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        body = bytearray()
        size = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            size += len(message.get("body", b""))
            if size > self.max_bytes:
                return await JSONResponse({"detail": "Request body is too large."}, 413)(scope, receive, send)
            body.extend(message.get("body", b""))
            if not message.get("more_body", False):
                break
        replayed = False

        async def replay():
            """Replay consumed messages without duplicating the body buffer."""
            nonlocal replayed
            if not replayed:
                replayed = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, replay, send)


async def validation_error_response(request, error):
    """Avoid echoing passwords, oversized input or malformed Unicode in 422 bodies."""
    return JSONResponse({"detail": "Request contains invalid fields."}, status_code=422)
