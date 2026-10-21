"""Offline app-owned main-model registration, encryption and revocation checks."""

import asyncio
import json
import os
from dataclasses import replace
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import AsyncMock, patch

from _bootstrap import bootstrap_src
bootstrap_src()


def main() -> None:
    """Use real JWT/RBAC and disposable SQLite without provider/network calls."""
    from cryptography.fernet import Fernet
    settings = {
        "PYTHON_DOTENV_DISABLED": "1", "DATABASE_URL": "sqlite://",
        "GMS_JWT_SECRET": "app-owned-model-test-secret-at-least-32-characters",
        "GMS_MODEL_CREDENTIAL_ENCRYPTION_KEY": Fernet.generate_key().decode(),
        "GMS_ALLOWED_COMPATIBLE_LLM_ENDPOINTS": "https://a.invalid/v1,https://b.invalid/v1",
        "AZURE_OPENAI_ENDPOINT": "https://azure.invalid",
        "AZURE_OPENAI_API_KEY": "PRIVATE_CLASSIFIER_KEY", "AZURE_OPENAI_API_VERSION": "test",
        "AZURE_OPENAI_DEPLOYMENT": "classifier", "GITHUB_PERSONAL_ACCESS_TOKEN": "PRIVATE_PAT",
        "GMS_ALLOWED_LLM_ENDPOINTS": "", "GMS_ALLOWED_LLM_CREDENTIAL_ENV_VARS": "",
        "NEMO_POLICY_SOURCE": "database", "NEMO_RUNTIME_CACHE_TTL_SECONDS": "300",
    }
    with patch.dict(os.environ, settings):
        from fastapi import FastAPI
        from fastapi.exceptions import RequestValidationError
        from fastapi.testclient import TestClient
        from sqlalchemy import create_engine, func, select
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool
        from nemo_mcp_guardrails import runtime_factory as factory
        from nemo_mcp_guardrails.api import app_llm_grants, app_main_models, apps, llm_configs
        from nemo_mcp_guardrails.database.connection import get_db
        from nemo_mcp_guardrails.database.models import (
            AppLlmGrantRecord, AppRecord, AppUserRecord, LlmConfigRecord, UserRecord,
        )
        from nemo_mcp_guardrails.llm_access import LlmAccessError, require_llm_grant
        from nemo_mcp_guardrails.llm_credentials import LlmCredentialError
        from nemo_mcp_guardrails.management_auth import create_access_token
        from nemo_mcp_guardrails.model_credentials import decrypt_model_key
        from nemo_mcp_guardrails.request_limits import validation_error_response
        import nemo_mcp_guardrails.management_audit as audit
        import nemo_mcp_guardrails.rate_limits as rates
        from migrate_app_main_models import migrate

        engine = create_engine("sqlite://", poolclass=StaticPool,
                               connect_args={"check_same_thread": False})
        for record in (UserRecord, LlmConfigRecord, AppRecord, AppUserRecord, AppLlmGrantRecord):
            record.__table__.create(engine)
        sessions = sessionmaker(bind=engine, expire_on_commit=False)
        headers = {}
        with sessions.begin() as db:
            for label in ("admin", "a", "b", "both", "viewer", "outsider"):
                user = UserRecord(email=label + "@example.invalid", name=label, username=label,
                                  password_hash="unused", enabled=True,
                                  system_role="admin" if label == "admin" else "developer")
                db.add(user); db.flush()
                headers[label] = {"Authorization": "Bearer " + create_access_token(user)}
                if label in {"a", "b", "both", "viewer"}:
                    for app_id in ((1, 2) if label == "both" else (2,) if label == "b" else (1,)):
                        db.add(AppUserRecord(app_id=app_id, user_id=user.id,
                                             role="viewer" if label == "viewer" else "admin"))
            db.add_all([AppRecord(id=i, name="App " + str(i), client_id=label,
                                 api_key_hash="unused", authorized=True) for i, label in ((1, "a"), (2, "b"))])
            db.add_all([AppLlmGrantRecord(app_id=i, purpose="guardrail", llm_config_id=None,
                                          enabled=True) for i in (1, 2)])

        def test_db():
            """Keep real authentication and app membership checks on isolated rows."""
            with sessions() as db:
                yield db

        def counts():
            """Detect partial registration or rejected-request persistence."""
            with sessions() as db:
                return tuple(db.scalar(select(func.count()).select_from(model))
                             for model in (LlmConfigRecord, AppLlmGrantRecord))

        app = FastAPI()
        for router in (apps.router, app_llm_grants.router, app_main_models.router, llm_configs.router):
            app.include_router(router)
        app.dependency_overrides[get_db] = test_db
        app.add_exception_handler(RequestValidationError, validation_error_response)
        app.add_middleware(audit.ManagementAuditMiddleware)
        audits = []
        check = TestCase()
        payload = {"name": "Owned A", "provider": "openai_compatible", "model_name": "my-model",
                   "endpoint": "https://a.invalid/v1", "api_key": "PRIVATE_OWN_KEY"}
        with patch.object(audit, "_persist_management_audit", side_effect=audits.append), \
             patch.object(rates, "limiter", rates.RateLimiter()), TestClient(app) as client:
            for prefix in ("/apps/1", "/apps/by-client-id/a"):
                original = counts()
                assert client.post(prefix + "/main-models", json=payload).status_code == 401
                for actor in ("b", "viewer", "outsider"):
                    assert client.post(prefix + "/main-models", headers=headers[actor], json=payload).status_code == 403
                assert counts() == original
            created = client.post("/apps/1/main-models", headers=headers["a"], json=payload)
            assert created.status_code == 201, created.text
            assert created.headers["cache-control"] == "no-store"
            assert "PRIVATE_" not in created.text and "encrypted_api_key" not in created.text
            assert "credential_reference" not in created.text
            config_id = created.json()["id"]
            with sessions() as db:
                owned = db.get(LlmConfigRecord, config_id)
                assert owned.owner_app_id == 1 and owned.credential_reference is None
                assert "PRIVATE_" not in owned.encrypted_api_key
                assert decrypt_model_key(owned) == payload["api_key"]
                require_llm_grant(db, 1, "main", config_id)
                app_a = db.get(AppRecord, 1)
                assert app_a.main_llm_config_id is None and app_a.guardrail_llm_config_id is None
                assert db.scalar(select(func.count()).select_from(AppLlmGrantRecord).where(
                    AppLlmGrantRecord.llm_config_id == config_id)) == 1
            assert client.put("/apps/1", headers=headers["a"], json={"main_llm_config_id": config_id}).status_code == 200
            for prefix in ("/apps/1", "/apps/by-client-id/a"):
                assert config_id in [x["id"] for x in client.get(prefix + "/llm-options?purpose=main", headers=headers["a"]).json()["configs"]]
                assert not client.get(prefix + "/llm-options?purpose=guardrail", headers=headers["a"]).json()["configs"]
            for prefix in ("/apps/2", "/apps/by-client-id/b"):
                assert client.put(prefix + "/llm-grants/main/" + str(config_id), headers=headers["admin"], json={"enabled": True}).status_code == 400
                denied = client.put(prefix, headers=headers["both"], json={"main_llm_config_id": config_id})
                # App selection updates have only the numeric route; aliases reject PUT.
                assert denied.status_code == (405 if "by-client-id" in prefix else 403), denied.text
            for prefix in ("/apps/1", "/apps/by-client-id/a"):
                assert client.put(prefix + "/llm-grants/guardrail/" + str(config_id), headers=headers["admin"], json={"enabled": True}).status_code == 400
                denied = client.put(prefix, headers=headers["a"], json={"guardrail_llm_config_id": config_id})
                assert denied.status_code == (405 if "by-client-id" in prefix else 403), denied.text
            assert client.post("/llm-configs", headers=headers["a"], json=payload).status_code == 403
            original = counts()
            for fields in ({"credential_reference": "env:AZURE_OPENAI_API_KEY"}, {"owner_app_id": 2},
                           {"purpose": "guardrail"}, {"enabled": False}, {"api_key": ""},
                           {"api_key": "PRIVATE_OWN_KEY\n"}, {"provider": "native_vendor"}):
                result = client.post("/apps/1/main-models", headers=headers["a"], json={**payload, **fields})
                assert result.status_code == 422 and "PRIVATE_" not in result.text
            for destination in ("https://unapproved.invalid/v1", "http://169.254.169.254/v1", "https://a.invalid/v1?key=x"):
                result = client.post("/apps/1/main-models", headers=headers["a"], json={**payload, "endpoint": destination})
                assert result.status_code == 400 and "PRIVATE_" not in result.text
            assert client.post("/apps/1/main-models", headers=headers["a"], json=payload).status_code == 409
            assert counts() == original
            with patch.dict(os.environ, {"GMS_MODEL_CREDENTIAL_ENCRYPTION_KEY": ""}):
                assert client.post("/apps/1/main-models", headers=headers["a"], json={**payload, "name": "No key"}).status_code == 503
            assert counts() == original
            alias = client.post("/apps/by-client-id/a/main-models", headers=headers["a"],
                                json={**payload, "name": "Alias A", "model_name": "other-model", "api_key": "PRIVATE_OTHER_KEY"})
            assert alias.status_code == 201
            other_id = alias.json()["id"]
            assert "PRIVATE_" not in json.dumps(audits, default=str) and "encrypted_api_key" not in json.dumps(audits, default=str)
            assert any(x["action"] == "llm_config.created" and x["outcome"] == "succeeded" for x in audits)

            with sessions() as db:
                config = factory._to_runtime_llm_config(db.get(LlmConfigRecord, config_id))
                second = factory._to_runtime_llm_config(db.get(LlmConfigRecord, other_id))
            for changed in (replace(config, owner_app_id=2), replace(config, endpoint="https://b.invalid/v1"),
                            replace(config, model_name="other"), replace(config, encrypted_api_key=second.encrypted_api_key),
                            replace(config, encrypted_api_key=config.encrypted_api_key[:-4] + "xxxx")):
                with check.assertRaises(LlmCredentialError):
                    decrypt_model_key(changed)
            environment = factory.RuntimeEnvironment("PRIVATE_CLASSIFIER_KEY", "https://azure.invalid", "test", "classifier", "PRIVATE_PAT", "1")
            with patch.object(factory, "ChatOpenAI") as model:
                factory.build_chat_model(environment, config, "main agent")
                assert model.call_args.kwargs["api_key"] == "PRIVATE_OWN_KEY"
                with check.assertRaises(LlmAccessError):
                    factory.build_chat_model(environment, config, "guardrail")
            with patch.object(factory, "SessionLocal", sessions), \
                 patch.object(factory, "load_runtime_policy_snapshot", side_effect=lambda i: factory.RuntimePolicySnapshot(i, ())), \
                 patch.object(factory, "load_runtime_revision", return_value=()), \
                 patch.object(factory, "_build_guardrails_runtime_parts_uncached", AsyncMock(return_value=object())) as builder:
                factory.clear_guardrails_runtime_cache()
                asyncio.run(factory.build_guardrails_runtime_parts(1))
                asyncio.run(factory.build_guardrails_runtime_parts(1))
                assert builder.await_count == 1
                with patch.dict(os.environ, {"GMS_MODEL_CREDENTIAL_ENCRYPTION_KEY": Fernet.generate_key().decode()}):
                    asyncio.run(factory.build_guardrails_runtime_parts(1))
                    assert builder.await_count == 2
                    with check.assertRaises(LlmCredentialError):
                        decrypt_model_key(config)
                with sessions.begin() as db:
                    grant = db.scalar(select(AppLlmGrantRecord).where(AppLlmGrantRecord.app_id == 1,
                                      AppLlmGrantRecord.purpose == "main", AppLlmGrantRecord.llm_config_id == config_id))
                    grant.enabled = False
                with check.assertRaises(LlmAccessError):
                    asyncio.run(factory.build_guardrails_runtime_parts(1))
                factory.clear_guardrails_runtime_cache()
            with sessions.begin() as db:
                db.add_all([AppLlmGrantRecord(app_id=2, purpose="main", llm_config_id=config_id, enabled=True),
                            AppLlmGrantRecord(app_id=1, purpose="guardrail", llm_config_id=config_id, enabled=True)])
            with sessions() as db:
                for app_id, purpose in ((2, "main"), (1, "guardrail")):
                    with check.assertRaises(LlmAccessError):
                        require_llm_grant(db, app_id, purpose, config_id)
            assert not client.get("/apps/2/llm-options?purpose=main", headers=headers["b"]).json()["configs"]
            assert not client.get("/apps/1/llm-options?purpose=guardrail", headers=headers["a"]).json()["configs"]
            azure = client.post("/apps/1/main-models", headers=headers["a"], json={
                **payload, "name": "Owned Azure", "provider": "azure_openai",
                "endpoint": "https://azure.invalid", "api_key": "PRIVATE_AZURE_OWN_KEY",
            })
            assert azure.status_code == 201, azure.text
            with sessions() as db:
                azure_config = factory._to_runtime_llm_config(db.get(LlmConfigRecord, azure.json()["id"]))
            with patch.object(factory, "AzureChatOpenAI") as azure_model:
                factory.build_chat_model(environment, azure_config, "main agent")
                assert azure_model.call_args.kwargs["api_key"] == "PRIVATE_AZURE_OWN_KEY"
        fake = SimpleNamespace(scalar=lambda statement: "nemo_mcp_guardrails", execute=lambda statement: (_ for _ in ()).throw(AssertionError("DDL on wrong target")))
        with check.assertRaises(ValueError):
            migrate(fake, "nemo_mcp_guardrails")
        print("App-owned main-model registration, encryption, scope and cache checks passed.")


if __name__ == "__main__":
    main()
