import os
from uuid import uuid4

from _bootstrap import bootstrap_src

bootstrap_src()

from fastapi.testclient import TestClient
from sqlalchemy import select

from migrate_management_auth import migrate_management_auth_schema
from nemo_mcp_guardrails.api.main import app
from nemo_mcp_guardrails.app_auth import hash_api_key
from nemo_mcp_guardrails.database.connection import SessionLocal
from nemo_mcp_guardrails.database.models import (
    AppRecord,
    AppUserRecord,
    UserRecord,
)
from nemo_mcp_guardrails.management_auth import create_access_token, hash_password


def _headers(user: UserRecord) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user)}"}


def main() -> None:
    """Verify admin-managed user creation and user/app linking."""

    os.environ["GMS_JWT_SECRET"] = "test-management-users-secret-with-32-characters"
    os.environ["GMS_JWT_EXPIRY_MINUTES"] = "60"
    migrate_management_auth_schema()

    suffix = uuid4().hex
    created_user_id: int | None = None
    app_id: int | None = None
    admin_id: int | None = None
    developer_id: int | None = None
    created_email = f"managed-{suffix}@example.com"

    with SessionLocal() as db:
        admin = UserRecord(
            email=f"admin-{suffix}@example.com",
            name="Admin User",
            username=f"admin-{suffix}",
            password_hash=hash_password("admin-password"),
            system_role="admin",
            enabled=True,
        )
        developer = UserRecord(
            email=f"developer-{suffix}@example.com",
            name="Developer User",
            username=f"developer-{suffix}",
            password_hash=hash_password("developer-password"),
            system_role="developer",
            enabled=True,
        )
        app_record = AppRecord(
            name="Managed User Test App",
            client_id=f"managed-user-test-{suffix}",
            api_key_hash=hash_api_key("not-used-in-this-test"),
            authorized=True,
        )
        db.add_all([admin, developer, app_record])
        db.commit()
        db.refresh(admin)
        db.refresh(developer)
        db.refresh(app_record)
        admin_id = admin.id
        developer_id = developer.id
        app_id = app_record.id

    try:
        with SessionLocal() as db:
            admin = db.get(UserRecord, admin_id)
            developer = db.get(UserRecord, developer_id)
            assert admin is not None
            assert developer is not None

            with TestClient(app) as client:
                denied = client.get("/management-users", headers=_headers(developer))
                assert denied.status_code == 403, denied.text

                created = client.post(
                    "/management-users",
                    headers=_headers(admin),
                    json={
                        "email": created_email.upper(),
                        "name": "Managed Developer",
                        "username": f"managed-{suffix}",
                        "system_role": "developer",
                        "enabled": True,
                    },
                )
                assert created.status_code == 201, created.text
                created_body = created.json()
                created_user_id = created_body["id"]
                temporary_password = created_body["temporary_password"]
                assert created_body["email"] == created_email
                assert "not be shown again" in created_body["temporary_password_notice"]

                login = client.post(
                    "/management-auth/login",
                    json={"email": created_email, "password": temporary_password},
                )
                assert login.status_code == 200, login.text

                updated = client.put(
                    f"/management-users/{created_user_id}",
                    headers=_headers(admin),
                    json={"enabled": False},
                )
                assert updated.status_code == 200, updated.text
                assert updated.json()["enabled"] is False

                disabled_login = client.post(
                    "/management-auth/login",
                    json={"email": created_email, "password": temporary_password},
                )
                assert disabled_login.status_code == 401, disabled_login.text

                reenabled = client.put(
                    f"/management-users/{created_user_id}",
                    headers=_headers(admin),
                    json={"enabled": True, "system_role": "developer"},
                )
                assert reenabled.status_code == 200, reenabled.text

                reset = client.post(
                    f"/management-users/{created_user_id}/password",
                    headers=_headers(admin),
                )
                assert reset.status_code == 200, reset.text
                reset_password = reset.json()["temporary_password"]
                assert reset_password != temporary_password

                old_password = client.post(
                    "/management-auth/login",
                    json={"email": created_email, "password": temporary_password},
                )
                assert old_password.status_code == 401, old_password.text

                new_password = client.post(
                    "/management-auth/login",
                    json={"email": created_email, "password": reset_password},
                )
                assert new_password.status_code == 200, new_password.text

                linked = client.post(
                    f"/management-users/{created_user_id}/apps",
                    headers=_headers(admin),
                    json={"app_id": app_id, "role": "admin"},
                )
                assert linked.status_code == 201, linked.text
                assert linked.json()["app_id"] == app_id
                assert linked.json()["role"] == "admin"

                relinked = client.post(
                    f"/management-users/{created_user_id}/apps",
                    headers=_headers(admin),
                    json={"app_id": app_id, "role": "admin"},
                )
                assert relinked.status_code == 201, relinked.text
                assert relinked.json()["role"] == "admin"

                viewer_rejected = client.post(
                    f"/management-users/{created_user_id}/apps",
                    headers=_headers(admin),
                    json={"app_id": app_id, "role": "viewer"},
                )
                assert viewer_rejected.status_code == 422, viewer_rejected.text

                links = client.get(
                    f"/management-users/{created_user_id}/apps",
                    headers=_headers(admin),
                )
                assert links.status_code == 200, links.text
                assert [link["app_id"] for link in links.json()] == [app_id]

                unlinked = client.delete(
                    f"/management-users/{created_user_id}/apps/{app_id}",
                    headers=_headers(admin),
                )
                assert unlinked.status_code == 204, unlinked.text
    finally:
        with SessionLocal() as db:
            if created_user_id is not None:
                for link in list(
                    db.scalars(
                        select(AppUserRecord).where(
                            AppUserRecord.user_id == created_user_id
                        )
                    )
                ):
                    db.delete(link)
                created_user = db.get(UserRecord, created_user_id)
                if created_user is not None:
                    db.delete(created_user)
            if app_id is not None:
                app_record = db.get(AppRecord, app_id)
                if app_record is not None:
                    db.delete(app_record)
            for user_id in (admin_id, developer_id):
                if user_id is None:
                    continue
                user = db.get(UserRecord, user_id)
                if user is not None:
                    db.delete(user)
            db.commit()

    print("Management user HTTP checks passed.")
    print("- Only system admins can use /management-users.")
    print("- Admin-created users receive one-time temporary passwords.")
    print("- Admins can reset passwords and link users to apps.")


if __name__ == "__main__":
    main()
