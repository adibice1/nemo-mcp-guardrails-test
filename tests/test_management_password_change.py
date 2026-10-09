"""Isolated password-change, session-revocation, and audit regressions."""

import os
from unittest.mock import patch

from _bootstrap import bootstrap_src

bootstrap_src()


def main() -> None:
    """Verify both roles and negative API cases without a real database."""

    settings = {
        "PYTHON_DOTENV_DISABLED": "1",
        "DATABASE_URL": "sqlite://",
        "GMS_JWT_SECRET": "password-change-test-secret-at-least-32-characters",
    }
    with patch.dict(os.environ, settings):
        import jwt
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from sqlalchemy import create_engine, select
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool
        from nemo_mcp_guardrails.api.management_auth import router
        from nemo_mcp_guardrails.api.management_users import router as users_router
        from nemo_mcp_guardrails.database.connection import get_db
        from nemo_mcp_guardrails.database.models import UserRecord
        from nemo_mcp_guardrails.management_auth import hash_password, verify_password
        from nemo_mcp_guardrails.management_audit import ManagementAuditMiddleware

        engine = create_engine("sqlite://", poolclass=StaticPool,
                               connect_args={"check_same_thread": False})
        UserRecord.__table__.create(engine)
        sessions = sessionmaker(bind=engine, expire_on_commit=False)
        original_password = "original memorable passphrase"
        with sessions.begin() as db:
            for role in ("admin", "developer"):
                db.add(UserRecord(email=f"{role}@example.com", name=role, username=role,
                                  password_hash=hash_password(original_password),
                                  system_role=role, enabled=True))

        def test_db():
            """Supply independent sessions from the disposable SQLite database."""
            with sessions() as db:
                yield db

        app = FastAPI()
        app.include_router(router)
        app.include_router(users_router)
        app.dependency_overrides[get_db] = test_db
        app.add_middleware(ManagementAuditMiddleware)
        audit = []
        with patch("nemo_mcp_guardrails.management_audit._persist_management_audit",
                   side_effect=lambda values: audit.append(values)), TestClient(app) as client:
            def login(role, password):
                """Authenticate through the real endpoint and return bearer headers."""
                response = client.post("/management-auth/login",
                                       json={"email": f"{role}@example.com", "password": password})
                assert response.status_code == 200, response.status_code
                return {"Authorization": "Bearer " + response.json()["access_token"]}

            payload = {"current_password": original_password,
                       "new_password": "my new memorable passphrase"}
            assert client.put("/management-auth/me/password", json=payload).status_code == 401
            admin_headers = login("admin", original_password)
            for role in ("developer", "admin"):
                headers = login(role, original_password)
                for invalid in (
                    {**payload, "current_password": "incorrect"},
                    {**payload, "new_password": original_password},
                    {**payload, "new_password": " " * 15},
                ):
                    assert client.put("/management-auth/me/password", json=invalid,
                                      headers=headers).status_code == 400
                for invalid in (
                    {**payload, "new_password": "short"},
                    {**payload, "new_password": "x" * 257},
                    {**payload, "new_password": 123},
                    {**payload, "user_id": 999},
                ):
                    assert client.put("/management-auth/me/password", json=invalid,
                                      headers=headers).status_code == 422
                token = headers["Authorization"].removeprefix("Bearer ")
                claims = jwt.decode(token, settings["GMS_JWT_SECRET"], algorithms=["HS256"])
                claims.pop("pwdv")
                legacy = jwt.encode(claims, settings["GMS_JWT_SECRET"], algorithm="HS256")
                assert client.get("/management-auth/me",
                                  headers={"Authorization": "Bearer " + legacy}).status_code == 401
                response = client.put("/management-auth/me/password", json=payload, headers=headers)
                assert response.status_code == 204 and not response.content
                assert response.headers["cache-control"] == "no-store"
                assert client.get("/management-auth/me", headers=headers).status_code == 401
                assert client.post("/management-auth/login",
                    json={"email": f"{role}@example.com", "password": original_password}).status_code == 401
                updated_headers = login(role, payload["new_password"])
                assert client.get("/management-auth/me", headers=updated_headers).status_code == 200
                with sessions() as db:
                    user = db.scalar(select(UserRecord).where(UserRecord.username == role))
                    assert verify_password(payload["new_password"], user.password_hash)
                    assert user.password_hash != payload["new_password"]
                if role == "developer":
                    assert client.get("/management-auth/me", headers=admin_headers).status_code == 200

            admin_headers = login("admin", payload["new_password"])
            developer_headers = login("developer", payload["new_password"])
            with sessions() as db:
                developer = db.scalar(select(UserRecord).where(UserRecord.username == "developer"))
                developer_id = developer.id
            response = client.post(f"/management-users/{developer_id}/password", headers=admin_headers)
            assert response.status_code == 200
            reset_password = response.json()["temporary_password"]
            assert client.get("/management-auth/me", headers=developer_headers).status_code == 401
            login("developer", reset_password)
            assert any(row["action"] == "user.password_changed" and row["outcome"] == "succeeded"
                       for row in audit)
            assert any(row["action"] == "user.password_changed" and row["outcome"] == "rejected"
                       for row in audit)
            for row in audit:
                assert original_password not in repr(row)
                assert payload["new_password"] not in repr(row)
                assert reset_password not in repr(row)

        engine.dispose()
    print("Password-change checks passed: both roles, validation, isolation, old-session rejection, reset, and audit.")


if __name__ == "__main__":
    main()
