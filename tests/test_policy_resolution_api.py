from uuid import uuid4

from _bootstrap import bootstrap_src

bootstrap_src()

from fastapi.testclient import TestClient
from sqlalchemy import select

from nemo_mcp_guardrails.api.main import app
from nemo_mcp_guardrails.app_auth import hash_api_key
from nemo_mcp_guardrails.database.connection import SessionLocal
from nemo_mcp_guardrails.database.models import (
    AppPolicyAssignmentRecord,
    AppRecord,
    PolicyRecord,
)


TEMP_API_KEY = "temporary-resolution-api-key"


def create_temporary_apps(suffix: str) -> tuple[int, str, int, str]:
    """Create two temporary apps for policy-resolution checks."""

    client_a = f"resolution-app-a-{suffix}"
    client_b = f"resolution-app-b-{suffix}"
    with SessionLocal() as db:
        app_a = AppRecord(
            name=f"Resolution App A {suffix}",
            client_id=client_a,
            api_key_hash=hash_api_key(TEMP_API_KEY),
            authorized=True,
        )
        app_b = AppRecord(
            name=f"Resolution App B {suffix}",
            client_id=client_b,
            api_key_hash=hash_api_key(TEMP_API_KEY),
            authorized=True,
        )
        db.add_all([app_a, app_b])
        db.commit()
        db.refresh(app_a)
        db.refresh(app_b)
        return app_a.id, client_a, app_b.id, client_b


def cleanup_records(app_ids: list[int], condition_value: str) -> None:
    """Delete temporary apps and policies created by this test."""

    with SessionLocal() as db:
        for app_id in app_ids:
            app_record = db.get(AppRecord, app_id)
            if app_record is not None:
                db.delete(app_record)

        policies = list(
            db.scalars(
                select(PolicyRecord).where(
                    PolicyRecord.conditions["custom_resource"].astext
                    .like(f"{condition_value}%")
                )
            )
        )
        for policy in policies:
            db.delete(policy)
        db.commit()


def count_policy_assignments(app_id: int, policy_id: int) -> int:
    """Count one app's assignments for a reusable policy."""

    with SessionLocal() as db:
        return len(
            list(
                db.scalars(
                    select(AppPolicyAssignmentRecord).where(
                        AppPolicyAssignmentRecord.app_id == app_id,
                        AppPolicyAssignmentRecord.policy_id == policy_id,
                    )
                )
            )
        )


