"""Offline runtime grant, cache revocation and credential-lookup regressions."""

import asyncio
import os
from contextlib import ExitStack
from dataclasses import replace
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import AsyncMock, patch

from _bootstrap import bootstrap_src

bootstrap_src()


def main() -> None:
    """Use real app/JWT authentication, SQLite grants and fake external boundaries."""

    settings = {
        "PYTHON_DOTENV_DISABLED": "1", "DATABASE_URL": "sqlite://",
        "NEMO_POLICY_SOURCE": "database", "NEMO_RUNTIME_CACHE_TTL_SECONDS": "300",
        "GMS_JWT_SECRET": "runtime-grants-fake-jwt-secret-at-least-32-characters",
        "AZURE_OPENAI_ENDPOINT": "https://example.openai.azure.com",
        "AZURE_OPENAI_API_KEY": "PRIVATE_DEFAULT_KEY", "AZURE_OPENAI_DEPLOYMENT": "fake",
        "AZURE_OPENAI_API_VERSION": "fake-version", "GITHUB_PERSONAL_ACCESS_TOKEN": "PRIVATE_PAT",
        "GMS_ALLOWED_LLM_ENDPOINTS": "", "GMS_ALLOWED_LLM_CREDENTIAL_ENV_VARS": "APP_A_KEY,APP_B_KEY",
        "APP_A_KEY": "PRIVATE_A_KEY", "APP_B_KEY": "PRIVATE_B_KEY", "NEMO_RUNTIME_DEBUG": "0",
    }
    with patch.dict(os.environ, settings):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from nemoguardrails.rails.llm.options import RailStatus
        from sqlalchemy import create_engine, select, update
        from sqlalchemy.exc import SQLAlchemyError
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool
        from nemo_mcp_guardrails import runtime_factory as factory
        from nemo_mcp_guardrails.api import app_llm_grants, runtime
        from nemo_mcp_guardrails.app_auth import hash_api_key
        from nemo_mcp_guardrails.database.connection import get_db
        from nemo_mcp_guardrails.database.models import AppLlmGrantRecord, AppRecord, LlmConfigRecord, UserRecord
        from nemo_mcp_guardrails.guarded_execution import GuardedExecutionResult
        from nemo_mcp_guardrails.llm_access import LlmAccessError
        from nemo_mcp_guardrails.llm_credentials import LlmCredentialError, resolve_llm_credential
        from nemo_mcp_guardrails.management_auth import create_access_token

        engine = create_engine("sqlite://", poolclass=StaticPool,
                               connect_args={"check_same_thread": False})
        for record in (UserRecord, LlmConfigRecord, AppRecord, AppLlmGrantRecord):
            record.__table__.create(engine)
        sessions = sessionmaker(bind=engine, expire_on_commit=False)
        with sessions.begin() as db:
            user = UserRecord(email="admin@example.invalid", name="Admin", username="admin",
                              password_hash="unused", enabled=True, system_role="admin")
            db.add(user)
            db.flush()
            admin = {"Authorization": "Bearer " + create_access_token(user)}
            db.add_all([LlmConfigRecord(id=value, name=f"Model {value}", provider="azure_openai",
                                       model_name="fake", endpoint=settings["AZURE_OPENAI_ENDPOINT"],
                                       credential_reference=f"env:APP_{label}_KEY", enabled=True)
                        for value, label in ((1, "A"), (2, "B"))])
            db.flush()
            db.add_all([AppRecord(id=value, name=label, client_id=label,
                                 api_key_hash=hash_api_key("fake-runtime-key"), authorized=True,
                                 main_llm_config_id=value, guardrail_llm_config_id=value)
                        for value, label in ((1, "a"), (2, "b"))])
            db.flush()
            db.add_all([AppLlmGrantRecord(app_id=value, purpose=purpose, llm_config_id=value, enabled=True)
                        for value in (1, 2) for purpose in ("main", "guardrail")])

        def test_db():
            """Keep runtime app and management JWT authentication backed by real rows."""
            with sessions() as db:
                yield db

        def change(model, condition, **values):
            """Commit a disposable state change independently of cached runtimes."""
            with sessions.begin() as db:
                db.execute(update(model).where(condition).values(**values))

        builds = []

        async def fake_builder(app_id, selection=None, policy_snapshot=None):
            """Record the exact granted selection used to construct each fake bundle."""
            builds.append((app_id, selection))
            return SimpleNamespace(
                rails=object(), agent=object(), output_rail_enabled=True,
                blocked_output_phrases=(), input_policy_count=0, input_policy_entries=(),
                blocked_tools=frozenset(), prompt_rule_config=SimpleNamespace(
                    input_rule_count=0, output_rule_count=0,
                ),
            )

        result = GuardedExecutionResult(
            "passed", "Safe response.", RailStatus.PASSED, RailStatus.PASSED,
            (), None, None, None, None, "fake",
        )
        app = FastAPI()
        app.include_router(runtime.router)
        app.include_router(app_llm_grants.router)
        app.dependency_overrides[get_db] = test_db
        check = TestCase()
        real_builder = factory._build_guardrails_runtime_parts_uncached
        factory.clear_guardrails_runtime_cache()
        with ExitStack() as stack:
            stack.enter_context(patch.object(factory, "SessionLocal", sessions))
            stack.enter_context(patch.object(factory, "load_runtime_policy_snapshot",
                side_effect=lambda app_id: factory.RuntimePolicySnapshot(app_id, ())))
            stack.enter_context(patch.object(factory, "load_runtime_revision", return_value=("unchanged",)))
            builder = stack.enter_context(patch.object(factory, "_build_guardrails_runtime_parts_uncached",
                                                       side_effect=fake_builder))
            execute = stack.enter_context(patch.object(runtime, "execute_guarded_message", AsyncMock(return_value=result)))
            store = stack.enter_context(patch.object(runtime, "_store_conversation_turns"))
            client = stack.enter_context(TestClient(app))

            def run(label="a", denied=False):
                """Verify failed setup reaches neither execution nor conversation storage."""
                before = (execute.await_count, store.call_count)
                response = client.post("/v1/guardrails/run", json={"message": "Review."}, headers={
                    "X-App-ID": label, "X-API-Key": "fake-runtime-key",
                })
                assert response.status_code == (503 if denied else 200), response.text
                assert "PRIVATE_" not in response.text and "credential_reference" not in response.text
                if denied:
                    assert (execute.await_count, store.call_count) == before
                return response

            assert client.get("/v1/guardrails/auth-check", headers={
                "X-App-ID": "a", "X-API-Key": "fake-runtime-key",
            }).status_code == 200
            run(); run()
            assert len(builds) == 1
            for purpose in ("main", "guardrail"):
                path = f"/apps/1/llm-grants/{purpose}/1"
                assert client.delete(path, headers=admin).status_code == 204
                before = len(builds)
                run(denied=True)
                assert len(builds) == before
                assert client.put(path, headers=admin, json={"enabled": True}).status_code == 200
                run()
            run("b")
            change(AppRecord, AppRecord.id == 1, main_llm_config_id=2)
            run(denied=True)
            run("b")
            change(AppRecord, AppRecord.id == 1, main_llm_config_id=None)
            run(denied=True)
            assert client.put("/apps/1/llm-grants/main/default", headers=admin,
                              json={"enabled": True}).status_code == 200
            run()
            change(AppRecord, AppRecord.id == 1, guardrail_llm_config_id=None)
            run(denied=True)
            assert client.put("/apps/1/llm-grants/guardrail/default", headers=admin,
                              json={"enabled": True}).status_code == 200
            run()
            change(AppRecord, AppRecord.id == 1, main_llm_config_id=1, guardrail_llm_config_id=1)
            run()
            before = len(builds)
            change(LlmConfigRecord, LlmConfigRecord.id == 1, model_name="changed")
            run()
            assert len(builds) == before + 1 and builds[-1][1].main_llm_config.model_name == "changed"
            for values in ({"enabled": False}, {"credential_reference": "env:GMS_JWT_SECRET"},
                           {"endpoint": "https://unapproved.invalid"}, {"provider": "gemini"}):
                with sessions() as db:
                    previous = {key: getattr(db.get(LlmConfigRecord, 1), key) for key in values}
                change(LlmConfigRecord, LlmConfigRecord.id == 1, **values)
                run(denied=True)
                change(LlmConfigRecord, LlmConfigRecord.id == 1, **previous)
            with patch.object(factory, "require_llm_grant", side_effect=SQLAlchemyError("PRIVATE_DB")):
                run(denied=True)
            run()
            with patch.dict(os.environ, {"GMS_ALLOWED_LLM_CREDENTIAL_ENV_VARS": "INVALID NAME"}):
                run(denied=True)
            with patch.dict(os.environ, {"NEMO_RUNTIME_CACHE_TTL_SECONDS": "0"}):
                before = len(builds)
                run(); run()
                assert len(builds) == before + 2
                assert client.delete("/apps/1/llm-grants/main/1", headers=admin).status_code == 204
                run(denied=True)
                assert client.put("/apps/1/llm-grants/main/1", headers=admin,
                                  json={"enabled": True}).status_code == 200

            with ExitStack() as attempt:
                attempt.enter_context(patch.object(factory, "_build_guardrails_runtime_parts_uncached", real_builder))
                attempt.enter_context(patch.object(factory, "load_app_connector_config",
                                                  return_value=SimpleNamespace(credential_reference=None)))
                attempt.enter_context(patch.object(factory, "build_rails_config_with_prompt_rules", return_value=()))
                model = attempt.enter_context(patch.object(factory, "build_chat_model"))
                tools = attempt.enter_context(patch.object(factory, "build_guarded_github_tools", AsyncMock()))
                attempt.enter_context(patch.dict(os.environ, {"AZURE_OPENAI_API_KEY": ""}))
                factory.clear_guardrails_runtime_cache()
                run(denied=True)
                model.assert_not_called()
                tools.assert_not_awaited()

            async def races():
                """Recheck grants after lock waits and reject changed in-flight builds."""
                factory.clear_guardrails_runtime_cache()
                lock = asyncio.Lock()
                await lock.acquire()
                factory._RUNTIME_BUILD_LOCKS[1] = lock
                before = builder.call_count
                task = asyncio.create_task(factory.build_guardrails_runtime_parts(1))
                await asyncio.sleep(0)
                change(AppLlmGrantRecord, (AppLlmGrantRecord.app_id == 1) &
                       (AppLlmGrantRecord.purpose == "main") &
                       (AppLlmGrantRecord.llm_config_id == 1), enabled=False)
                lock.release()
                with check.assertRaises(LlmAccessError):
                    await task
                assert builder.call_count == before
                change(AppLlmGrantRecord, AppLlmGrantRecord.app_id == 1, enabled=True)
                for ttl in ("300", "0"):
                    factory.clear_guardrails_runtime_cache()
                    async def changing_builder(app_id, selection=None, policy_snapshot=None):
                        """Change valid model metadata while construction is in flight."""
                        change(LlmConfigRecord, LlmConfigRecord.id == 1,
                               model_name=selection.main_llm_config.model_name + "-changed")
                        return await fake_builder(app_id, selection)
                    with patch.dict(os.environ, {"NEMO_RUNTIME_CACHE_TTL_SECONDS": ttl}), patch.object(
                        factory, "_build_guardrails_runtime_parts_uncached", side_effect=changing_builder,
                    ), check.assertRaises(LlmAccessError):
                        await factory.build_guardrails_runtime_parts(1)
                    assert 1 not in factory._RUNTIME_PARTS_CACHE

            asyncio.run(races())
        environment = factory.RuntimeEnvironment(
            "PRIVATE_DEFAULT_KEY", settings["AZURE_OPENAI_ENDPOINT"], "fake", "fake", "PRIVATE_PAT", "1",
        )
        config = factory.RuntimeLlmConfig("Fake", "azure_openai", "fake", None, "env:APP_A_KEY", True)
        for purpose in ("main agent", "guardrail"):
            with patch.object(factory, "AzureChatOpenAI") as constructor, patch(
                "nemo_mcp_guardrails.llm_credentials.os.getenv", wraps=os.getenv,
            ) as reads:
                with check.assertRaises(LlmCredentialError):
                    factory.build_chat_model(environment, replace(config, credential_reference="env:GMS_JWT_SECRET"), purpose)
                assert all(call.args[0] != "GMS_JWT_SECRET" for call in reads.call_args_list)
                constructor.assert_not_called()
            with patch.dict(os.environ, {"APP_A_KEY": ""}), check.assertRaises(LlmCredentialError):
                factory.build_chat_model(environment, config, purpose)
            with patch.object(factory, "AzureChatOpenAI") as constructor:
                with patch.object(factory, "DefaultHttpxClient"), patch.object(factory, "DefaultAsyncHttpxClient"):
                    factory.build_chat_model(environment, config, purpose)
                    assert constructor.call_args.kwargs["api_key"] == "PRIVATE_A_KEY"
        assert resolve_llm_credential("env: APP_A_KEY ") == "PRIVATE_A_KEY"
        factory.clear_guardrails_runtime_cache()
        engine.dispose()
    print("Runtime LLM grant checks passed: real app/JWT authentication, live cache checks, purpose/default isolation, revocation, build races and approved credential lookups.")


if __name__ == "__main__":
    main()
