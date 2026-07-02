from sqlalchemy import select, update
from sqlalchemy.orm import Session

from nemo_mcp_guardrails.database.models import (
    CompiledPolicyRuleRecord,
    PolicyRecord,
)
from nemo_mcp_guardrails.policy_compiler import (
    InputPolicyObject,
    OutputPolicyObject,
    compile_output_rail_rules,
    compile_policy,
)


def to_input_policy_object(policy: PolicyRecord) -> InputPolicyObject:
    """Convert a stored input policy row into the compiler dataclass."""

    connector = (
        policy.normalized_connector.name
        if policy.normalized_connector
        else policy.connector
    )
    action = policy.normalized_action.name if policy.normalized_action else policy.action
    resource = (
        policy.normalized_resource.name
        if policy.normalized_resource
        else policy.resource
    )

    if not (connector and action and resource and policy.effect):
        raise ValueError(f"Policy {policy.id} is missing required input policy fields")

    custom_resource_value = (policy.conditions or {}).get("custom_resource")
    custom_resource = (
        str(custom_resource_value).strip()
        if custom_resource_value is not None
        else None
    )

    return InputPolicyObject(
        connector=connector,
        action=action,
        resource=resource,
        effect=policy.effect,
        custom_resource=custom_resource or None,
    )


def to_output_policy_object(policy: PolicyRecord) -> OutputPolicyObject:
    """Convert a stored output policy row into the compiler dataclass."""

    output_rule_value = (policy.conditions or {}).get("output_rule")
    output_rule = (
        str(output_rule_value).strip()
        if output_rule_value is not None
        else (policy.description or "").strip()
    )
    missing_fields = [
        field
        for field, value in (
            ("category", policy.category),
            ("output_rule", output_rule),
            ("effect", policy.effect),
        )
        if not value
    ]
    if missing_fields:
        raise ValueError(
            f"Policy {policy.id} is missing required fields: "
            + ", ".join(missing_fields)
        )

    return OutputPolicyObject(
        category=policy.category or "",
        description=output_rule,
        effect=policy.effect,
    )


def compile_policy_rule_record(policy: PolicyRecord) -> CompiledPolicyRuleRecord:
    """Compile one stored policy row into a persisted rail rule record."""

    if policy.policy_type == "input":
        compiled_policy = compile_policy(to_input_policy_object(policy))
        return CompiledPolicyRuleRecord(
            policy_id=policy.id,
            rail_type="input",
            rule_text=compiled_policy.input_rail_rule,
            policy_version=policy.policy_version,
            stale=False,
            enabled=True,
        )

    if policy.policy_type == "output":
        output_rules = compile_output_rail_rules((to_output_policy_object(policy),))
        return CompiledPolicyRuleRecord(
            policy_id=policy.id,
            rail_type="output",
            rule_text=output_rules[0],
            policy_version=policy.policy_version,
            stale=False,
            enabled=True,
        )

    raise ValueError(f"Unsupported policy type: {policy.policy_type}")


def mark_compiled_policy_rules_stale(db: Session, policy_id: int) -> None:
    """Disable previously compiled rules for one policy."""

    db.execute(
        update(CompiledPolicyRuleRecord)
        .where(CompiledPolicyRuleRecord.policy_id == policy_id)
        .values(stale=True, enabled=False)
    )


def refresh_compiled_policy_rule(
    db: Session,
    policy: PolicyRecord,
) -> CompiledPolicyRuleRecord | None:
    """Refresh the compiled rule for one policy inside the caller transaction."""

    mark_compiled_policy_rules_stale(db, policy.id)

    if not policy.enabled:
        return None

    compiled_rule = compile_policy_rule_record(policy)
    db.add(compiled_rule)
    return compiled_rule


def refresh_all_compiled_policy_rules(db: Session) -> list[CompiledPolicyRuleRecord]:
    """Refresh compiled rules for every enabled policy inside the transaction."""

    db.execute(update(CompiledPolicyRuleRecord).values(stale=True, enabled=False))

    policies = list(
        db.scalars(
            select(PolicyRecord)
            .where(PolicyRecord.enabled.is_(True))
            .order_by(PolicyRecord.id)
        )
    )
    compiled_rules = [compile_policy_rule_record(policy) for policy in policies]
    db.add_all(compiled_rules)
    return compiled_rules
