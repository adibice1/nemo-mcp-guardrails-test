import os
from uuid import uuid4

from _bootstrap import bootstrap_src

bootstrap_src()

from fastapi.testclient import TestClient
from sqlalchemy import select

from nemo_mcp_guardrails.api.main import app
from nemo_mcp_guardrails.database.connection import SessionLocal
from nemo_mcp_guardrails.database.models import AppRecord, AppUserRecord, UserRecord
from nemo_mcp_guardrails.management_auth import create_access_token, hash_password


def _headers(user: UserRecord) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user)}"}


def main() -> None:
    """Verify developer ownership boundaries and system-admin overrides."""

    os.environ["GMS_JWT_SECRET"] = "test-rbac-secret-with-at-least-32-characters"
    suffix = uuid4().hex
    users: list[UserRecord] = []
    created_app_id: int | None = None

    with SessionLocal() as db:
        for label, role in (
            ("developer-a", "developer"),
            ("developer-b", "developer"),
            ("admin", "admin"),
        ):
            email = f"{label}-{suffix}@example.com"
            user = UserRecord(
                email=email,
                name=label,
                username=email,
                password_hash=hash_password("test-password"),
                system_role=role,
                enabled=True,
            )
            db.add(user)
            users.append(user)
        db.commit()
        for user in users:
            db.refresh(user)

    developer_a, developer_b, admin = users

    try:
        with TestClient(app) as client:
            missing_auth = client.get("/apps")
            assert missing_auth.status_code == 401, missing_auth.text

            created = client.post(
                "/apps",
                headers=_headers(developer_a),
                json={
                    "name": "Creator-Owned App",
                    "client_id": f"creator-owned-{suffix}",
                    "api_key": "creator-owned-test-api-key",
                    "authorized": True,
                    "main_llm_config_id": None,
                    "guardrail_llm_config_id": None,
                },
            )
            assert created.status_code == 201, created.text
            created_app_id = created.json()["id"]

            with SessionLocal() as db:
                links = list(
                    db.scalars(
                        select(AppUserRecord).where(
                            AppUserRecord.app_id == created_app_id
                        )
                    )
                )
                assert [(link.user_id, link.role) for link in links] == [
                    (developer_a.id, "owner")
                ]

            list_a = client.get("/apps", headers=_headers(developer_a))
            assert list_a.status_code == 200, list_a.text
            assert created_app_id in {item["id"] for item in list_a.json()}

            list_b = client.get("/apps", headers=_headers(developer_b))
            assert list_b.status_code == 200, list_b.text
            assert created_app_id not in {item["id"] for item in list_b.json()}

            denied = client.get(
                f"/apps/{created_app_id}", headers=_headers(developer_b)
            )
            assert denied.status_code == 403, denied.text

            owner_update = client.put(
                f"/apps/{created_app_id}",
                headers=_headers(developer_a),
                json={"name": "Owner Updated App"},
            )
            assert owner_update.status_code == 200, owner_update.text

            guardrail_denied = client.put(
                f"/apps/{created_app_id}",
                headers=_headers(developer_a),
                json={"guardrail_llm_config_id": None},
            )
            assert guardrail_denied.status_code == 403, guardrail_denied.text

            admin_update = client.put(
                f"/apps/{created_app_id}",
                headers=_headers(admin),
                json={"guardrail_llm_config_id": None},
            )
            assert admin_update.status_code == 200, admin_update.text

            global_denied = client.post(
                "/global-policy-assignments",
                headers=_headers(developer_a),
                json={"policy_ids": [999999], "enabled": True},
            )
            assert global_denied.status_code == 403, global_denied.text

            global_admin = client.post(
                "/global-policy-assignments",
                headers=_headers(admin),
                json={"policy_ids": [999999], "enabled": True},
            )
            assert global_admin.status_code == 404, global_admin.text

            admin_list = client.get("/apps", headers=_headers(admin))
            assert admin_list.status_code == 200, admin_list.text
            assert created_app_id in {item["id"] for item in admin_list.json()}
    finally:
        with SessionLocal() as db:
            if created_app_id is not None:
                created_app = db.get(AppRecord, created_app_id)
                if created_app is not None:
                    db.delete(created_app)
            for user in users:
                persisted = db.get(UserRecord, user.id)
                if persisted is not None:
                    db.delete(persisted)
            db.commit()

    print("Management RBAC HTTP checks passed.")
    print("- New apps are linked only to their creator as owner.")
    print("- Developers see and manage only linked apps.")
    print("- System admins can access all apps and admin-only controls.")


if __name__ == "__main__":
    main()
