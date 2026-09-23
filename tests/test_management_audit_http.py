import os
from unittest.mock import patch

from _bootstrap import bootstrap_src

bootstrap_src()


def main() -> None:
    """Verify sanitized management audit capture and admin-only queries."""

    settings = {
        "PYTHON_DOTENV_DISABLED": "1",
        "DATABASE_URL": "sqlite://",
        "GMS_JWT_SECRET": "management-audit-test-secret-at-least-32-chars",
        "GMS_JWT_EXPIRY_MINUTES": "10",
    }
    with patch.dict(os.environ, settings):
        from fastapi import Depends, FastAPI, Response, status
        from fastapi.testclient import TestClient
        from sqlalchemy import create_engine, select
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool

        import nemo_mcp_guardrails.management_audit as audit_module
        from nemo_mcp_guardrails.api.audit_logs import router
        from nemo_mcp_guardrails.api.management_auth import (
            require_management_user,
        )
        from nemo_mcp_guardrails.database.connection import get_db
        from nemo_mcp_guardrails.database.models import (
            Base,
            ManagementAuditLogRecord,
            UserRecord,
        )
        from nemo_mcp_guardrails.management_audit import (
            ManagementAuditMiddleware,
            classify_management_action,
        )
        from nemo_mcp_guardrails.management_auth import create_access_token
        from nemo_mcp_guardrails.management_permissions import (
            require_system_admin,
        )
        from nemo_mcp_guardrails.performance import RequestTimingMiddleware

        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        sessions = sessionmaker(bind=engine, expire_on_commit=False)
        with engine.connect() as connection:
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        Base.metadata.create_all(
            engine,
            tables=[UserRecord.__table__, ManagementAuditLogRecord.__table__],
        )

        app = FastAPI()
        app.add_middleware(RequestTimingMiddleware)
        app.add_middleware(ManagementAuditMiddleware)
        app.include_router(router)

        def test_db():
            """Use the disposable database for endpoints and authentication."""

            with sessions() as db:
                yield db

        app.dependency_overrides[get_db] = test_db

        @app.put("/management-auth/me")
        def update_profile(
            payload: dict[str, str],
            user: UserRecord = Depends(require_management_user),
        ) -> dict[str, int]:
            return {"id": user.id}

        @app.post("/management-users", status_code=status.HTTP_201_CREATED)
        def create_user(
            payload: dict[str, str],
            user: UserRecord = Depends(require_system_admin),
        ) -> dict[str, int]:
            return {"id": user.id}

        @app.post("/v1/guardrails/run")
        def run_guardrails(payload: dict[str, str]) -> dict[str, str]:
            return {"status": "passed"}

        @app.patch("/policies/9")
        def fail_policy_update(
            user: UserRecord = Depends(require_system_admin),
        ) -> Response:
            return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        @app.get("/apps")
        def list_apps() -> list[object]:
            return []

        try:
            with sessions.begin() as db:
                admin = UserRecord(
                    email="admin@example.com",
                    name="Admin",
                    username="admin",
                    password_hash="not-used",
                    system_role="admin",
                    enabled=True,
                )
                developer = UserRecord(
                    email="developer@example.com",
                    name="Developer",
                    username="developer",
                    password_hash="not-used",
                    system_role="developer",
                    enabled=True,
                )
                db.add_all([admin, developer])
                db.flush()
                admin_header = {
                    "Authorization": f"Bearer {create_access_token(admin)}"
                }
                developer_header = {
                    "Authorization": f"Bearer {create_access_token(developer)}"
                }

            assert classify_management_action(
                "POST", "/apps/7/connectors"
            ) == ("app_connector.created", "app_connector")
            assert classify_management_action(
                "DELETE", "/apps/7/policy-assignments/8"
            ) == ("app_policy_assignment.deleted", "app_policy_assignment")
            assert classify_management_action(
                "POST", "/management-users/2/password"
            ) == ("user.password_reset", "user")
            assert classify_management_action(
                "POST", "/v1/guardrails/run"
            ) is None

            with patch.object(audit_module, "SessionLocal", sessions):
                with TestClient(app) as client:
                    secret = "must-never-appear-in-audit-storage"
                    response = client.put(
                        "/management-auth/me",
                        headers=admin_header,
                        json={"password": secret},
                    )
                    assert response.status_code == 200, response.text

                    response = client.post(
                        "/management-users",
                        headers=developer_header,
                        json={"temporary_password": secret},
                    )
                    assert response.status_code == 403, response.text

                    response = client.post(
                        "/management-users",
                        headers={"Authorization": "Bearer invalid-token"},
                        json={"temporary_password": secret},
                    )
                    assert response.status_code == 401, response.text

                    response = client.patch(
                        "/policies/9", headers=admin_header
                    )
                    assert response.status_code == 500, response.text

                    assert client.post(
                        "/v1/guardrails/run", json={"message": secret}
                    ).status_code == 200
                    assert client.get("/apps").status_code == 200

                    for credentials, expected in [
                        ({}, 401),
                        (developer_header, 403),
                    ]:
                        response = client.get(
                            "/audit-logs", headers=credentials
                        )
                        assert response.status_code == expected, response.text

                    response = client.get("/audit-logs", headers=admin_header)
                    assert response.status_code == 200, response.text
                    assert response.headers["cache-control"] == "no-store"
                    records = response.json()["items"]
                    assert len(records) == 4
                    assert {record["outcome"] for record in records} == {
                        "succeeded", "rejected", "failed"
                    }
                    assert {
                        (record["actor_email"], record["http_status"])
                        for record in records
                    } == {
                        ("admin@example.com", 200),
                        ("admin@example.com", 500),
                        ("developer@example.com", 403),
                        (None, 401),
                    }
                    assert secret not in response.text

                    succeeded = client.get(
                        "/audit-logs",
                        headers=admin_header,
                        params={"outcome": "succeeded"},
                    ).json()
                    assert len(succeeded["items"]) == 1
                    assert succeeded["items"][0]["action"] == "profile.updated"

                    users = client.get(
                        "/audit-logs",
                        headers=admin_header,
                        params={"entity_type": "user", "limit": 1},
                    ).json()
                    assert len(users["items"]) == 1
                    assert users["has_more"] is True
                    assert client.get(
                        "/audit-logs",
                        headers=admin_header,
                        params={"offset": 10001},
                    ).status_code == 422

            with sessions() as db:
                stored = list(db.scalars(select(ManagementAuditLogRecord)))
                assert len(stored) == 4
                assert all(secret not in row.target_path for row in stored)
                assert all(row.request_id for row in stored)
        finally:
            app.dependency_overrides.clear()
            engine.dispose()

    print("Management audit capture, sanitization and RBAC checks passed.")


if __name__ == "__main__":
    main()
