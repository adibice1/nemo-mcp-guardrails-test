from _bootstrap import bootstrap_src

bootstrap_src()

from sqlalchemy import func, select

from nemo_mcp_guardrails.database.connection import (
    SessionLocal,
    create_database_tables,
)
from nemo_mcp_guardrails.database.models import (
    AppPolicyAssignmentRecord,
    GlobalPolicyAssignmentRecord,
    PolicyRecord,
)


def backfill_current_global_output_policies() -> None:
    """Globally assign existing output policies without duplicating links."""

    with SessionLocal() as db:
        output_policy_ids = tuple(
            db.scalars(
                select(PolicyRecord.id).where(
                    PolicyRecord.policy_type == "output",
                    PolicyRecord.enabled.is_(True),
                )
            )
        )
        assigned_policy_ids = set(
            db.scalars(select(GlobalPolicyAssignmentRecord.policy_id))
        )

        db.add_all(
            GlobalPolicyAssignmentRecord(policy_id=policy_id)
            for policy_id in output_policy_ids
            if policy_id not in assigned_policy_ids
        )
        db.commit()


def main() -> None:
    """Create assignment tables and globally assign current output policies."""

    create_database_tables()
    backfill_current_global_output_policies()

    with SessionLocal() as db:
        app_assignment_count = db.scalar(
            select(func.count()).select_from(AppPolicyAssignmentRecord)
        )
        global_assignment_count = db.scalar(
            select(func.count()).select_from(GlobalPolicyAssignmentRecord)
        )

    print("Policy assignment migration complete.")
    print(f"- app policy assignments: {app_assignment_count}")
    print(f"- global policy assignments: {global_assignment_count}")


if __name__ == "__main__":
    main()
