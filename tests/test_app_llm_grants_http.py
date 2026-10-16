"""Offline real-JWT checks for app-specific model grant administration."""

import json
import os
from unittest import TestCase
from unittest.mock import patch

from _bootstrap import bootstrap_src

bootstrap_src()


def main() -> None:
    """Exercise real persistence/RBAC without model clients or real credentials."""

    settings = {
        "PYTHON_DOTENV_DISABLED": "1", "DATABASE_URL": "sqlite://",
        "GMS_JWT_SECRET": "grant-api-test-secret-with-at-least-32-characters",
        "AZURE_OPENAI_ENDPOINT": "https://example.openai.azure.com",
        "GMS_ALLOWED_LLM_ENDPOINTS": "",
        "GMS_ALLOWED_LLM_CREDENTIAL_ENV_VARS": "APP_A_KEY,APP_B_KEY",
    }
    with patch.dict(os.environ, settings):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from sqlalchemy import create_engine, func, select
        from sqlalchemy.exc import SQLAlchemyError
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool
        from nemo_mcp_guardrails.api import app_llm_grants, apps, llm_configs
        from nemo_mcp_guardrails.database.connection import get_db
        from nemo_mcp_guardrails.database.models import (
            AppLlmGrantRecord, AppRecord, AppUserRecord, LlmConfigRecord, UserRecord,
        )
        from nemo_mcp_guardrails.llm_credentials import (
            LlmCredentialError, validate_llm_credential_reference,
        )
        from nemo_mcp_guardrails.management_auth import create_access_token
        import nemo_mcp_guardrails.management_audit as audit
        from migrate_app_llm_grants import inventory, seed_manifest

        engine = create_engine("sqlite://", poolclass=StaticPool,
                               connect_args={"check_same_thread": False})
        for record in (UserRecord, LlmConfigRecord, AppRecord, AppUserRecord, AppLlmGrantRecord):
            record.__table__.create(engine)
        sessions = sessionmaker(bind=engine, expire_on_commit=False)
        headers = {}
        with sessions.begin() as db:
            users = {}
            for label in ("admin", "a", "owner", "b", "both", "outsider", "viewer"):
                user = UserRecord(email=f"{label}@example.invalid", name=label, username=label,
                                  password_hash="unused", enabled=True,
                                  system_role="admin" if label == "admin" else "developer")
                db.add(user)
                db.flush()
                users[label] = user
                headers[label] = {"Authorization": "Bearer " + create_access_token(user)}
            for config_id, values in enumerate((
                {"credential_reference": "env:APP_A_KEY"},
                {"credential_reference": "env:APP_B_KEY"}, {"enabled": False},
                {"credential_reference": "env:GMS_JWT_SECRET"},
                {"endpoint": "https://unapproved.invalid"}, {"provider": "gemini"},
            ), 1):
                fields = dict(name=f"Model {config_id}", provider="azure_openai", model_name="fake",
                              endpoint=settings["AZURE_OPENAI_ENDPOINT"], enabled=True)
                fields.update(values)
                db.add(LlmConfigRecord(id=config_id, **fields))
            db.flush()
            db.add_all([
                AppRecord(id=1, name="App A", client_id="a", api_key_hash="unused", authorized=True,
                          main_llm_config_id=1),
                AppRecord(id=2, name="App B", client_id="b", api_key_hash="unused", authorized=True,
                          main_llm_config_id=2),
            ])
            db.flush()
            for label, app_id, role in (("a", 1, "admin"), ("owner", 1, "owner"),
                                        ("b", 2, "admin"), ("both", 1, "admin"),
                                        ("both", 2, "admin"), ("viewer", 1, "viewer")):
                db.add(AppUserRecord(app_id=app_id, user_id=users[label].id, role=role))

        def test_db():
            """Override only database sessions; keep authentication and permissions real."""
            with sessions() as db:
                yield db

        def snapshot():
            """Detect partial app edits and unintended grant changes."""
            with sessions() as db:
                app = db.get(AppRecord, 1)
                grants = list(db.execute(select(
                    AppLlmGrantRecord.id, AppLlmGrantRecord.enabled,
                ).order_by(AppLlmGrantRecord.id)))
                return (app.name, app.client_id, app.main_llm_config_id,
                        app.guardrail_llm_config_id, app.authorized, grants)

        app = FastAPI()
        for router in (apps.router, app_llm_grants.router, llm_configs.router):
            app.include_router(router)
        app.dependency_overrides[get_db] = test_db
        app.add_middleware(audit.ManagementAuditMiddleware)
        audits = []
        check = TestCase()
        with patch.object(audit, "_persist_management_audit", side_effect=audits.append), TestClient(app) as client:
            def put_grant(prefix, purpose="main", ref="1", enabled=True):
                """Submit an explicit decision as an administrator without app membership."""
                return client.put(f"{prefix}/llm-grants/{purpose}/{ref}",
                                  headers=headers["admin"], json={"enabled": enabled})

            for prefix in ("/apps/1", "/apps/by-client-id/a"):
                assert client.get(prefix + "/llm-options?purpose=main").status_code == 401
                assert client.put(prefix + "/llm-grants/main/1", json={"enabled": True}).status_code == 401
                assert client.delete(prefix + "/llm-grants/main/1").status_code == 401
                for actor in ("outsider", "b", "viewer"):
                    assert client.get(prefix + "/llm-grants", headers=headers[actor]).status_code == 403
                for actor in ("a", "owner", "both"):
                    options = client.get(prefix + "/llm-options?purpose=main", headers=headers[actor])
                    assert options.json() == {"purpose": "main", "environment_default_allowed": False,
                                              "configs": []}
                    for enabled in (True, False, None):
                        denied = client.put(prefix + "/llm-grants/main/1", headers=headers[actor],
                                            json={"enabled": enabled})
                        assert denied.status_code == 403
                    assert client.delete(prefix + "/llm-grants/main/1",
                                         headers=headers[actor]).status_code == 403
            assert client.get("/llm-configs", headers=headers["a"]).status_code == 403
            assert len(client.get("/llm-configs", headers=headers["admin"]).json()) == 6
            original = snapshot()
            for actor in ("a", "owner", "both", "admin"):
                for field in ("main_llm_config_id", "guardrail_llm_config_id"):
                    for value in (1, 2, 999999, None):
                        result = client.put("/apps/1", headers=headers[actor],
                                            json={field: value, "name": "Must not change"})
                        assert result.status_code == 403, result.text
                        assert snapshot() == original
            rejected = client.post("/apps", headers=headers["admin"], json={
                "name": "Rejected", "client_id": "rejected", "main_llm_config_id": 1,
            })
            assert rejected.status_code == 400
            created = client.post("/apps", headers=headers["admin"],
                                  json={"name": "New app", "client_id": "new"})
            assert created.status_code == 201
            with sessions() as db:
                assert db.scalar(select(func.count()).select_from(AppLlmGrantRecord)) == 0
                manifest = inventory(db, app_ids={1})
                manifest.entries[0].enabled = True

            grant = put_grant("/apps/1")
            assert grant.status_code == 200, grant.text
            grant_id = grant.json()["id"]
            assert put_grant("/apps/by-client-id/a").json()["id"] == grant_id
            assert put_grant("/apps/2", ref="2").status_code == 200
            for prefix in ("/apps/1", "/apps/by-client-id/a"):
                choices = client.get(prefix + "/llm-options?purpose=main&app_id=2&client_id=b",
                                     headers=headers["both"]).json()
                assert [row["id"] for row in choices["configs"]] == [1]
                assert "credential_reference" not in json.dumps(choices)
            assert client.put("/apps/1", headers=headers["both"],
                              json={"main_llm_config_id": 2}).status_code == 403
            assert client.put("/apps/1", headers=headers["a"],
                              json={"main_llm_config_id": 1}).status_code == 200
            assert client.put("/apps/1", headers=headers["admin"],
                              json={"guardrail_llm_config_id": 1}).status_code == 403
            assert put_grant("/apps/1", purpose="guardrail").status_code == 200
            assert client.put("/apps/1", headers=headers["admin"],
                              json={"guardrail_llm_config_id": 1}).status_code == 200
            assert client.put("/apps/1", headers=headers["owner"],
                              json={"guardrail_llm_config_id": 1}).status_code == 403

            assert client.delete("/apps/by-client-id/a/llm-grants/main/1",
                                 headers=headers["admin"]).status_code == 204
            with sessions() as db:
                assert db.get(AppLlmGrantRecord, grant_id).enabled is False
                assert db.get(AppRecord, 1).main_llm_config_id == 1
                with check.assertRaisesRegex(ValueError, "Existing grants"):
                    seed_manifest(db, manifest, apply=True)
            assert client.put("/apps/1", headers=headers["admin"],
                              json={"main_llm_config_id": 1}).status_code == 403
            assert client.put("/apps/1", headers=headers["a"],
                              json={"name": "App A renamed"}).status_code == 200
            assert put_grant("/apps/1").json()["id"] == grant_id
            assert put_grant("/apps/1", ref="default").status_code == 200
            guardrail_options = client.get("/apps/1/llm-options?purpose=guardrail", headers=headers["a"]).json()
            assert guardrail_options["environment_default_allowed"] is False
            assert client.put("/apps/1", headers=headers["admin"],
                              json={"guardrail_llm_config_id": None}).status_code == 403
            assert put_grant("/apps/1", purpose="guardrail", ref="default").status_code == 200
            assert client.put("/apps/1", headers=headers["a"],
                              json={"main_llm_config_id": None}).status_code == 200
            for config_id in (3, 4, 5, 6):
                assert put_grant("/apps/1", ref=str(config_id)).status_code == 400
            with sessions.begin() as db:
                db.add_all([AppLlmGrantRecord(app_id=1, purpose="main", llm_config_id=value,
                                              enabled=True) for value in (3, 4, 5, 6)])
            choices = client.get("/apps/1/llm-options?purpose=main", headers=headers["a"]).json()
            assert [row["id"] for row in choices["configs"]] == [1]
            assert choices["environment_default_allowed"] is True
            for value in (3, 4, 5, 6):
                assert client.put("/apps/1", headers=headers["admin"],
                                  json={"main_llm_config_id": value}).status_code == 403
            with patch.dict(os.environ, {"GMS_ALLOWED_LLM_CREDENTIAL_ENV_VARS": "INVALID NAME"}):
                assert put_grant("/apps/1", ref="default").status_code == 400
                assert client.get("/apps/1/llm-options?purpose=main", headers=headers["a"]).json()["configs"] == []
                assert client.put("/apps/1", headers=headers["admin"],
                                  json={"main_llm_config_id": None}).status_code == 403
            original = snapshot()
            with patch.object(apps, "require_llm_grant", side_effect=SQLAlchemyError("PRIVATE_MARKER")):
                result = client.put("/apps/1", headers=headers["a"],
                                    json={"main_llm_config_id": 1, "name": "Must not change"})
                assert result.status_code == 503 and "PRIVATE_MARKER" not in result.text
            with patch.object(app_llm_grants, "_options", side_effect=SQLAlchemyError("PRIVATE_MARKER")):
                result = client.get("/apps/1/llm-options?purpose=main", headers=headers["a"])
                assert result.status_code == 503 and "PRIVATE_MARKER" not in result.text
            assert snapshot() == original
            for body in ({}, {"enabled": "true"}, {"enabled": None}, {"enabled": True, "extra": 1}):
                assert client.put("/apps/1/llm-grants/main/1", headers=headers["admin"],
                                  json=body).status_code == 422
            for reference in (None, "", "env:AZURE_OPENAI_API_KEY", " env: APP_A_KEY "):
                assert validate_llm_credential_reference(reference) in (None, "env:AZURE_OPENAI_API_KEY", "env:APP_A_KEY")
            with patch("nemo_mcp_guardrails.llm_credentials.os.getenv", wraps=os.getenv) as lookup:
                with check.assertRaises(LlmCredentialError):
                    validate_llm_credential_reference("env:GMS_JWT_SECRET")
                assert [call.args[0] for call in lookup.call_args_list] == ["GMS_ALLOWED_LLM_CREDENTIAL_ENV_VARS"]
            for reference in ("env:APP_A_KEY_OTHER", "env:", "vault:key", "env:INVALID NAME"):
                with check.assertRaises(LlmCredentialError):
                    validate_llm_credential_reference(reference)
            for reference in ("env:GMS_JWT_SECRET", "vault:key", "env:APP_A_KEY_OTHER"):
                result = client.post("/llm-configs", headers=headers["admin"], json={
                    "name": "Rejected credential", "model_name": "fake", "credential_reference": reference,
                })
                assert result.status_code == 400 and reference not in result.text
            result = client.post("/llm-configs", headers=headers["admin"], json={
                "name": "Approved reference", "model_name": "fake", "credential_reference": " env: APP_A_KEY ",
            })
            assert result.status_code == 201 and "credential_reference" not in result.json()
            with sessions() as db:
                assert db.get(LlmConfigRecord, result.json()["id"]).credential_reference == "env:APP_A_KEY"
            assert any(row["action"] == "app_llm_grant.updated" and row["outcome"] == "succeeded" for row in audits)
            assert any(row["action"] == "app_llm_grant.deleted" and row["outcome"] == "succeeded" for row in audits)
            assert any(row["entity_type"] == "app_llm_grant" and row["outcome"] == "rejected" for row in audits)
            audit_text = json.dumps(audits, default=str)
            assert "credential_reference" not in audit_text and "APP_A_KEY" not in audit_text
        engine.dispose()
    print("App LLM grant checks passed: real JWT/RBAC, app/purpose isolation, explicit defaults, revocation, provisioning, atomic rejection, and audit privacy. Runtime enforcement has a separate diagnostic.")


if __name__ == "__main__":
    main()
