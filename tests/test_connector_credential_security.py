"""Offline authorization and secret-destination checks for GitHub connectors."""

import os
from contextlib import ExitStack
from unittest.mock import AsyncMock, patch

from _bootstrap import bootstrap_src

bootstrap_src()


def main() -> None:
    """Use real JWT/RBAC and disposable SQLite without contacting GitHub or Azure."""

    settings = {
        "PYTHON_DOTENV_DISABLED": "1", "DATABASE_URL": "sqlite://",
        "GMS_JWT_SECRET": "connector-security-test-secret-at-least-32-characters",
        "AZURE_OPENAI_API_KEY": "fake-azure-key",
        "AZURE_OPENAI_ENDPOINT": "https://example.openai.azure.com",
        "AZURE_OPENAI_API_VERSION": "2024-12-01-preview",
        "AZURE_OPENAI_DEPLOYMENT": "fake-deployment",
        "GITHUB_PERSONAL_ACCESS_TOKEN": "PRIVATE_DEFAULT_PAT",
        "APP_A_GITHUB_PAT": "PRIVATE_APP_PAT", "APP_B_GITHUB_PAT": "PRIVATE_OTHER_PAT",
        "MISSING_GITHUB_PAT": "", "GITHUB_MCP_READ_ONLY": "1",
        "GMS_ALLOWED_GITHUB_CREDENTIAL_ENV_VARS": "APP_A_GITHUB_PAT,MISSING_GITHUB_PAT",
        "NEMO_RUNTIME_CACHE_TTL_SECONDS": "0", "NEMO_POLICY_SOURCE": "database",
    }
    with patch.dict(os.environ, settings):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from sqlalchemy import create_engine, select
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool
        from nemo_mcp_guardrails import connector_credentials as credentials
        from nemo_mcp_guardrails import runtime_factory as factory
        from nemo_mcp_guardrails.api import apps, runtime
        from nemo_mcp_guardrails.app_auth import hash_api_key
        from nemo_mcp_guardrails.database.connection import get_db
        from nemo_mcp_guardrails.database.models import (
            AppConnectorRecord, AppRecord, AppUserRecord, ConnectorRecord,
            LlmConfigRecord, UserRecord,
        )
        from nemo_mcp_guardrails.management_auth import create_access_token

        engine = create_engine(
            "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False},
        )
        for record in (UserRecord, LlmConfigRecord, AppRecord, AppUserRecord,
                       ConnectorRecord, AppConnectorRecord):
            record.__table__.create(engine)
        sessions = sessionmaker(bind=engine, expire_on_commit=False)
        headers = {}
        with sessions.begin() as db:
            users = {}
            for label in ("admin", "developer", "owner", "outsider"):
                user = UserRecord(
                    email=f"{label}@example.com", name=label, username=label,
                    password_hash="unused-test-hash", enabled=True,
                    system_role="admin" if label == "admin" else "developer",
                )
                db.add(user)
                db.flush()
                users[label] = user
                headers[label] = {"Authorization": "Bearer " + create_access_token(user)}
            app_record = AppRecord(name="App A", client_id="app-a",
                                   api_key_hash=hash_api_key("fake-runtime-key"), authorized=True)
            other_app = AppRecord(name="App B", client_id="app-b", api_key_hash="unused")
            connector = ConnectorRecord(name="github", display_name="GitHub", enabled=True)
            db.add_all([app_record, other_app, connector])
            db.flush()
            app_id, other_id, connector_id = app_record.id, other_app.id, connector.id
            db.add_all([
                AppUserRecord(app_id=app_id, user_id=users["developer"].id, role="admin"),
                AppUserRecord(app_id=app_id, user_id=users["owner"].id, role="owner"),
                AppConnectorRecord(app_id=app_id, connector_id=connector_id,
                                   credential_reference="env:APP_A_GITHUB_PAT", enabled=True),
            ])

        def test_db():
            """Provide independent sessions for real authentication and CRUD."""
            with sessions() as db:
                yield db

        def snapshot():
            """Detect insertion, deletion, reference changes, and partial updates."""
            with sessions() as db:
                return tuple((row.id, row.credential_reference, row.enabled, row.updated_at)
                             for row in db.scalars(select(AppConnectorRecord).where(
                                 AppConnectorRecord.app_id == app_id,
                             )))

        app = FastAPI()
        app.include_router(apps.router)
        app.include_router(runtime.router)
        app.dependency_overrides[get_db] = test_db
        bases = (f"/apps/{app_id}/connectors", "/apps/by-client-id/app-a/connectors")
        denied = 0
        with TestClient(app) as client:
            for base in bases:
                for label in ("developer", "owner"):
                    for reference in (None, "", "env:GITHUB_PERSONAL_ACCESS_TOKEN",
                                      "env:APP_A_GITHUB_PAT", "env:GMS_JWT_SECRET"):
                        for method, url in (("POST", base), ("PUT", base + "/github"),
                                            ("PUT", base + f"/{connector_id}")):
                            before = snapshot()
                            response = client.request(method, url, headers=headers[label], json={
                                "connector_name": "github", "credential_reference": reference,
                                "enabled": False,
                            })
                            assert response.status_code == 403, response.status_code
                            assert response.json() == {"detail": "Administrator access required"}
                            assert snapshot() == before
                            denied += 1
                assert client.put(base + "/github", json={"enabled": False}).status_code == 401
                assert client.put(base + "/github", headers=headers["outsider"],
                                  json={"enabled": False}).status_code == 403
                before = snapshot()
                for reference in ("env:GMS_JWT_SECRET", "env:APP_B_GITHUB_PAT",
                                  "env:", "env:APP_*", "vault:PRIVATE_MARKER"):
                    for method, url in (("POST", base), ("PUT", base + "/github")):
                        response = client.request(method, url, headers=headers["admin"], json={
                            "connector_name": "github", "credential_reference": reference,
                            "enabled": False,
                        })
                        assert response.status_code == 400, response.status_code
                        assert "PRIVATE_" not in response.text
                        assert snapshot() == before
                approved = client.put(base + "/github", headers=headers["admin"], json={
                    "credential_reference": "env: APP_A_GITHUB_PAT ",
                })
                assert approved.status_code == 200
                assert approved.json()["credential_reference"] == "env:APP_A_GITHUB_PAT"
                for cleared in (None, "  "):
                    response = client.put(base + "/github", headers=headers["admin"],
                                          json={"credential_reference": cleared})
                    assert response.status_code == 200
                    assert response.json()["credential_reference"] is None
                    assert client.put(base + "/github", headers=headers["admin"], json={
                        "credential_reference": "env:APP_A_GITHUB_PAT",
                    }).status_code == 200
                for label in ("admin", "developer", "owner"):
                    upsert = client.post(base, headers=headers[label], json={
                        "connector_id": connector_id, "enabled": True,
                    })
                    assert upsert.status_code == 201
                    assert upsert.json()["credential_reference"] == "env:APP_A_GITHUB_PAT"
                for reference in ("github", str(connector_id)):
                    toggled = client.put(base + "/" + reference, headers=headers["developer"],
                                         json={"enabled": False})
                    assert toggled.status_code == 200
                    assert toggled.json()["credential_reference"] == "env:APP_A_GITHUB_PAT"
                    assert toggled.json()["enabled"] is False
                    assert client.put(base + "/" + reference, headers=headers["owner"],
                                      json={"enabled": True}).status_code == 200

                assert client.delete(base + "/github", headers=headers["developer"]).status_code == 204
                assert snapshot() == ()
                for label in ("developer", "owner"):
                    response = client.post(base, headers=headers[label],
                                           json={"connector_name": "github"})
                    assert response.status_code == 403
                    assert snapshot() == ()
                response = client.post(base, headers=headers["admin"], json={
                    "connector_name": "github", "credential_reference": "env:GMS_JWT_SECRET",
                })
                assert response.status_code == 400
                assert snapshot() == ()
                response = client.post(base, headers=headers["admin"], json={"connector_name": "github"})
                assert response.status_code == 201
                assert response.json()["credential_reference"] is None
                response = client.put(base + "/github", headers=headers["admin"], json={
                    "credential_reference": "env:APP_A_GITHUB_PAT",
                })
                assert response.status_code == 200
            assert client.post(f"/apps/{other_id}/connectors", headers=headers["developer"],
                               json={"connector_name": "github"}).status_code == 403

            assert credentials.resolve_github_credential(None) == "PRIVATE_DEFAULT_PAT"
            assert credentials.resolve_github_credential("  ") == "PRIVATE_DEFAULT_PAT"
            assert credentials.resolve_github_credential("env: APP_A_GITHUB_PAT ") == "PRIVATE_APP_PAT"
            getenv = os.getenv
            with patch.object(credentials.os, "getenv", wraps=getenv) as reads:
                try:
                    credentials.resolve_github_credential("env:GMS_JWT_SECRET")
                except credentials.ConnectorCredentialError:
                    pass
                else:
                    raise AssertionError("Server JWT secret was resolved as a GitHub PAT")
                assert all(call.args[0] != "GMS_JWT_SECRET" for call in reads.call_args_list)
            with patch.dict(os.environ, {"GMS_ALLOWED_GITHUB_CREDENTIAL_ENV_VARS": "APP_*"}):
                for reference in (None, "env:APP_A_GITHUB_PAT"):
                    try:
                        credentials.resolve_github_credential(reference)
                    except credentials.ConnectorCredentialError:
                        pass
                    else:
                        raise AssertionError("Malformed backend approval did not fail closed")

            with ExitStack() as stack:
                stack.enter_context(patch.object(factory, "SessionLocal", sessions))
                stack.enter_context(patch.object(factory, "load_runtime_policy_snapshot",
                    side_effect=lambda app_id: factory.RuntimePolicySnapshot(app_id, ())))
                stack.enter_context(patch.object(factory, "load_runtime_llm_selection", return_value=object()))
                external = [stack.enter_context(patch.object(factory, name)) for name in (
                    "build_chat_model", "LLMRails", "create_agent",
                )]
                tools = stack.enter_context(patch.object(factory, "build_guarded_github_tools", AsyncMock()))
                execute = stack.enter_context(patch.object(runtime, "execute_guarded_message", AsyncMock()))
                for reference in ("env:GMS_JWT_SECRET", "env:APP_B_GITHUB_PAT",
                                  "vault:PRIVATE_MARKER", "env:MISSING_GITHUB_PAT", None):
                    with sessions.begin() as db:
                        link = db.scalar(select(AppConnectorRecord).where(
                            AppConnectorRecord.app_id == app_id,
                        ))
                        link.credential_reference = reference
                    with patch.dict(os.environ, {"GITHUB_PERSONAL_ACCESS_TOKEN": ""}
                                    if reference is None else {}):
                        response = client.post("/v1/guardrails/run", json={"message": "Review."},
                                               headers={"X-App-ID": "app-a", "X-API-Key": "fake-runtime-key"})
                    assert response.status_code == 503, response.status_code
                    assert response.json() == {"detail": (
                        "Runtime connector credentials are unavailable. Ask a GMS administrator to review the connector configuration."
                    )}
                    assert "PRIVATE_" not in response.text
                for boundary in external:
                    boundary.assert_not_called()
                tools.assert_not_awaited()
                execute.assert_not_awaited()
        engine.dispose()
        print(f"Connector security checks passed ({denied} protected-field cases, provisioning, omissions, legacy records, and runtime).")


if __name__ == "__main__":
    main()
