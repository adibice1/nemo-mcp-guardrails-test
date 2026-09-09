import asyncio
import unittest

from _bootstrap import bootstrap_src

bootstrap_src()

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from nemo_mcp_guardrails.performance import RequestTimingMiddleware, measure_stage


LOGGER = "uvicorn.error.gms.performance"


def timing_app() -> FastAPI:
    """Build a standalone app without database or external-service dependencies."""

    app = FastAPI()
    app.add_middleware(RequestTimingMiddleware)

    @app.get("/items/{item_id}")
    async def item(item_id: str) -> JSONResponse:
        """Return content that must not appear in the timing log."""

        with measure_stage("lookup"):
            await asyncio.sleep(0)
        return JSONResponse(
            {"value": item_id},
            headers={"Server-Timing": "existing;dur=1"},
        )

    @app.get("/failure")
    async def failure() -> None:
        """Raise a private diagnostic value to check timing-log redaction."""

        with measure_stage("failing_stage"):
            raise RuntimeError("private-error-content")

    @app.get("/first")
    async def first() -> dict[str, bool]:
        """Yield inside the first request's timing scope."""

        with measure_stage("first_stage"):
            await asyncio.sleep(0.01)
        return {"ok": True}

    @app.get("/second")
    async def second() -> dict[str, bool]:
        """Record a different stage during the first request."""

        with measure_stage("second_stage"):
            await asyncio.sleep(0)
        return {"ok": True}

    return app


class RequestTimingTests(unittest.TestCase):
    """Verify headers, exception behavior, privacy and request isolation."""

    def test_headers_and_private_values(self) -> None:
        """Log route templates and timings, not headers, IDs or content."""

        with TestClient(timing_app()) as client:
            with self.assertLogs(LOGGER, level="INFO") as captured:
                response = client.get(
                    "/items/private-path-value?token=private-query-value",
                    headers={"Authorization": "Bearer private-header-value"},
                )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"value": "private-path-value"})
        self.assertIn("existing;dur=1", response.headers["server-timing"])
        self.assertRegex(response.headers["server-timing"], r"gms;dur=\d+\.\d")
        request_id = response.headers["x-gms-request-id"]
        self.assertEqual(len(request_id), 32)
        log = "\n".join(captured.output)
        self.assertIn(request_id, log)
        self.assertIn("route=/items/{item_id}", log)
        self.assertIn("lookup:", log)
        for value in ("private-path-value", "private-query-value", "private-header-value"):
            self.assertNotIn(value, log)

    def test_error_is_not_swallowed_or_logged(self) -> None:
        """Preserve errors while recording the failed stage without its message."""

        with TestClient(timing_app(), raise_server_exceptions=False) as client:
            with self.assertLogs(LOGGER, level="INFO") as captured:
                response = client.get("/failure")
        self.assertEqual(response.status_code, 500)
        log = "\n".join(captured.output)
        self.assertIn("status=500", log)
        self.assertIn("failing_stage:", log)
        self.assertNotIn("private-error-content", log)

    def test_concurrent_requests_are_isolated(self) -> None:
        """Keep overlapping requests' measurements and identifiers separate."""

        async def run_requests():
            """Make two concurrent in-process HTTP requests."""

            async with AsyncClient(
                transport=ASGITransport(app=timing_app()), base_url="http://test"
            ) as client:
                return await asyncio.gather(client.get("/first"), client.get("/second"))

        with self.assertLogs(LOGGER, level="INFO") as captured:
            first, second = asyncio.run(run_requests())
        first_id = first.headers["x-gms-request-id"]
        second_id = second.headers["x-gms-request-id"]
        self.assertNotEqual(first_id, second_id)
        first_log = next(line for line in captured.output if first_id in line)
        second_log = next(line for line in captured.output if second_id in line)
        self.assertIn("first_stage:", first_log)
        self.assertNotIn("second_stage:", first_log)
        self.assertIn("second_stage:", second_log)
        self.assertNotIn("first_stage:", second_log)

    def test_stage_outside_http_does_not_log(self) -> None:
        """Keep direct diagnostic scripts working without a request context."""

        with self.assertNoLogs(LOGGER, level="INFO"):
            with measure_stage("outside_request"):
                pass


if __name__ == "__main__":
    unittest.main()
