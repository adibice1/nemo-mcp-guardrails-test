from _bootstrap import bootstrap_src

bootstrap_src()

from sqlalchemy import select

from nemo_mcp_guardrails.database.connection import SessionLocal
from nemo_mcp_guardrails.database.models import PolicyRecord
from nemo_mcp_guardrails.policy_rule_service import refresh_compiled_policy_rule


def preferred_policy_name(policy: PolicyRecord) -> str | None:
    """Return a stored assignment name when one is available."""

    if policy.global_assignment and policy.global_assignment.display_name:
        return policy.global_assignment.display_name.strip()
    for assignment in policy.app_assignments:
        if assignment.display_name and assignment.display_name.strip():
            return assignment.display_name.strip()
    return None


def main() -> None:
    """Move legacy output rule text into conditions and refresh compiled rules."""

    migrated = 0
    with SessionLocal() as db:
        policies = list(
            db.scalars(
                select(PolicyRecord)
                .where(PolicyRecord.policy_type == "output")
                .order_by(PolicyRecord.id)
            )
        )
        for policy in policies:
            conditions = dict(policy.conditions or {})
            if not str(conditions.get("output_rule") or "").strip():
                legacy_rule = (policy.description or "").strip()
                if not legacy_rule:
                    continue
                conditions["output_rule"] = legacy_rule
                policy.conditions = conditions

            display_name = preferred_policy_name(policy)
            if display_name:
                policy.description = display_name

            refresh_compiled_policy_rule(db, policy)
            migrated += 1

        db.commit()

    print(f"Migrated and recompiled {migrated} output policies.")


if __name__ == "__main__":
    main()
