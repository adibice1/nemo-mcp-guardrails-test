"""Read detached enforcement definitions and their compiled rules in one SELECT."""

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from nemo_mcp_guardrails.database.models import (
    AppPolicyAssignmentRecord, AppRecord, CompiledPolicyRuleRecord,
    ConnectorActionRecord, ConnectorRecord, ConnectorResourceRecord,
    GlobalPolicyAssignmentRecord, PolicyRecord,
)
from nemo_mcp_guardrails.database.policy_errors import PolicyLoadError
from nemo_mcp_guardrails.github_resource_bindings import compile_resource_binding
from nemo_mcp_guardrails.input_conditions import prepare_input_conditions
from nemo_mcp_guardrails.policy_compiler import (
    InputPolicyObject, OutputPolicyObject, compile_output_rail_rules, compile_policy,
)


@dataclass(frozen=True)
class SnapshotPolicy:
    """Keep exact policy/artifact contents without mutable ORM or JSON values."""

    policy_id: int
    policy_version: int
    priority: int
    policy: InputPolicyObject | OutputPolicyObject = field(repr=False)
    compiled_rule_id: int
    rule_text: str = field(repr=False)


@dataclass(frozen=True)
class RuntimePolicySnapshot:
    """Represent one app's complete selected policy content for later comparison."""

    app_id: int
    policies: tuple[SnapshotPolicy, ...]


def _snapshot_statement(app_id: int) -> Any:
    """Select authorization, definitions, normalized metadata and artifacts atomically."""

    app = AppRecord.__table__
    policy = PolicyRecord.__table__
    rule = CompiledPolicyRuleRecord.__table__
    global_link = GlobalPolicyAssignmentRecord.__table__
    app_link = AppPolicyAssignmentRecord.__table__
    connector = ConnectorRecord.__table__
    action = ConnectorActionRecord.__table__
    resource = ConnectorResourceRecord.__table__
    assigned = or_(
        select(global_link.c.id).where(
            global_link.c.policy_id == policy.c.id, global_link.c.enabled.is_(True),
        ).correlate(policy).exists(),
        select(app_link.c.id).where(
            app_link.c.policy_id == policy.c.id, app_link.c.app_id == app.c.id,
            app_link.c.enabled.is_(True),
        ).correlate(policy, app).exists(),
    )
    columns = [app.c.id.label("app_id")]
    columns.extend(policy.c[name] for name in (
        "id", "policy_type", "effect", "priority", "conditions", "policy_version",
        "connector_id", "action_id", "resource_id", "connector", "action", "resource",
        "category", "description",
    ))
    columns.extend(rule.c[name].label(f"compiled_{name}") for name in (
        "id", "rail_type", "rule_text", "policy_version", "stale",
    ))
    for name, table in (("connector", connector), ("action", action), ("resource", resource)):
        columns.extend((table.c.name.label(f"normalized_{name}"),
                        table.c.enabled.label(f"{name}_enabled")))
        if name != "connector":
            columns.append(table.c.connector_id.label(f"{name}_connector_id"))
    source = app.outerjoin(policy, and_(policy.c.enabled.is_(True), assigned))
    source = source.outerjoin(rule, and_(rule.c.policy_id == policy.c.id, rule.c.enabled.is_(True)))
    source = source.outerjoin(connector, connector.c.id == policy.c.connector_id)
    source = source.outerjoin(action, action.c.id == policy.c.action_id)
    source = source.outerjoin(resource, resource.c.id == policy.c.resource_id)
    return select(*columns).select_from(source).where(
        app.c.id == app_id, app.c.authorized.is_(True),
    ).order_by(policy.c.id, rule.c.id)


def _input_policy(row: Mapping[str, Any], conditions: dict) -> InputPolicyObject:
    """Require supported metadata and canonical versioned nonempty selectors."""

    metadata = {}
    for name in ("connector", "action", "resource"):
        if row[f"{name}_id"] is not None:
            value = row[f"normalized_{name}"]
            if row[f"{name}_enabled"] is not True:
                raise ValueError("Unavailable normalized metadata.")
            if name != "connector" and (
                row["connector_id"] is None
                or row[f"{name}_connector_id"] != row["connector_id"]
            ):
                raise ValueError("Inconsistent normalized metadata.")
        else:
            value = row[name]
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Missing input metadata.")
        metadata[name] = value
    policy = InputPolicyObject(**metadata, effect=row["effect"],
                               custom_resource=conditions.get("custom_resource"))
    prepared = prepare_input_conditions(policy, conditions)
    if prepared and prepared != conditions:
        raise ValueError("Unreviewed or noncanonical input selector.")
    # Also reject unsupported broad combinations; an empty selector is no exemption.
    policy = replace(policy, custom_resource=prepared.get("custom_resource"))
    compile_resource_binding(policy)
    return policy


def _snapshot_policy(row: Mapping[str, Any]) -> SnapshotPolicy:
    """Verify a selected definition has exactly the current compiler artifact."""

    conditions = row["conditions"]
    if conditions is None:
        conditions = {}
    if not isinstance(conditions, dict) or row["effect"] != "block":
        raise ValueError("Invalid policy conditions or effect.")
    if type(row["policy_version"]) is not int or row["policy_version"] < 1:
        raise ValueError("Invalid policy version.")
    if type(row["priority"]) is not int:
        raise ValueError("Invalid policy priority.")
    if row["policy_type"] == "input":
        policy = _input_policy(row, conditions)
        text = compile_policy(policy).input_rail_rule
    elif row["policy_type"] == "output":
        output_rule = conditions.get("output_rule")
        if output_rule is None:
            output_rule = row["description"]
        if not all(isinstance(value, str) and value.strip()
                   for value in (row["category"], output_rule)):
            raise ValueError("Invalid output metadata.")
        policy = OutputPolicyObject(row["category"], output_rule.strip(), row["effect"])
        text, = compile_output_rail_rules((policy,))
    else:
        raise ValueError("Unsupported policy type.")
    if (
        row["compiled_id"] is None or row["compiled_stale"] is not False
        or row["compiled_rail_type"] != row["policy_type"]
        or row["compiled_policy_version"] != row["policy_version"]
        or row["compiled_rule_text"] != text
    ):
        raise ValueError("Missing or mismatched compiled artifact.")
    return SnapshotPolicy(row["id"], row["policy_version"], row["priority"], policy,
                          row["compiled_id"], text)


def read_runtime_policy_snapshot(db: Session, app_id: int) -> RuntimePolicySnapshot:
    """Read one authorized app's exact scoped state without flushing or fallback."""

    if type(app_id) is not int or app_id < 1:
        raise PolicyLoadError("Runtime policy snapshot is unavailable.")
    try:
        with db.no_autoflush:
            rows = list(db.execute(_snapshot_statement(app_id)).mappings())
        if not rows:
            raise ValueError("App is unavailable.")
        policies = []
        seen = set()
        for row in rows:
            if row["id"] is None:
                continue  # An authorized app with no selected policies is legitimate.
            if row["id"] in seen:
                raise ValueError("Multiple enabled artifacts for one policy.")
            seen.add(row["id"])
            policies.append(_snapshot_policy(row))
        return RuntimePolicySnapshot(app_id, tuple(policies))
    except (SQLAlchemyError, ValueError, TypeError, KeyError, AttributeError):
        raise PolicyLoadError("Runtime policy snapshot is unavailable.") from None
