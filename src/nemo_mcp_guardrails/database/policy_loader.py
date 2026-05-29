from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from nemo_mcp_guardrails.database.connection import SessionLocal
from nemo_mcp_guardrails.database.models import PolicyRecord
from nemo_mcp_guardrails.policy_compiler import (
    DEFAULT_INPUT_POLICY_OBJECTS,
    DEFAULT_OUTPUT_POLICY_OBJECTS,
    InputPolicyObject,
    OutputPolicyObject,
)


def _load_enabled_policy_records(policy_type: str) -> list[PolicyRecord] | None:
    """Load enabled policy rows of one type, returning None if the DB is unavailable."""

    try:
        with SessionLocal() as db:
            return list(
                db.scalars(
                    select(PolicyRecord)
                    .where(
                        PolicyRecord.enabled.is_(True),
                        PolicyRecord.policy_type == policy_type,
                    )
                    .order_by(PolicyRecord.id)
                )
            )
    except SQLAlchemyError:
        return None


def _to_input_policy_object(record: PolicyRecord) -> InputPolicyObject | None:
    """Convert one enabled database row into an input policy object."""

    if not (record.app and record.action and record.resource and record.effect):
        return None

    return InputPolicyObject(
        app=record.app,
        action=record.action,
        resource=record.resource,
        effect=record.effect,
    )


def _to_output_policy_object(record: PolicyRecord) -> OutputPolicyObject | None:
    """Convert one enabled database row into an output policy object."""

    if not (record.category and record.description and record.effect):
        return None

    return OutputPolicyObject(
        category=record.category,
        description=record.description,
        effect=record.effect,
    )


def load_input_policy_objects() -> tuple[InputPolicyObject, ...]:
    """Load enabled input policies from Postgres, falling back to default policies."""

    records = _load_enabled_policy_records("input")
    if records is None:
        return DEFAULT_INPUT_POLICY_OBJECTS

    policies = tuple(
        policy
        for record in records
        if (policy := _to_input_policy_object(record)) is not None
    )

    return policies or DEFAULT_INPUT_POLICY_OBJECTS


def load_output_policy_objects() -> tuple[OutputPolicyObject, ...]:
    """Load enabled output policies from Postgres, falling back to default policies."""

    records = _load_enabled_policy_records("output")
    if records is None:
        return DEFAULT_OUTPUT_POLICY_OBJECTS

    policies = tuple(
        policy
        for record in records
        if (policy := _to_output_policy_object(record)) is not None
    )

    return policies or DEFAULT_OUTPUT_POLICY_OBJECTS
