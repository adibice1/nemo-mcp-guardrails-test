from uuid import uuid4

from _bootstrap import bootstrap_src

bootstrap_src()

from fastapi.testclient import TestClient
from sqlalchemy import select

from nemo_mcp_guardrails.api.main import app
from nemo_mcp_guardrails.database.connection import SessionLocal
from nemo_mcp_guardrails.database.models import (
    CompiledPolicyRuleRecord,
    ConnectorRecord,
    PolicyRecord,
)


def ensure_global_connector() -> tuple[int, bool]:
    """Ensure output-policy API tests can resolve the global connector."""

    with SessionLocal() as db:
        connector = db.scalar(
            select(ConnectorRecord).where(ConnectorRecord.name == "global")
        )
        if connector:
            return connector.id, False

        connector = ConnectorRecord(
            name="global",
            display_name="Global",
            enabled=True,
        )
        db.add(connector)
        db.commit()
        db.refresh(connector)
        return connector.id, True


def active_compiled_rules(policy_id: int) -> list[CompiledPolicyRuleRecord]:
    """Return active non-stale compiled rules for one policy."""

    with SessionLocal() as db:
        return list(
            db.scalars(
                select(CompiledPolicyRuleRecord).where(
                    CompiledPolicyRuleRecord.policy_id == policy_id,
                    CompiledPolicyRuleRecord.enabled.is_(True),
                    CompiledPolicyRuleRecord.stale.is_(False),
                )
            )
        )


def all_compiled_rules(policy_id: int) -> list[CompiledPolicyRuleRecord]:
    """Return every compiled rule for one policy."""

    with SessionLocal() as db:
        return list(
            db.scalars(
                select(CompiledPolicyRuleRecord).where(
                    CompiledPolicyRuleRecord.policy_id == policy_id,
                )
            )
        )


def policy_exists(policy_id: int) -> bool:
    """Return whether a policy row still exists."""

    with SessionLocal() as db:
        return db.get(PolicyRecord, policy_id) is not None


def delete_policy(policy_id: int) -> None:
    """Delete one temporary policy if it exists."""

    with SessionLocal() as db:
        policy = db.get(PolicyRecord, policy_id)
        if policy:
            db.delete(policy)
            db.commit()


def delete_global_connector_if_created(created: bool, connector_id: int) -> None:
    """Delete the temporary global connector only if this test created it."""

    if not created:
        return

    with SessionLocal() as db:
        connector = db.get(ConnectorRecord, connector_id)
        if connector:
            db.delete(connector)
            db.commit()


def main() -> None:
    """Verify policy CRUD automatically refreshes compiled rail rules."""

    connector_id, created_connector = ensure_global_connector()
    suffix = uuid4().hex
    policy_id: int | None = None

    try:
        with TestClient(app) as client:
            create_response = client.post(
                "/policies",
                json={
                    "policy_type": "output",
                    "category": f"auto_compile_category_{suffix}",
                    "description": "Temporary auto compile test policy.",
                    "effect": "block",
                    "enabled": True,
                },
            )
            assert create_response.status_code == 201, create_response.text
            policy_id = create_response.json()["id"]

            created_rules = active_compiled_rules(policy_id)
            assert len(created_rules) == 1
            assert created_rules[0].rail_type == "output"
            assert created_rules[0].policy_version == 1

            update_response = client.put(
                f"/policies/{policy_id}",
                json={
                    "description": "Temporary auto compile test policy updated.",
                },
            )
            assert update_response.status_code == 200, update_response.text
            assert update_response.json()["policy_version"] == 2

            updated_active_rules = active_compiled_rules(policy_id)
            assert len(updated_active_rules) == 1
            assert updated_active_rules[0].policy_version == 2

            all_rules_after_update = all_compiled_rules(policy_id)
            assert len(all_rules_after_update) == 2
            assert any(rule.stale is True for rule in all_rules_after_update)
            assert any(rule.enabled is False for rule in all_rules_after_update)

            disable_response = client.put(
                f"/policies/{policy_id}",
                json={"enabled": False},
            )
            assert disable_response.status_code == 200, disable_response.text
            assert disable_response.json()["policy_version"] == 3
            assert active_compiled_rules(policy_id) == []

            invalid_response = client.post(
                "/policies",
                json={
                    "policy_type": "output",
                    "category": f"auto_compile_invalid_{suffix}",
                    "effect": "block",
                    "enabled": True,
                },
            )
            assert invalid_response.status_code == 400

            with SessionLocal() as db:
                invalid_policy = db.scalar(
                    select(PolicyRecord).where(
                        PolicyRecord.category == f"auto_compile_invalid_{suffix}"
                    )
                )
                assert invalid_policy is None

            delete_response = client.delete(f"/policies/{policy_id}")
            assert delete_response.status_code == 204, delete_response.text
            assert not policy_exists(policy_id)
            assert all_compiled_rules(policy_id) == []

        print("Policy auto-compile checks passed.")
        print("- POST /policies creates an active compiled rule.")
        print("- PUT /policies/{id} stales old rules and creates a new active rule.")
        print("- Disabling a policy leaves no active compiled rule.")
        print("- Invalid compiler input returns 400 without partial persistence.")
        print("- Deleting a policy cascades compiled rules.")

    finally:
        if policy_id is not None:
            delete_policy(policy_id)
        delete_global_connector_if_created(created_connector, connector_id)


if __name__ == "__main__":
    main()
