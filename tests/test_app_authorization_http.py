"""Offline checks for administrator-controlled client-app authorization."""

import os
from unittest.mock import AsyncMock, patch

from _bootstrap import bootstrap_src

bootstrap_src()


def main() -> None:
    """Verify real JWT/RBAC and runtime revocation using disposable SQLite."""

    settings = {
        "PYTHON_DOTENV_DISABLED": "1", "DATABASE_URL": "sqlite://",
        "GMS_JWT_SECRET": "app-authorization-test-secret-at-least-32-characters",
    }
    with patch.dict(os.environ, settings):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool
        from nemo_mcp_guardrails.api import apps, runtime
        from nemo_mcp_guardrails.app_auth import hash_api_key
        from nemo_mcp_guardrails.database.connection import get_db
        from nemo_mcp_guardrails.database.models import (
            AppRecord, AppUserRecord, LlmConfigRecord, UserRecord,
        )
        from nemo_mcp_guardrails.management_auth import create_access_token

        engine = create_engine(
            "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False},
        )
        for record in (UserRecord, LlmConfigRecord, AppRecord, AppUserRecord):
            record.__table__.create(engine)
        sessions = sessionmaker(bind=engine, expire_on_commit=False)
        headers = {}
        api_key = "fake-app-authorization-test-key"
        with sessions.begin() as db:
            users = {}
            for label in ("admin", "app-admin", "app-owner", "unlinked"):
                user = UserRecord(
                    email=f"{label}@example.com", name=label, username=label,
                    password_hash="unused-test-hash", enabled=True,
                    system_role="admin" if label == "admin" else "developer",
                )
                db.add(user)
                db.flush()
                users[label] = user
                headers[label] = {"Authorization": "Bearer " + create_access_token(user)}
            record = AppRecord(name="Original app", client_id="original",
                               api_key_hash=hash_api_key(api_key), authorized=True)
            db.add(record)
            db.flush()
            app_id = record.id
            db.add_all([
                AppUserRecord(app_id=app_id, user_id=users["app-admin"].id, role="admin"),
                AppUserRecord(app_id=app_id, user_id=users["app-owner"].id, role="owner"),
            ])

        def test_db():
            """Use real persistence and permission queries without external services."""
            with sessions() as db:
                yield db

        def snapshot():
            """Observe the stored fields to detect partial rejected updates."""
            with sessions() as db:
                record = db.get(AppRecord, app_id)
                return (record.name, record.client_id, record.authorized,
                        record.main_llm_config_id, record.guardrail_llm_config_id,
                        record.api_key_hash, record.updated_at)

        app = FastAPI()
        app.include_router(apps.router)
        app.include_router(runtime.router)
        app.dependency_overrides[get_db] = test_db
        url = f"/apps/{app_id}"
        invalid_runtime = {"detail": "Invalid app credentials"}
        with TestClient(app) as client:
            def runtime_headers(client_id):
                """Supply the fixture app credentials, independently of management JWTs."""
                return {"X-App-ID": client_id, "X-API-Key": api_key}

            def reject_developer_authorization():
                """Reject protected fields before other validation or any mutation."""
                original = snapshot()
                for label in ("app-admin", "app-owner"):
                    for authorized in (True, False, None):
                        for payload in (
                            {"authorized": authorized},
                            {"authorized": authorized, "name": "Forbidden rename",
                             "client_id": "forbidden-rebind", "main_llm_config_id": 999999},
                        ):
                            response = client.put(url, headers=headers[label], json=payload)
                            assert response.status_code == 403, response.status_code
                            assert response.json() == {
                                "detail": "Only administrators can change app authorization",
                            }
                            assert snapshot() == original

            assert client.put(url, json={"authorized": True}).status_code == 401
            assert client.put(url, headers=headers["unlinked"],
                              json={"authorized": False}).status_code == 403
            assert client.put("/apps/by-client-id/original", headers=headers["app-admin"],
                              json={"authorized": False}).status_code == 405
            assert client.get("/v1/guardrails/auth-check",
                              headers=runtime_headers("original")).status_code == 200
            renamed = client.put(url, headers=headers["app-admin"], json={"name": "Developer edit"})
            assert renamed.status_code == 200
            assert renamed.json()["name"] == "Developer edit"
            assert renamed.json()["authorized"] is True
            guardrail = client.put(url, headers=headers["app-owner"],
                                  json={"guardrail_llm_config_id": None})
            assert guardrail.status_code == 403

            disabled = client.put(url, headers=headers["admin"], json={"authorized": False})
            assert disabled.status_code == 200
            assert disabled.json()["authorized"] is False
            reject_developer_authorization()
            assert client.get(url, headers=headers["app-admin"]).status_code == 200
            assert client.get("/apps/by-client-id/original",
                              headers=headers["app-owner"]).status_code == 200
            blocked = client.get("/v1/guardrails/auth-check", headers=runtime_headers("original"))
            assert blocked.status_code == 401
            assert blocked.json() == invalid_runtime
            with patch.object(runtime, "build_guardrails_runtime_parts", AsyncMock()) as builder:
                blocked = client.post("/v1/guardrails/run", headers=runtime_headers("original"),
                                      json={"message": "Review."})
                assert blocked.status_code == 401
                assert blocked.json() == invalid_runtime
                builder.assert_not_awaited()

            renamed = client.put(url, headers=headers["app-owner"],
                                 json={"name": "Disabled developer edit", "client_id": "renamed"})
            assert renamed.status_code == 200
            assert renamed.json()["authorized"] is False
            for client_id in ("original", "renamed"):
                blocked = client.get("/v1/guardrails/auth-check", headers=runtime_headers(client_id))
                assert blocked.status_code == 401
                assert blocked.json() == invalid_runtime

            enabled = client.put(url, headers=headers["admin"], json={"authorized": True})
            assert enabled.status_code == 200
            assert enabled.json()["authorized"] is True
            reject_developer_authorization()
            authenticated = client.get("/v1/guardrails/auth-check", headers=runtime_headers("renamed"))
            assert authenticated.status_code == 200
            assert authenticated.json()["app_id"] == app_id
            assert client.get("/v1/guardrails/auth-check",
                              headers=runtime_headers("original")).status_code == 401

        engine.dispose()
        print("App authorization checks passed (24 protected-field cases, RBAC, atomicity, and runtime revocation).")


if __name__ == "__main__":
    main()
