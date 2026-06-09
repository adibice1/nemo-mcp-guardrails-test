from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from nemo_mcp_guardrails.database.connection import SessionLocal
from nemo_mcp_guardrails.database.models import CompiledPolicyRuleRecord


@dataclass(frozen=True)
class LoadedPromptRule:
    """Represent one compiled prompt rule loaded from the database."""

    source: str
    source_id: int | None
    policy_id: int | None
    rail_type: str
    rule_text: str


def load_prompt_policy_rules() -> tuple[LoadedPromptRule, ...]:
    """Load enabled compiled prompt rules from Postgres."""

    try:
        with SessionLocal() as db:
            records = list(
                db.scalars(
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
            )
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
