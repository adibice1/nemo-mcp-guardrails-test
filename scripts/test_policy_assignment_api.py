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
    GlobalPolicyAssignmentRecord,
    PolicyRecord,
)


TEMP_API_KEY = "temporary-assignment-api-key"


def create_temporary_records() -> tuple[int, list[int]]:
    """Create one temporary app and two reusable policies."""

    suffix = uuid4().hex
    with SessionLocal() as db:
        app_record = AppRecord(
            name=f"Temporary Assignment App {suffix}",
            client_id=f"assignment-api-{suffix}",
            api_key_hash=hash_api_key(TEMP_API_KEY),
            authorized=True,
        )
        policies = [
            PolicyRecord(
                policy_type="output",
                category=f"temporary_assignment_category_a_{suffix}",
                description="Temporary assignment API test policy A",
                effect="block",
                enabled=True,
            ),
            PolicyRecord(
                policy_type="output",
                category=f"temporary_assignment_category_b_{suffix}",
                description="Temporary assignment API test policy B",
                effect="block",
                enabled=True,
            ),
        ]
        db.add(app_record)
        db.add_all(policies)
        db.commit()
        db.refresh(app_record)
        for policy in policies:
            db.refresh(policy)

        return app_record.id, [policy.id for policy in policies]


def delete_temporary_records(app_id: int, policy_ids: list[int]) -> None:
    """Delete temporary app and policies created by this test."""

    with SessionLocal() as db:
        app_record = db.get(AppRecord, app_id)
        if app_record:
            db.delete(app_record)

        for policy_id in policy_ids:
            policy = db.get(PolicyRecord, policy_id)
            if policy:
                db.delete(policy)

        db.commit()


def count_app_assignments(app_id: int) -> int:
    """Return assignment count for one app."""

    with SessionLocal() as db:
        return len(
            list(
                db.scalars(
                    select(AppPolicyAssignmentRecord).where(
                        AppPolicyAssignmentRecord.app_id == app_id
                    )
                )
            )
        )


def count_global_assignments(policy_ids: list[int]) -> int:
    """Return global assignment count for the supplied policy IDs."""

    with SessionLocal() as db:
        return len(
            list(
                db.scalars(
                    select(GlobalPolicyAssignmentRecord).where(
                        GlobalPolicyAssignmentRecord.policy_id.in_(policy_ids)
                    )
                )
            )
        )


def main() -> None:
    """Verify assignment APIs support single/bulk upserts and labels."""

    app_id, policy_ids = create_temporary_records()

    try:
        with TestClient(app) as client:
            app_response = client.get(f"/apps/{app_id}")
            assert app_response.status_code == 200, app_response.text
            app_body = app_response.json()
            assert "display_label" in app_body
            assert app_body["display_label"].startswith("Temporary Assignment App")

            app_bulk = client.post(
                f"/apps/{app_id}/policy-assignments",
                json={"policy_ids": policy_ids, "enabled": True},
            )
            assert app_bulk.status_code == 201, app_bulk.text
            app_bulk_body = app_bulk.json()
            assert len(app_bulk_body) == 2
            assert {item["policy_id"] for item in app_bulk_body} == set(policy_ids)
            assert all(item["app_label"] for item in app_bulk_body)
            assert all(item["policy_label"].startswith("Block") for item in app_bulk_body)
            assert count_app_assignments(app_id) == 2

            app_single_update = client.post(
                f"/apps/{app_id}/policy-assignments",
                json={"policy_ids": [policy_ids[0]], "enabled": False},
            )
            assert app_single_update.status_code == 201, app_single_update.text
            app_single_body = app_single_update.json()
            assert len(app_single_body) == 1
            assert app_single_body[0]["policy_id"] == policy_ids[0]
            assert app_single_body[0]["enabled"] is False
            assert count_app_assignments(app_id) == 2

            global_bulk = client.post(
                "/global-policy-assignments",
                json={"policy_ids": policy_ids, "enabled": True},
            )
            assert global_bulk.status_code == 201, global_bulk.text
            global_bulk_body = global_bulk.json()
            assert len(global_bulk_body) == 2
            assert {item["policy_id"] for item in global_bulk_body} == set(policy_ids)
            assert all(item["policy_label"].startswith("Block") for item in global_bulk_body)
            assert count_global_assignments(policy_ids) == 2

            global_single_update = client.post(
                "/global-policy-assignments",
                json={"policy_ids": [policy_ids[1]], "enabled": False},
            )
            assert global_single_update.status_code == 201, global_single_update.text
            global_single_body = global_single_update.json()
            assert len(global_single_body) == 1
            assert global_single_body[0]["policy_id"] == policy_ids[1]
            assert global_single_body[0]["enabled"] is False
            assert count_global_assignments(policy_ids) == 2

        print("Policy assignment API checks passed.")
        print("- App responses include display_label.")
        print("- App policy assignments support single and bulk policy_ids.")
        print("- Global policy assignments support single and bulk policy_ids.")
        print("- Existing assignments update in place instead of duplicating rows.")
        print("- Assignment responses include readable labels.")

    finally:
        delete_temporary_records(app_id, policy_ids)


if __name__ == "__main__":
    main()
