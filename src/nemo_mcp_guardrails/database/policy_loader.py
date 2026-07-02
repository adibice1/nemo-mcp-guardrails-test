import os
from dataclasses import dataclass

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from nemo_mcp_guardrails.database.connection import SessionLocal
from nemo_mcp_guardrails.database.models import (
    AppPolicyAssignmentRecord,
    GlobalPolicyAssignmentRecord,
    PolicyRecord,
)
from nemo_mcp_guardrails.policy_compiler import (
    DEFAULT_INPUT_POLICY_OBJECTS,
    DEFAULT_OUTPUT_POLICY_OBJECTS,
    InputPolicyObject,
    OutputPolicyObject,
)


POLICY_SOURCE_ENV = "NEMO_POLICY_SOURCE"


@dataclass(frozen=True)
class LoadedInputPolicy:
    """Represent one loaded input policy plus its source metadata."""

    source: str
    source_id: int | None
    policy: InputPolicyObject


def default_policy_source_requested() -> bool:
    """Return whether runtime policy loading should skip the database."""

    return os.getenv(POLICY_SOURCE_ENV, "").lower() in {
        "default",
        "defaults",
        "static",
    }


def _load_enabled_policy_records(
    policy_type: str,
    app_id: int | None = None,
) -> list[PolicyRecord] | None:
    """Load enabled policies, optionally scoped to global and app assignments."""

    try:
        with SessionLocal() as db:
            statement = (
                select(PolicyRecord)
                .options(
                    selectinload(PolicyRecord.normalized_connector),
                    selectinload(PolicyRecord.normalized_action),
                    selectinload(PolicyRecord.normalized_resource),
                )
                .where(
                    PolicyRecord.enabled.is_(True),
                    PolicyRecord.policy_type == policy_type,
                )
                .order_by(PolicyRecord.id)
            )

            if app_id is not None:
                statement = statement.where(
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
                    )
                )

            return list(db.scalars(statement))
    except SQLAlchemyError:
        return None


def _to_input_policy_object(record: PolicyRecord) -> InputPolicyObject | None:
    """Convert one enabled database row into an input policy object."""

    connector = (
        record.normalized_connector.name
        if record.normalized_connector
        else record.connector
    )
    action = record.normalized_action.name if record.normalized_action else record.action
    resource = (
        record.normalized_resource.name if record.normalized_resource else record.resource
    )

    if not (connector and action and resource and record.effect):
        return None

    custom_resource_value = (record.conditions or {}).get("custom_resource")
    custom_resource = (
        str(custom_resource_value).strip()
        if custom_resource_value is not None
        else None
    )

    return InputPolicyObject(
        connector=connector,
        action=action,
        resource=resource,
        effect=record.effect,
        custom_resource=custom_resource or None,
    )


def _to_output_policy_object(record: PolicyRecord) -> OutputPolicyObject | None:
    """Convert one enabled database row into an output policy object."""

    output_rule_value = (record.conditions or {}).get("output_rule")
    output_rule = (
        str(output_rule_value).strip()
        if output_rule_value is not None
        else (record.description or "").strip()
    )
    if not (record.category and output_rule and record.effect):
        return None

    return OutputPolicyObject(
        category=record.category,
        description=output_rule,
        effect=record.effect,
    )


def _default_input_policy_entries() -> tuple[LoadedInputPolicy, ...]:
    """Return default input policies with source metadata."""

    return tuple(
        LoadedInputPolicy(
            source="default",
            source_id=None,
            policy=policy,
        )
        for policy in DEFAULT_INPUT_POLICY_OBJECTS
    )


def load_input_policy_entries(
    app_id: int | None = None,
) -> tuple[LoadedInputPolicy, ...]:
    """Load enabled input policies, optionally scoped to one app."""

    if default_policy_source_requested():
        return _default_input_policy_entries()

    records = _load_enabled_policy_records("input", app_id=app_id)
    if records is None:
        return _default_input_policy_entries()

    entries = tuple(
        LoadedInputPolicy(
            source="database",
            source_id=record.id,
            policy=policy,
        )
        for record in records
        if (policy := _to_input_policy_object(record)) is not None
    )

    if app_id is not None:
        return entries

    return entries or _default_input_policy_entries()


def load_input_policy_objects(
    app_id: int | None = None,
) -> tuple[InputPolicyObject, ...]:
    """Load enabled input policy objects, optionally scoped to one app."""

    return tuple(
        entry.policy for entry in load_input_policy_entries(app_id=app_id)
    )


def load_output_policy_objects(
    app_id: int | None = None,
) -> tuple[OutputPolicyObject, ...]:
    """Load enabled output policy objects, optionally scoped to one app."""

    if default_policy_source_requested():
        return DEFAULT_OUTPUT_POLICY_OBJECTS

    records = _load_enabled_policy_records("output", app_id=app_id)
    if records is None:
        return DEFAULT_OUTPUT_POLICY_OBJECTS

    policies = tuple(
        policy
        for record in records
        if (policy := _to_output_policy_object(record)) is not None
    )

    if app_id is not None:
        return policies

    return policies or DEFAULT_OUTPUT_POLICY_OBJECTS
