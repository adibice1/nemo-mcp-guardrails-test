from dataclasses import dataclass

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import SQLAlchemyError

from nemo_mcp_guardrails.database.connection import SessionLocal
from nemo_mcp_guardrails.database.models import (
    AppPolicyAssignmentRecord,
    CompiledPolicyRuleRecord,
    GlobalPolicyAssignmentRecord,
    PolicyRecord,
)


@dataclass(frozen=True)
class LoadedPromptRule:
    """Represent one compiled prompt rule loaded from the database."""

    source: str
    source_id: int | None
    policy_id: int | None
    rail_type: str
    rule_text: str


def load_prompt_policy_rules(
    app_id: int | None = None,
) -> tuple[LoadedPromptRule, ...]:
    """Load enabled compiled prompt rules, optionally scoped to one app."""

    try:
        with SessionLocal() as db:
            statement = (
                select(CompiledPolicyRuleRecord)
                .where(
                    CompiledPolicyRuleRecord.enabled.is_(True),
                    CompiledPolicyRuleRecord.stale.is_(False),
                )
                .order_by(
                    CompiledPolicyRuleRecord.rail_type,
                    CompiledPolicyRuleRecord.id,
                )
            )

            if app_id is not None:
                statement = statement.join(
                    PolicyRecord,
                    PolicyRecord.id == CompiledPolicyRuleRecord.policy_id,
                ).where(
                    PolicyRecord.enabled.is_(True),
                    or_(
                        PolicyRecord.global_assignment.has(
                            GlobalPolicyAssignmentRecord.enabled.is_(True)
                        ),
                        PolicyRecord.app_assignments.any(
                            and_(
                                AppPolicyAssignmentRecord.app_id == app_id,
                                AppPolicyAssignmentRecord.enabled.is_(True),
                            )
                        ),
                    ),
                )

            records = list(db.scalars(statement))
    except SQLAlchemyError:
        return ()

    return tuple(
        LoadedPromptRule(
            source="database",
            source_id=record.id,
            policy_id=record.policy_id,
            rail_type=record.rail_type,
            rule_text=record.rule_text,
        )
        for record in records
    )
