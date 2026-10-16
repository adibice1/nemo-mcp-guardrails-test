"""Offline authorization and credential-destination regressions for LLM configs."""

import asyncio
import os
from functools import partial
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from _bootstrap import bootstrap_src

bootstrap_src()


def main() -> None:
    """Use real JWT checks, SQLite, and mock HTTP transports without external calls."""

    settings = {
        "PYTHON_DOTENV_DISABLED": "1", "DATABASE_URL": "sqlite://",
        "NEMO_POLICY_SOURCE": "defaults",
        "GMS_JWT_SECRET": "llm-security-test-secret-with-at-least-32-characters",
        "AZURE_OPENAI_ENDPOINT": "https://example.openai.azure.com",
        "AZURE_OPENAI_API_KEY": "fake-default-key",
        "GMS_ALLOWED_LLM_ENDPOINTS": "",
        "GMS_ALLOWED_LLM_CREDENTIAL_ENV_VARS": "",
    }
    with patch.dict(os.environ, settings):
        import httpx
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from openai import APIStatusError, DefaultAsyncHttpxClient, DefaultHttpxClient
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool
        from nemo_mcp_guardrails.api import llm_configs, runtime
        from nemo_mcp_guardrails.api.auth import require_authenticated_app
        from nemo_mcp_guardrails.database.connection import get_db
        from nemo_mcp_guardrails.database.models import LlmConfigRecord, UserRecord
        from nemo_mcp_guardrails.llm_security import LlmEndpointError, validate_llm_endpoint
        from nemo_mcp_guardrails.management_auth import create_access_token
        from nemo_mcp_guardrails import runtime_factory as factory

        engine = create_engine("sqlite://", poolclass=StaticPool,
                               connect_args={"check_same_thread": False})
        UserRecord.__table__.create(engine)
        LlmConfigRecord.__table__.create(engine)
        sessions = sessionmaker(bind=engine)
        headers = {}
        with sessions.begin() as db:
            for role in ("developer", "admin"):
                user = UserRecord(email=f"{role}@example.com", name=role, username=role,
                                  password_hash="unused", system_role=role, enabled=True)
                db.add(user)
                db.flush()
                headers[role] = {"Authorization": "Bearer " + create_access_token(user)}

        def test_db():
            """Supply disposable sessions for real management authentication."""
            with sessions() as db:
                yield db

        app = FastAPI()
        app.include_router(llm_configs.router)
        app.include_router(runtime.router)
        app.dependency_overrides[get_db] = test_db
        app.dependency_overrides[require_authenticated_app] = lambda: SimpleNamespace(
            id=1, client_id="offline-runtime"
        )
        payload = {"name": "Approved", "model_name": "fake-deployment",
                   "endpoint": "https://EXAMPLE.openai.azure.com:443/",
                   "credential_reference": "env:AZURE_OPENAI_API_KEY"}
        invalid = (
            "https://attacker.invalid",
            "https://example.openai.azure.com.attacker.invalid",
            "https://example.openai.azure.com@attacker.invalid",
            "http://example.openai.azure.com",
            "https://user:PRIVATE_MARKER@example.openai.azure.com",
            "https://example.openai.azure.com/openai",
            "https://example.openai.azure.com/?key=PRIVATE_MARKER",
            "https://example.openai.azure.com/#PRIVATE_MARKER",
            "https://example.openai.azure.com:444",
            "https://example.openai.azure.com:invalid",
            "https://example.openai.azure.com\\@attacker.invalid",
            "https://example.openai.azure.com\n.attacker.invalid",
        )
        with TestClient(app) as client:
            assert client.post("/llm-configs", json=payload).status_code == 401
            assert client.post("/llm-configs", headers=headers["developer"],
                               json=payload).status_code == 403
            created = client.post("/llm-configs", headers=headers["admin"], json=payload)
            assert created.status_code == 201, created.status_code
            assert created.json()["endpoint"] == "https://example.openai.azure.com"
            assert "credential_reference" not in created.json()
            assert client.post("/llm-configs", headers=headers["admin"],
                               json=payload).status_code == 409
            choices = client.get("/llm-configs", headers=headers["developer"])
            assert choices.status_code == 403
            choices = client.get("/llm-configs", headers=headers["admin"])
            assert choices.status_code == 200 and len(choices.json()) == 1
            assert "credential_reference" not in choices.json()[0]
            fallback = dict(payload, name="Default", endpoint=None)
            assert client.post("/llm-configs", headers=headers["admin"],
                               json=fallback).status_code == 201
            for endpoint in invalid:
                response = client.post("/llm-configs", headers=headers["admin"],
                                       json=dict(payload, name="Rejected", endpoint=endpoint))
                assert response.status_code == 400, endpoint
                assert "PRIVATE_MARKER" not in response.text
            execute = AsyncMock()
            with patch.object(runtime, "build_guardrails_runtime_parts",
                              AsyncMock(side_effect=LlmEndpointError("PRIVATE_MARKER"))), patch.object(
                runtime, "execute_guarded_message", execute
            ):
                response = client.post("/v1/guardrails/run", json={"message": "Hello"})
            assert response.status_code == 503 and "PRIVATE_MARKER" not in response.text
            execute.assert_not_called()

        environment = factory.RuntimeEnvironment(
            "fake-default-key", settings["AZURE_OPENAI_ENDPOINT"], "2024-02-15-preview",
            "fake-deployment", "fake-pat", "1",
        )
        for purpose in ("main agent", "guardrail"):
            for endpoint in invalid:
                config = factory.RuntimeLlmConfig(
                    "Legacy", "azure_openai", "fake", endpoint, "env:GMS_JWT_SECRET", True
                )
                with patch.object(factory, "resolve_llm_credential") as credential, patch.object(
                    factory, "AzureChatOpenAI"
                ) as constructor:
                    try:
                        factory.build_chat_model(environment, config, purpose)
                    except LlmEndpointError:
                        pass
                    else:
                        raise AssertionError("Unapproved legacy endpoint executed")
                    credential.assert_not_called()
                    constructor.assert_not_called()
        with patch.dict(os.environ, {"GMS_ALLOWED_LLM_ENDPOINTS": "https://second.example.com/"}):
            assert validate_llm_endpoint("https://SECOND.example.com:443/") == "https://second.example.com"
        with patch.dict(os.environ, {"GMS_ALLOWED_LLM_ENDPOINTS": "http://invalid.example.com"}):
            try:
                validate_llm_endpoint(settings["AZURE_OPENAI_ENDPOINT"])
            except LlmEndpointError:
                pass
            else:
                raise AssertionError("Malformed backend allowlist must fail closed")

        async def check_redirects():
            """Prove neither SDK transport forwards credentials to redirect targets."""
            observed = []

            def redirect(request):
                """Return a synthetic redirect without making a network request."""
                observed.append(request)
                return httpx.Response(307, headers={"Location": "https://attacker.invalid/"})

            transport = httpx.MockTransport(redirect)
            with patch.object(factory, "DefaultHttpxClient",
                              partial(DefaultHttpxClient, transport=transport)), patch.object(
                factory, "DefaultAsyncHttpxClient",
                partial(DefaultAsyncHttpxClient, transport=transport)
            ):
                model = factory.build_chat_model(environment, None, "main agent")
            try:
                assert model.http_client.follow_redirects is False
                assert model.http_async_client.follow_redirects is False
                for asynchronous in (False, True):
                    try:
                        if asynchronous:
                            await model.ainvoke("Offline test")
                        else:
                            model.invoke("Offline test")
                    except APIStatusError as error:
                        assert error.status_code == 307
                    else:
                        raise AssertionError("SDK should reject a redirect")
                assert len(observed) == 2
                assert all(req.url.host == "example.openai.azure.com" for req in observed)
                assert all(req.headers["api-key"] == "fake-default-key" for req in observed)
            finally:
                model.root_client.close()
                await model.root_async_client.close()

        asyncio.run(check_redirects())
        engine.dispose()
        print("LLM authorization, legacy endpoint, and sync/async redirect checks passed.")


if __name__ == "__main__":
    main()