def main() -> None:
    """Verify equivalent policies are reused and app deletion only unassigns."""

    suffix = uuid4().hex
    condition_value = f"resolution-test-{suffix}"
    app_a_id, client_a, app_b_id, client_b = create_temporary_apps(suffix)
    payload = {
        "display_name": "App A issue policy",
        "policy": {
            "policy_type": "input",
            "connector": "github",
            "action": "create",
            "resource": "issue",
            "description": "Resolution policy created by App A",
            "effect": "block",
            "priority": 100,
            "conditions": {"custom_resource": condition_value},
            "enabled": True,
        }
    }

    try:
        with TestClient(app) as client:
            first = client.post(
                f"/apps/by-client-id/{client_a}/policy-assignments/resolve",
                json=payload,
            )
            assert first.status_code == 200, first.text
            first_body = first.json()
            assert first_body["resolution"] == "created"
            assert first_body["scope"] == "app"
            assert first_body["display_name"] == "App A issue policy"
            policy_id = first_body["policy_id"]
            app_a_assignment_id = first_body["assignment_id"]

            duplicate = client.post(
                f"/apps/by-client-id/{client_a}/policy-assignments/resolve",
                json={
                    "display_name": "Duplicate name",
                    "policy": {
                        **payload["policy"],
                        "description": "Different name, equivalent behavior",
                    }
                },
            )
            assert duplicate.status_code == 200, duplicate.text
            assert duplicate.json()["resolution"] == "already_assigned"
            assert duplicate.json()["policy_id"] == policy_id
            assert duplicate.json()["assignment_id"] == app_a_assignment_id

            reused = client.post(
                f"/apps/by-client-id/{client_b}/policy-assignments/resolve",
                json={
                    "display_name": "App B issue policy",
                    "policy": {
                        **payload["policy"],
                        "description": "App B requests the same behavior",
                    }
                },
            )
            assert reused.status_code == 200, reused.text
            assert reused.json()["resolution"] == "reused"
            assert reused.json()["policy_id"] == policy_id
            assert reused.json()["display_name"] == "App B issue policy"
            assert count_policy_assignments(app_b_id, policy_id) == 1

            target_payload = {
                "display_name": "App B target policy",
                "policy": {
                    **payload["policy"],
                    "description": "Existing target policy",
                    "conditions": {
                        "custom_resource": f"{condition_value}-target"
                    },
                },
            }
            target = client.post(
                f"/apps/by-client-id/{client_b}/policy-assignments/resolve",
                json=target_payload,
            )
            assert target.status_code == 200, target.text
            target_policy_id = target.json()["policy_id"]

            edit_to_existing = client.put(
                f"/apps/by-client-id/{client_a}/policy-assignments/"
                f"{app_a_assignment_id}/resolve",
                json={**target_payload, "display_name": "App A switched policy"},
            )
            assert edit_to_existing.status_code == 200, edit_to_existing.text
            assert edit_to_existing.json()["resolution"] == "reused"
            assert edit_to_existing.json()["policy_id"] == target_policy_id
            assert edit_to_existing.json()["display_name"] == "App A switched policy"
            assert count_policy_assignments(app_a_id, policy_id) == 0
            assert count_policy_assignments(app_b_id, policy_id) == 1

            new_payload = {
                "display_name": "App A new behavior",
                "policy": {
                    **payload["policy"],
                    "description": "New edited behavior",
                    "conditions": {
                        "custom_resource": f"{condition_value}-new"
                    },
                },
            }
            edit_to_new = client.put(
                f"/apps/by-client-id/{client_a}/policy-assignments/"
                f"{app_a_assignment_id}/resolve",
                json=new_payload,
            )
            assert edit_to_new.status_code == 200, edit_to_new.text
            assert edit_to_new.json()["resolution"] == "created"
            assert edit_to_new.json()["display_name"] == "App A new behavior"
            app_a_new_policy_id = edit_to_new.json()["policy_id"]
            assert app_a_new_policy_id not in {policy_id, target_policy_id}

            rename_only = client.put(
                f"/apps/by-client-id/{client_a}/policy-assignments/"
                f"{app_a_assignment_id}/resolve",
                json={**new_payload, "display_name": "Renamed App A policy"},
            )
            assert rename_only.status_code == 200, rename_only.text
            assert rename_only.json()["resolution"] == "already_assigned"
            assert rename_only.json()["display_name"] == "Renamed App A policy"

            direct_duplicate = client.post(
                "/policies",
                json={
                    **payload["policy"],
                    "description": "Direct duplicate should be rejected",
                },
            )
            assert direct_duplicate.status_code == 409, direct_duplicate.text
            assert direct_duplicate.json()["detail"]["policy_id"] == policy_id

            unassign_a = client.delete(
                f"/apps/by-client-id/{client_a}/policy-assignments/"
                f"{app_a_assignment_id}"
            )
            assert unassign_a.status_code == 204, unassign_a.text
            assert count_policy_assignments(app_a_id, policy_id) == 0
            assert count_policy_assignments(app_b_id, policy_id) == 1

            with SessionLocal() as db:
                assert db.get(PolicyRecord, policy_id) is not None

            global_resolution = client.post(
                "/global-policy-assignments/resolve",
                json=payload,
            )
            assert global_resolution.status_code == 200, global_resolution.text
            assert global_resolution.json()["resolution"] == "reused"
            assert global_resolution.json()["policy_id"] == policy_id

            app_a_after_global = client.post(
                f"/apps/by-client-id/{client_a}/policy-assignments/resolve",
                json=payload,
            )
            assert app_a_after_global.status_code == 200
            assert app_a_after_global.json()["resolution"] == "already_assigned"
            assert app_a_after_global.json()["scope"] == "global"
            assert count_policy_assignments(app_a_id, policy_id) == 0

        print("Policy resolution API checks passed.")
        print("- App A creates one reusable policy and assignment.")
        print("- Equivalent App A requests return already_assigned.")
        print("- App B reuses the same policy ID.")
        print("- App A edits safely to existing and new reusable policies.")
        print("- Direct duplicate policy creation returns 409.")
        print("- App A deletion removes only its assignment.")
        print("- Global assignment reuse prevents redundant App A assignment.")
    finally:
        cleanup_records([app_a_id, app_b_id], condition_value)


if __name__ == "__main__":
    main()
