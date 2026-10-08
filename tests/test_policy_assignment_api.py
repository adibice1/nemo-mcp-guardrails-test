from uuid import uuid4

from _bootstrap import bootstrap_src

bootstrap_src()

from fastapi.testclient import TestClient
from sqlalchemy import event, select
from _management_auth import install_management_admin_override

from nemo_mcp_guardrails.api.main import app
from nemo_mcp_guardrails.api.apps import (
    _effective_policy_assignments_for_app,
    _list_policy_assignments_for_app,
    list_app_summaries,
)
from nemo_mcp_guardrails.api.global_policy_assignments import (
    list_global_policy_assignments,
)
from nemo_mcp_guardrails.app_auth import hash_api_key
from nemo_mcp_guardrails.database.connection import SessionLocal
from nemo_mcp_guardrails.database.models import (
    AppPolicyAssignmentRecord,
    AppRecord,
    GlobalPolicyAssignmentRecord,
    PolicyRecord,
    UserRecord,
)


TEMP_API_KEY = "temporary-assignment-api-key"


def create_temporary_records() -> tuple[int, str, list[int]]:
    """Create one temporary app and two reusable policies."""

    suffix = uuid4().hex
    client_id = f"assignment-api-{suffix}"
    with SessionLocal() as db:
        app_record = AppRecord(
            name=f"Temporary Assignment App {suffix}",
            client_id=client_id,
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

        return app_record.id, client_id, [policy.id for policy in policies]


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


def assert_summary_counts(client: TestClient, app_id: int) -> None:
    """Compare the consolidated counts with the existing detail endpoints."""

    summaries = client.get("/apps/summaries")
    assert summaries.status_code == 200, summaries.text
    summary = next(item for item in summaries.json() if item["id"] == app_id)
    effective = client.get(f"/apps/{app_id}/effective-policy-assignments")
    connectors = client.get(f"/apps/{app_id}/connectors")
    assert effective.status_code == 200, effective.text
    assert connectors.status_code == 200, connectors.text
    assert summary["policy_count"] == effective.json()["enabled_assignment_count"]
    assert summary["connector_count"] == sum(
        item["enabled"] for item in connectors.json()
    )


def assert_list_query_counts(app_id: int) -> None:
    """Check fresh sessions do not lazy-load policy metadata per row."""

    admin = UserRecord(id=-1, system_role="admin")
    operations = (
        (lambda db, app_record: list_app_summaries(user=admin, db=db), 1),
        (lambda db, app_record: _effective_policy_assignments_for_app(app_record, db), 2),
        (lambda db, app_record: _list_policy_assignments_for_app(app_id, db), 1),
        (lambda db, app_record: list_global_policy_assignments(db=db), 1),
    )
    for operation, expected in operations:
        statements: list[str] = []

        def record_query(connection, cursor, statement, parameters, context, many):
            """Count SELECTs on this test connection without recording values."""

            if statement.lstrip().upper().startswith("SELECT"):
                statements.append("SELECT")

        with SessionLocal() as db:
            app_record = db.get(AppRecord, app_id)
            assert app_record is not None
            connection = db.connection()
            event.listen(connection, "before_cursor_execute", record_query)
            try:
                operation(db, app_record)
            finally:
                event.remove(connection, "before_cursor_execute", record_query)
        assert len(statements) == expected, (expected, len(statements))


def main() -> None:
    """Verify assignment APIs support single/bulk upserts and labels."""

    install_management_admin_override()
    app_id, client_id, policy_ids = create_temporary_records()

    try:
        with TestClient(app) as client:
            app_response = client.get(f"/apps/{app_id}")
            assert app_response.status_code == 200, app_response.text
            app_body = app_response.json()
            assert "display_label" in app_body
            assert app_body["display_label"].startswith("Temporary Assignment App")

            app_by_client_id_response = client.get(f"/apps/by-client-id/{client_id}")
            assert app_by_client_id_response.status_code == 200
            assert app_by_client_id_response.json()["id"] == app_id
            assert_summary_counts(client, app_id)

            app_bulk = client.post(
                f"/apps/{app_id}/policy-assignments",
                json={"policy_ids": policy_ids, "enabled": True},
            )
            assert app_bulk.status_code == 201, app_bulk.text
            app_bulk_body = app_bulk.json()
            assert len(app_bulk_body) == 2
            assert_summary_counts(client, app_id)
            assert_list_query_counts(app_id)
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
            assert_summary_counts(client, app_id)
            assert count_app_assignments(app_id) == 2

            app_client_id_list = client.get(
                f"/apps/by-client-id/{client_id}/policy-assignments"
            )
            assert app_client_id_list.status_code == 200, app_client_id_list.text
            assert len(app_client_id_list.json()) == 2

            app_client_id_update = client.post(
                f"/apps/by-client-id/{client_id}/policy-assignments",
                json={"policy_ids": [policy_ids[0]], "enabled": True},
            )
            assert app_client_id_update.status_code == 201
            assert app_client_id_update.json()[0]["policy_id"] == policy_ids[0]
            assert app_client_id_update.json()[0]["enabled"] is True
            assert count_app_assignments(app_id) == 2

            assignment_id = app_client_id_update.json()[0]["id"]
            app_client_id_put = client.put(
                f"/apps/by-client-id/{client_id}/policy-assignments/{assignment_id}",
                json={"enabled": False},
            )
            assert app_client_id_put.status_code == 200, app_client_id_put.text
            assert app_client_id_put.json()["id"] == assignment_id
            assert app_client_id_put.json()["enabled"] is False

            app_client_id_delete = client.delete(
                f"/apps/by-client-id/{client_id}/policy-assignments/{assignment_id}"
            )
            assert app_client_id_delete.status_code == 204
            assert_summary_counts(client, app_id)
            assert count_app_assignments(app_id) == 1

            app_bulk_restore = client.post(
                f"/apps/by-client-id/{client_id}/policy-assignments",
                json={"policy_ids": policy_ids, "enabled": True},
            )
            assert app_bulk_restore.status_code == 201, app_bulk_restore.text
            assert count_app_assignments(app_id) == 2

            app_bulk_update = client.put(
                f"/apps/by-client-id/{client_id}/policy-assignments",
                json={"policy_ids": policy_ids, "enabled": False},
            )
            assert app_bulk_update.status_code == 200, app_bulk_update.text
            assert len(app_bulk_update.json()) == 2
            assert all(item["enabled"] is False for item in app_bulk_update.json())
            assert_summary_counts(client, app_id)

            app_missing_bulk_update = client.put(
                f"/apps/by-client-id/{client_id}/policy-assignments",
                json={"policy_ids": [999999999], "enabled": True},
            )
            assert app_missing_bulk_update.status_code == 404

            app_bulk_delete = client.request(
                "DELETE",
                f"/apps/by-client-id/{client_id}/policy-assignments",
                json={"policy_ids": [policy_ids[0]]},
            )
            assert app_bulk_delete.status_code == 200, app_bulk_delete.text
            assert app_bulk_delete.json()["deleted_policy_ids"] == [policy_ids[0]]
            assert app_bulk_delete.json()["deleted_count"] == 1
            assert count_app_assignments(app_id) == 1

            app_missing_bulk_delete = client.request(
                "DELETE",
                f"/apps/by-client-id/{client_id}/policy-assignments",
                json={"policy_ids": [policy_ids[0]]},
            )
            assert app_missing_bulk_delete.status_code == 404

            global_bulk = client.post(
                "/global-policy-assignments",
                json={"policy_ids": policy_ids, "enabled": True},
            )
            assert global_bulk.status_code == 201, global_bulk.text
            global_bulk_body = global_bulk.json()
            assert len(global_bulk_body) == 2
            assert_summary_counts(client, app_id)
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
            assert_summary_counts(client, app_id)
            assert count_global_assignments(policy_ids) == 2

            global_bulk_update = client.put(
                "/global-policy-assignments",
                json={"policy_ids": policy_ids, "enabled": False},
            )
            assert global_bulk_update.status_code == 200, global_bulk_update.text
            assert len(global_bulk_update.json()) == 2
            assert all(item["enabled"] is False for item in global_bulk_update.json())
            assert_summary_counts(client, app_id)

            global_missing_bulk_update = client.put(
                "/global-policy-assignments",
                json={"policy_ids": [999999999], "enabled": True},
            )
            assert global_missing_bulk_update.status_code == 404

            global_bulk_delete = client.request(
                "DELETE",
                "/global-policy-assignments",
                json={"policy_ids": [policy_ids[0]]},
            )
            assert global_bulk_delete.status_code == 200, global_bulk_delete.text
            assert global_bulk_delete.json()["deleted_policy_ids"] == [policy_ids[0]]
            assert global_bulk_delete.json()["deleted_count"] == 1
            assert_summary_counts(client, app_id)
            assert count_global_assignments(policy_ids) == 1

            global_missing_bulk_delete = client.request(
                "DELETE",
                "/global-policy-assignments",
                json={"policy_ids": [policy_ids[0]]},
            )
            assert global_missing_bulk_delete.status_code == 404

            effective_by_id = client.get(
                f"/apps/{app_id}/effective-policy-assignments"
            )
            assert effective_by_id.status_code == 200, effective_by_id.text
            effective_body = effective_by_id.json()
            assert effective_body["app_id"] == app_id
            assert effective_body["app_label"].startswith("Temporary Assignment App")
            assert effective_body["global_assignment_count"] >= 1
            assert effective_body["app_assignment_count"] == 1
            assert effective_body["disabled_assignment_count"] >= 1

            app_policy_ids = {
                item["policy_id"] for item in effective_body["app_assignments"]
            }
            global_policy_ids = {
                item["policy_id"] for item in effective_body["global_assignments"]
            }
            assert policy_ids[1] in app_policy_ids
            assert policy_ids[1] in global_policy_ids
            assert all(
                "assignment_id" in item and "policy_label" in item
                for item in effective_body["global_assignments"]
            )
            assert all(
                "assignment_id" in item and item["scope"] == "app"
                for item in effective_body["app_assignments"]
            )

            effective_by_client_id = client.get(
                f"/apps/by-client-id/{client_id}/effective-policy-assignments"
            )
            assert effective_by_client_id.status_code == 200
            assert effective_by_client_id.json()["app_id"] == app_id
            assert_list_query_counts(app_id)

        print("Policy assignment API checks passed.")
        print("- App responses include display_label.")
        print("- App lookup and assignment CRUD aliases work with client_id.")
        print("- App policy assignments support single and bulk policy_ids.")
        print("- Global policy assignments support single and bulk policy_ids.")
        print("- Bulk assignment update/delete returns 404 for missing assignments.")
        print("- Effective policy assignment summaries include app and global scopes.")
        print("- Existing assignments update in place instead of duplicating rows.")
        print("- Assignment responses include readable labels.")

    finally:
        delete_temporary_records(app_id, policy_ids)


if __name__ == "__main__":
    main()
