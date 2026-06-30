from uuid import uuid4

from _bootstrap import bootstrap_src

bootstrap_src()

from sqlalchemy import select

from nemo_mcp_guardrails.app_auth import hash_api_key
from nemo_mcp_guardrails.database.connection import SessionLocal
from nemo_mcp_guardrails.database.models import (
    AppPolicyAssignmentRecord,
    AppRecord,
    PolicyRecord,
)
from nemo_mcp_guardrails.policy_service import (
    consolidate_equivalent_policies,
    resolve_policy_references,
)


def main() -> None:
    """Verify duplicate definitions merge without losing app display names."""

    suffix = uuid4().hex
    client_id = f"dedupe-app-{suffix}"
    condition = f"dedupe-{suffix}"
    app_id: int | None = None
    canonical_id: int | None = None
    duplicate_id: int | None = None

    try:
        with SessionLocal() as db:
            app = AppRecord(
                name=f"Dedupe App {suffix}",
                client_id=client_id,
                api_key_hash=hash_api_key("temporary-dedupe-key"),
                authorized=True,
            )
            db.add(app)
            db.flush()
            app_id = app.id

            canonical = PolicyRecord(
                policy_type="input",
                connector="github",
                action="create",
                resource="issue",
                description=None,
                effect="block",
                priority=100,
                conditions={"custom_resource": condition},
                enabled=True,
            )
            duplicate = PolicyRecord(
                policy_type="input",
                connector="github",
                action="create",
                resource="issue",
                description="Readable duplicate name",
                effect="block",
                priority=100,
                conditions={"custom_resource": condition},
                enabled=True,
            )
            resolve_policy_references(canonical, db)
            resolve_policy_references(duplicate, db)
            db.add_all([canonical, duplicate])
            db.flush()
            canonical_id = canonical.id
            duplicate_id = duplicate.id
            db.add_all(
                [
                    AppPolicyAssignmentRecord(
                        app_id=app.id,
                        policy_id=canonical.id,
                        enabled=True,
                    ),
                    AppPolicyAssignmentRecord(
                        app_id=app.id,
                        policy_id=duplicate.id,
                        display_name="App-specific readable name",
                        enabled=True,
                    ),
                ]
            )
            db.commit()

        with SessionLocal() as db:
            results = consolidate_equivalent_policies(db)
            db.commit()
            matching = [
                result
                for result in results
                if result.removed_policy_id == duplicate_id
            ]
            assert len(matching) == 1
            assert matching[0].canonical_policy_id == canonical_id
            assert matching[0].merged_app_assignments == 1

        with SessionLocal() as db:
            assert db.get(PolicyRecord, duplicate_id) is None
            canonical = db.get(PolicyRecord, canonical_id)
            assert canonical is not None
            assert canonical.description == "Readable duplicate name"
            assignments = list(
                db.scalars(
                    select(AppPolicyAssignmentRecord).where(
                        AppPolicyAssignmentRecord.app_id == app_id
                    )
                )
            )
            assert len(assignments) == 1
            assert assignments[0].policy_id == canonical_id
            assert assignments[0].display_name == "App-specific readable name"

        print("Policy deduplication checks passed.")
    finally:
        with SessionLocal() as db:
            if app_id is not None:
                app = db.get(AppRecord, app_id)
                if app is not None:
                    db.delete(app)
            for policy_id in (canonical_id, duplicate_id):
                if policy_id is not None:
                    policy = db.get(PolicyRecord, policy_id)
                    if policy is not None:
                        db.delete(policy)
            db.commit()


if __name__ == "__main__":
    main()
