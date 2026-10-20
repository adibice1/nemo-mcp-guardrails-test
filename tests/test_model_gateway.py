"""Offline gateway protocol, grants, tools, classifier and authoring regressions."""

import asyncio
import json
import logging
import os
from functools import partial
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import AsyncMock, MagicMock, patch

from _bootstrap import bootstrap_src

bootstrap_src()


def main() -> None:
    """Exercise real clients and management routes with disposable transports/stores."""
    settings = {
        "PYTHON_DOTENV_DISABLED": "1", "DATABASE_URL": "sqlite://",
        "GMS_JWT_SECRET": "gateway-test-secret-at-least-thirty-two-characters",
        "AZURE_OPENAI_API_KEY": "", "AZURE_OPENAI_ENDPOINT": "",
        "AZURE_OPENAI_API_VERSION": "", "AZURE_OPENAI_DEPLOYMENT": "",
        "GMS_ALLOWED_COMPATIBLE_LLM_ENDPOINTS": "https://gateway.example/v1,http://127.0.0.1:4000/v1",
        "GMS_ALLOWED_LLM_CREDENTIAL_ENV_VARS": "GATEWAY_TEST_KEY", "GATEWAY_TEST_KEY": "fake-gateway-key",
        "GITHUB_PERSONAL_ACCESS_TOKEN": "fake-pat", "GITHUB_MCP_READ_ONLY": "1",
        "GMS_POLICY_AI_PROVIDER": "openai_compatible", "GMS_POLICY_AI_ENDPOINT": "https://gateway.example/v1",
        "GMS_POLICY_AI_MODEL": "authoring-profile", "GMS_POLICY_AI_CREDENTIAL_REFERENCE": "env:GATEWAY_TEST_KEY",
    }
    with patch.dict(os.environ, settings):
        import httpx
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from langchain.agents import create_agent
        from langchain_core.tools import tool
        from nemoguardrails import LLMRails, RailsConfig
        from nemoguardrails.exceptions import LLMCallException
        from nemoguardrails.rails.llm.options import RailStatus, RailType
        from openai import APIStatusError, DefaultAsyncHttpxClient, DefaultHttpxClient
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool
        from nemo_mcp_guardrails import runtime_factory as factory
        from nemo_mcp_guardrails.api import app_llm_grants, apps, llm_configs, policy_assistant, runtime
        from nemo_mcp_guardrails.api.auth import require_authenticated_app
        from nemo_mcp_guardrails.classifier_model import ClassifierResponseError
        from nemo_mcp_guardrails.database.connection import get_db
        from nemo_mcp_guardrails.database.models import (
            AppLlmGrantRecord, AppRecord, AppUserRecord, LlmConfigRecord, UserRecord,
        )
        from nemo_mcp_guardrails.llm_access import LlmAccessError
        from nemo_mcp_guardrails.llm_credentials import LlmCredentialError
        from nemo_mcp_guardrails.llm_profiles import validate_profile_metadata
        from nemo_mcp_guardrails.llm_security import LlmEndpointError, validate_compatible_llm_endpoint
        from nemo_mcp_guardrails.management_auth import create_access_token

        check = TestCase()
        endpoint = "https://gateway.example/v1"
        config = factory.RuntimeLlmConfig("Gateway", "openai_compatible", "main-profile",
                                          endpoint, "env:GATEWAY_TEST_KEY", True)
        selection = factory.RuntimeLlmSelection(config, config, (1, 2))
        environment = factory.load_runtime_environment(llm_selection=selection)
        assert not environment.azure_api_key
        assert os.getenv("OPENAI_API_KEY") is None
        with check.assertRaises(LlmCredentialError):
            factory.load_runtime_environment()
        for value in ("https://gateway.example/other", "https://gateway.example/v1/../v1",
                      "https://gateway.example/v1/%2e%2e", "https://gateway.example//v1",
                      "https://gateway.example/v1?key=PRIVATE", "https://user:PRIVATE@gateway.example/v1",
                      "https://gateway.example/v1#PRIVATE", "https://gateway.example/v1\n",
                      "http://gateway.example/v1", "http://localhost:4000/v1",
                      "http://169.254.169.254/v1", "https://gateway.example.attacker.invalid/v1"):
            with check.assertRaises(LlmEndpointError):
                validate_compatible_llm_endpoint(value)
        assert validate_compatible_llm_endpoint("https://GATEWAY.example:443/v1/") == endpoint
        assert validate_compatible_llm_endpoint("http://127.0.0.1:4000/v1/").startswith("http://127.0.0.1")
        with patch.dict(os.environ, {"GMS_ALLOWED_COMPATIBLE_LLM_ENDPOINTS": endpoint + ",http://remote.example/v1"}):
            with check.assertRaises(LlmEndpointError):
                validate_compatible_llm_endpoint(endpoint)
        for reference in (None, "", "env:GMS_JWT_SECRET", "raw-secret", "vault:secret"):
            with check.assertRaises(LlmCredentialError):
                validate_profile_metadata("openai_compatible", endpoint, reference)
        with patch.object(factory, "resolve_llm_credential") as lookup:
            with check.assertRaises(LlmEndpointError):
                factory.build_chat_model(environment, factory.RuntimeLlmConfig(
                    "Bad", "openai_compatible", "model", "https://attacker.invalid/v1", "env:GATEWAY_TEST_KEY", True,
                ), "main agent")
            lookup.assert_not_called()

        engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
        for record in (UserRecord, LlmConfigRecord, AppRecord, AppUserRecord, AppLlmGrantRecord):
            record.__table__.create(engine)
        sessions = sessionmaker(bind=engine, expire_on_commit=False)
        headers = {}
        with sessions.begin() as db:
            for role in ("admin", "developer"):
                user = UserRecord(email=role + "@example.invalid", name=role, username=role,
                                  password_hash="unused", system_role=role, enabled=True)
                db.add(user); db.flush()
                headers[role] = {"Authorization": "Bearer " + create_access_token(user)}
                if role == "developer":
                    developer_id = user.id
            db.add(AppRecord(id=1, name="Gateway app", client_id="gateway-app", api_key_hash="unused", authorized=True))
            db.flush()
            db.add(AppUserRecord(app_id=1, user_id=developer_id, role="admin"))

        def test_db():
            """Provide isolated sessions to the real JWT/RBAC dependencies."""
            with sessions() as db:
                yield db

        app = FastAPI()
        for router in (llm_configs.router, apps.router, app_llm_grants.router):
            app.include_router(router)
        app.dependency_overrides[get_db] = test_db
        payload = {"name": "Gateway", "provider": "openai_compatible", "model_name": "main-profile",
                   "endpoint": endpoint, "credential_reference": "env:GATEWAY_TEST_KEY"}
        with TestClient(app) as client, patch.object(factory, "SessionLocal", sessions):
            assert client.post("/llm-configs", json=payload).status_code == 401
            assert client.post("/llm-configs", headers=headers["developer"], json=payload).status_code == 403
            created = client.post("/llm-configs", headers=headers["admin"], json=payload)
            assert created.status_code == 201, created.text
            model_id = created.json()["id"]
            assert "credential_reference" not in created.json() and "fake-gateway-key" not in created.text
            for invalid in ({"endpoint": None}, {"credential_reference": None}, {"endpoint": "https://attacker.invalid/v1"}):
                response = client.post("/llm-configs", headers=headers["admin"], json={**payload, "name": "Bad", **invalid})
                assert response.status_code == 400, response.text
            assert client.put("/apps/1", headers=headers["developer"], json={"main_llm_config_id": model_id}).status_code == 403
            for purpose in ("main", "guardrail"):
                path = f"/apps/1/llm-grants/{purpose}/{model_id}"
                assert client.put(path, headers=headers["developer"], json={"enabled": True}).status_code == 403
                assert client.put(path, headers=headers["admin"], json={"enabled": True}).status_code == 200
            assert client.put("/apps/1", headers=headers["developer"], json={"main_llm_config_id": model_id}).status_code == 200
            assert client.put("/apps/1", headers=headers["developer"], json={"guardrail_llm_config_id": model_id}).status_code == 403
            assert client.put("/apps/1", headers=headers["admin"], json={"guardrail_llm_config_id": model_id}).status_code == 200
            selected = factory.load_runtime_llm_selection(1)
            assert selected.main_llm_config.provider == "openai_compatible"
            async def cache_checks():
                """Invalidate a warm runtime when the compatible model profile changes."""
                factory.clear_guardrails_runtime_cache()
                with patch.object(factory, "load_runtime_policy_snapshot", return_value=("fixture",)), patch.object(
                    factory, "load_runtime_revision", return_value=()
                ), patch.object(factory, "_build_guardrails_runtime_parts_uncached", AsyncMock(return_value=object())) as build:
                    first = await factory.build_guardrails_runtime_parts(1)
                    assert await factory.build_guardrails_runtime_parts(1) is first
                    assert build.await_count == 1
                    with sessions.begin() as db:
                        db.get(LlmConfigRecord, model_id).model_name = "changed-profile"
                    await factory.build_guardrails_runtime_parts(1)
                    assert build.await_count == 2
                    assert client.delete(f"/apps/1/llm-grants/main/{model_id}", headers=headers["admin"]).status_code == 204
                    with check.assertRaises(LlmAccessError):
                        await factory.build_guardrails_runtime_parts(1)
                    assert build.await_count == 2
                factory.clear_guardrails_runtime_cache()

            asyncio.run(cache_checks())
            with check.assertRaises(LlmAccessError):
                factory.load_runtime_llm_selection(1)

        observed = []
        state = {"mode": "chat", "text": "no", "finish": "stop"}
        tool_calls = []

        @tool
        def read_marker() -> str:
            """Return a harmless marker without any connector or network access."""
            tool_calls.append("read")
            return "fixture-marker"

        def respond(request):
            """Implement a synthetic standard chat-completion service."""
            observed.append(request)
            assert request.url == httpx.URL(endpoint + "/chat/completions")
            assert request.headers["Authorization"] == "Bearer fake-gateway-key"
            body = json.loads(request.content)
            if state["mode"] == "redirect":
                return httpx.Response(307, headers={"Location": "https://attacker.invalid/v1"})
            message = {"role": "assistant", "content": state["text"]}
            finish = state["finish"]
            if state["mode"] == "tools":
                if not any(item["role"] == "tool" for item in body["messages"]):
                    message = {"role": "assistant", "content": None, "tool_calls": [{"id": "call_fixture", "type": "function",
                               "function": {"name": "read_marker", "arguments": "{}"}}]}
                    finish = "tool_calls"
                else:
                    message["content"] = "Marker read."
            return httpx.Response(200, json={"id": "offline-completion", "object": "chat.completion", "created": 1,
                "model": body["model"], "choices": [{"index": 0, "message": message, "finish_reason": finish}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}})

        async def clients():
            """Verify sync/async requests, agent tools, real rails and redirect refusal."""
            transport = httpx.MockTransport(respond)
            with patch.object(factory, "DefaultHttpxClient", partial(DefaultHttpxClient, transport=transport)), patch.object(
                factory, "DefaultAsyncHttpxClient", partial(DefaultAsyncHttpxClient, transport=transport)
            ):
                model = factory.build_chat_model(environment, config, "main agent")
                classifier = factory.build_chat_model(environment, config, "guardrail")
            try:
                assert model.invoke("Hello").content == "no"
                assert (await model.ainvoke("Hello")).content == "no"
                assert (await classifier.ainvoke("Classify")).content == "no"
                for text, finish in (("Here is my answer: no", "stop"), ("", "stop"), ("no", "length"), ("no", "content_filter")):
                    state.update(text=text, finish=finish)
                    with check.assertRaises(ClassifierResponseError):
                        await classifier.ainvoke("Classify")
                state.update(text="no", finish="stop", mode="tools")
                agent = create_agent(model=model, tools=[read_marker])
                answer = await agent.ainvoke({"messages": [{"role": "user", "content": "Read the marker"}]})
                assert tool_calls == ["read"] and answer["messages"][-1].content == "Marker read."
                state.update(mode="chat")
                rails = LLMRails(RailsConfig.from_path("config"), llm=classifier)
                for rail_type, messages in (
                    (RailType.INPUT, [{"role": "user", "content": "Read public information"}]),
                    (RailType.OUTPUT, [{"role": "user", "content": "Read"}, {"role": "assistant", "content": "Public information"}]),
                ):
                    for text, expected in (("no", RailStatus.PASSED), ("yes", RailStatus.BLOCKED)):
                        state.update(text=text)
                        result = await rails.check_async(messages, rail_types=[rail_type])
                        assert result.status == expected, (rail_type, result)
                    for text, finish in (("not a decision", "stop"), ("", "stop"), ("no", "length")):
                        state.update(text=text, finish=finish)
                        prior_logging = logging.root.manager.disable
                        logging.disable(logging.CRITICAL)
                        try:
                            with check.assertRaises(LLMCallException):
                                await rails.check_async(messages, rail_types=[rail_type])
                        finally:
                            logging.disable(prior_logging)
                    state.update(finish="stop")
                # A real malformed rail must never execute the agent or store a response.
                state.update(mode="chat", text="PRIVATE_INVALID_CLASSIFICATION", finish="stop")
                runtime_app = FastAPI()
                runtime_app.include_router(runtime.router)
                runtime_app.dependency_overrides[get_db] = test_db
                runtime_app.dependency_overrides[require_authenticated_app] = lambda: SimpleNamespace(id=1, client_id="fixture")
                agent_boundary = SimpleNamespace(ainvoke=AsyncMock())
                parts = SimpleNamespace(rails=rails, agent=agent_boundary, output_rail_enabled=False, blocked_output_phrases=())
                prior_logging = logging.root.manager.disable
                logging.disable(logging.CRITICAL)
                try:
                    with patch.object(runtime, "build_guardrails_runtime_parts", AsyncMock(return_value=parts)), patch.object(
                        runtime, "_store_conversation_turns"
                    ) as history, TestClient(runtime_app) as client:
                        response = client.post("/v1/guardrails/run", json={"message": "Read public information"})
                        assert response.status_code == 503 and "PRIVATE_INVALID_CLASSIFICATION" not in response.text
                        agent_boundary.ainvoke.assert_not_awaited()
                        history.assert_not_called()
                finally:
                    logging.disable(prior_logging)
                state.update(mode="redirect", text="no")
                before = len(observed)
                with check.assertRaises(APIStatusError):
                    model.invoke("Hello")
                with check.assertRaises(APIStatusError):
                    await model.ainvoke("Hello")
                assert len(observed) == before + 2
            finally:
                model.root_client.close(); await model.root_async_client.close()
                classifier.wrapped.root_client.close(); await classifier.wrapped.root_async_client.close()

        asyncio.run(clients())

        async def authoring():
            """Use the independent authoring profile and preserve JSON draft validation."""
            valid = {"draft": None, "related": [], "clarification": "Which restriction do you want?"}
            provider = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=AsyncMock(return_value=
                SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop", message=SimpleNamespace(
                    content=json.dumps(valid), refusal=None))])))))
            context = MagicMock()
            context.__aenter__ = AsyncMock(return_value=provider)
            context.__aexit__ = AsyncMock(return_value=None)
            with patch.object(policy_assistant, "AsyncOpenAI", return_value=context) as compatible, patch.object(
                policy_assistant, "AsyncAzureOpenAI"
            ) as azure:
                result = await policy_assistant.generate_suggestions("Draft a restriction", [])
                assert result.model_dump() == valid
                assert compatible.call_args.kwargs["base_url"] == endpoint
                assert compatible.call_args.kwargs["api_key"] == "fake-gateway-key"
                assert compatible.call_args.kwargs["http_client"].follow_redirects is False
                assert provider.chat.completions.create.call_args.kwargs["model"] == "authoring-profile"
                azure.assert_not_called()
                await compatible.call_args.kwargs["http_client"].aclose()

        asyncio.run(authoring())
        engine.dispose()
    print("Gateway checks passed: profiles, RBAC/grants, no Azure dependency, real chat/tool/rail transports, strict classification, redirects and authoring.")


if __name__ == "__main__":
    main()
