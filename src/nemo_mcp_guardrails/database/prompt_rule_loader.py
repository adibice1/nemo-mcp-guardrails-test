from dataclasses import dataclass

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import SQLAlchemyError

from nemo_mcp_guardrails.database.connection import SessionLocal
from nemo_mcp_guardrails.database.policy_errors import PolicyLoadError
from nemo_mcp_guardrails.database.policy_loader import (
    default_policy_source_requested,
    load_input_policy_objects,
    load_output_policy_objects,
)
from nemo_mcp_guardrails.policy_compiler import compile_output_rail_rules, compile_policy
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

    if default_policy_source_requested():
        return tuple(
            LoadedPromptRule("default", None, None, rail_type, text)
            for rail_type, texts in (
                ("input", tuple(
                    compile_policy(policy).input_rail_rule
                    for policy in load_input_policy_objects()
                )),
                ("output", compile_output_rail_rules(load_output_policy_objects())),
            )
            for text in texts
        )

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
    except SQLAlchemyError as error:
        raise PolicyLoadError("Compiled policies could not be loaded.") from error

    for record in records:
        if (
            record.rail_type not in {"input", "output"}
            or not isinstance(record.rule_text, str) or not record.rule_text.strip()
        ):
            raise PolicyLoadError("Compiled policy metadata is invalid.")

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
