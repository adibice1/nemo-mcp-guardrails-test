import os
from uuid import uuid4

from _bootstrap import bootstrap_src

bootstrap_src()

from fastapi.testclient import TestClient
from sqlalchemy import select

from nemo_mcp_guardrails.api.main import app
from nemo_mcp_guardrails.app_auth import authenticate_app, verify_api_key
from nemo_mcp_guardrails.database.connection import SessionLocal
from nemo_mcp_guardrails.database.models import (
    AppPolicyAssignmentRecord,
    AppRecord,
    AppUserRecord,
    GlobalPolicyAssignmentRecord,
    PolicyRecord,
    UserRecord,
)
from nemo_mcp_guardrails.management_auth import create_access_token, hash_password


def _headers(user: UserRecord) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user)}"}


def main() -> None:
    """Verify app-developer boundaries and system-admin overrides."""

    os.environ["GMS_JWT_SECRET"] = "test-rbac-secret-with-at-least-32-characters"
    suffix = uuid4().hex
    users: list[UserRecord] = []
    created_app_id: int | None = None
    assigned_policy_id: int | None = None
    unassigned_policy_id: int | None = None

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

            developer_create_denied = client.post(
                "/apps",
                headers=_headers(developer_a),
                json={
                    "name": "Developer Created App",
                    "client_id": f"developer-created-{suffix}",
                    "authorized": True,
                    "main_llm_config_id": None,
                    "guardrail_llm_config_id": None,
                },
            )
            assert developer_create_denied.status_code == 403, developer_create_denied.text

            created = client.post(
                "/apps",
                headers=_headers(admin),
                json={
                    "name": "Creator-Owned App",
                    "client_id": f"creator-owned-{suffix}",
                    "authorized": True,
                    "main_llm_config_id": None,
                    "guardrail_llm_config_id": None,
                },
            )
            assert created.status_code == 201, created.text
            created_body = created.json()
            created_app_id = created_body["id"]
            created_api_key = created_body["api_key"]
            assert created_api_key.startswith("gms_")
            assert "not be shown again" in created_body["api_key_notice"]

            with SessionLocal() as db:
                db.add(
                    AppUserRecord(
                        app_id=created_app_id,
                        user_id=developer_a.id,
                        role="admin",
                    )
                )
                db.commit()
                links = list(
                    db.scalars(
                        select(AppUserRecord).where(
                            AppUserRecord.app_id == created_app_id
                        )
                    )
                )
                assert sorted((link.user_id, link.role) for link in links) == sorted(
                    [(admin.id, "admin"), (developer_a.id, "admin")]
                )
                stored_app = db.get(AppRecord, created_app_id)
                assert stored_app is not None
                assert verify_api_key(created_api_key, stored_app.api_key_hash)

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

            developer_update = client.put(
                f"/apps/{created_app_id}",
                headers=_headers(developer_a),
                json={"name": "Owner Updated App"},
            )
            assert developer_update.status_code == 200, developer_update.text

            regenerated = client.post(
                f"/apps/{created_app_id}/api-key",
                headers=_headers(developer_a),
            )
            assert regenerated.status_code == 200, regenerated.text
            regenerated_api_key = regenerated.json()["api_key"]
            assert regenerated_api_key.startswith("gms_")
            assert regenerated_api_key != created_api_key
            with SessionLocal() as db:
                assert (
                    authenticate_app(
                        db,
                        f"creator-owned-{suffix}",
                        created_api_key,
                    )
                    is None
                )
                assert (
                    authenticate_app(
                        db,
                        f"creator-owned-{suffix}",
                        regenerated_api_key,
                    )
                    is not None
                )

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

            assigned_policy = client.post(
                "/policies",
                headers=_headers(admin),
                json={
                    "policy_type": "input",
                    "connector": "github",
                    "action": "create",
                    "resource": "issue",
                    "effect": "block",
                    "conditions": {
                        "custom_resource": f'issue named "rbac-{suffix}"'
                    },
                    "enabled": True,
                },
            )
            assert assigned_policy.status_code == 201, assigned_policy.text
            assigned_policy_id = assigned_policy.json()["id"]

            assign_policy = client.post(
                f"/apps/{created_app_id}/policy-assignments",
                headers=_headers(developer_a),
                json={"policy_ids": [assigned_policy_id], "enabled": True},
            )
            assert assign_policy.status_code == 201, assign_policy.text

            developer_delete_policy = client.delete(
                f"/policies/{assigned_policy_id}",
                headers=_headers(developer_a),
            )
            assert developer_delete_policy.status_code == 403, developer_delete_policy.text

            blocked_admin_delete = client.delete(
                f"/policies/{assigned_policy_id}",
                headers=_headers(admin),
            )
            assert blocked_admin_delete.status_code == 409, blocked_admin_delete.text
            blocked_detail = blocked_admin_delete.json()["detail"]
            assert blocked_detail["code"] == "policy_still_assigned"
            assert blocked_detail["policy_id"] == assigned_policy_id
            assert blocked_detail["app_assignments"][0]["app_id"] == created_app_id

            unassigned_policy = client.post(
                "/policies",
                headers=_headers(admin),
                json={
                    "policy_type": "input",
                    "connector": "github",
                    "action": "create",
                    "resource": "issue",
                    "effect": "block",
                    "conditions": {
                        "custom_resource": f'issue named "delete-ok-{suffix}"'
                    },
                    "enabled": True,
                },
            )
            assert unassigned_policy.status_code == 201, unassigned_policy.text
            unassigned_policy_id = unassigned_policy.json()["id"]

            delete_unassigned = client.delete(
                f"/policies/{unassigned_policy_id}",
                headers=_headers(admin),
            )
            assert delete_unassigned.status_code == 204, delete_unassigned.text
            unassigned_policy_id = None

            admin_list = client.get("/apps", headers=_headers(admin))
            assert admin_list.status_code == 200, admin_list.text
            assert created_app_id in {item["id"] for item in admin_list.json()}
    finally:
        with SessionLocal() as db:
            for policy_id in (assigned_policy_id, unassigned_policy_id):
                if policy_id is None:
                    continue
                for assignment in list(
                    db.scalars(
                        select(AppPolicyAssignmentRecord).where(
                            AppPolicyAssignmentRecord.policy_id == policy_id
                        )
                    )
                ):
                    db.delete(assignment)
                for assignment in list(
                    db.scalars(
                        select(GlobalPolicyAssignmentRecord).where(
                            GlobalPolicyAssignmentRecord.policy_id == policy_id
                        )
                    )
                ):
                    db.delete(assignment)
                policy = db.get(PolicyRecord, policy_id)
                if policy is not None:
                    db.delete(policy)
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
    print("- New apps are admin-created and can be linked to developers.")
    print("- Developers see and manage only linked apps with app-developer roles.")
    print("- System admins can access all apps and admin-only controls.")


if __name__ == "__main__":
    main()
