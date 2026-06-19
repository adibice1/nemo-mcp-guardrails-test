from typing import Any

from nemo_mcp_guardrails.database.models import (
    AppConnectorRecord,
    AppPolicyAssignmentRecord,
    AppRecord,
    GlobalPolicyAssignmentRecord,
    PolicyRecord,
)


def app_label(app: AppRecord) -> str:
    """Return a readable app label for API responses."""

    return f"{app.name} ({app.client_id})"


def _fallback_display_name(value: str | None) -> str | None:
    if value is None:
        return None
    return value.replace("_", " ").title()


def policy_connector_name(policy: PolicyRecord) -> str | None:
    """Return the policy connector display name with legacy fallback."""

    if policy.normalized_connector is not None:
        return policy.normalized_connector.display_name
    return _fallback_display_name(policy.connector)


def policy_action_name(policy: PolicyRecord) -> str | None:
    """Return the policy action display name with legacy fallback."""

    if policy.normalized_action is not None:
        return policy.normalized_action.display_name
    return _fallback_display_name(policy.action)


def policy_resource_name(policy: PolicyRecord) -> str | None:
    """Return the policy resource display name with legacy fallback."""

    if policy.normalized_resource is not None:
        return policy.normalized_resource.display_name
    return _fallback_display_name(policy.resource)


def policy_label(policy: PolicyRecord) -> str:
    """Return a concise readable policy label for API responses."""

    effect = (policy.effect or "policy").title()
    if policy.policy_type == "input":
        parts = [
            effect,
            policy_connector_name(policy),
            policy_action_name(policy),
            policy_resource_name(policy),
        ]
        return " ".join(part for part in parts if part)

    if policy.policy_type == "output":
        category = _fallback_display_name(policy.category) or "Output"
        return f"{effect} {category} Output"

    return f"Policy #{policy.id}"


def serialize_app(app: AppRecord) -> dict[str, Any]:
    """Serialize one app with a frontend-friendly display label."""

    return {
        "id": app.id,
        "name": app.name,
        "client_id": app.client_id,
        "display_label": app_label(app),
        "authorized": app.authorized,
        "main_llm_config_id": app.main_llm_config_id,
        "guardrail_llm_config_id": app.guardrail_llm_config_id,
        "created_at": app.created_at,
        "updated_at": app.updated_at,
    }


def serialize_app_connector(link: AppConnectorRecord) -> dict[str, Any]:
    """Serialize one app connector link with readable labels."""

    return {
        "id": link.id,
        "app_id": link.app_id,
        "app_label": app_label(link.app),
        "connector_id": link.connector_id,
        "connector_name": link.connector.name,
        "connector_display_name": link.connector.display_name,
        "credential_reference": link.credential_reference,
        "enabled": link.enabled,
        "connector_enabled": link.connector.enabled,
        "created_at": link.created_at,
        "updated_at": link.updated_at,
    }


def _policy_details(policy: PolicyRecord) -> dict[str, Any]:
    return {
        "policy_label": policy_label(policy),
        "policy_type": policy.policy_type,
        "connector": policy_connector_name(policy),
        "action": policy_action_name(policy),
        "resource": policy_resource_name(policy),
        "category": policy.category,
    }


def serialize_app_policy_assignment(
    assignment: AppPolicyAssignmentRecord,
) -> dict[str, Any]:
    """Serialize one app policy assignment with policy and app labels."""

    data = {
        "id": assignment.id,
        "app_id": assignment.app_id,
        "app_label": app_label(assignment.app),
        "policy_id": assignment.policy_id,
        "enabled": assignment.enabled,
        "created_at": assignment.created_at,
        "updated_at": assignment.updated_at,
    }
    data.update(_policy_details(assignment.policy))
    return data


def serialize_global_policy_assignment(
    assignment: GlobalPolicyAssignmentRecord,
) -> dict[str, Any]:
    """Serialize one global policy assignment with readable policy details."""

    data = {
        "id": assignment.id,
        "policy_id": assignment.policy_id,
        "enabled": assignment.enabled,
        "created_at": assignment.created_at,
        "updated_at": assignment.updated_at,
    }
    data.update(_policy_details(assignment.policy))
    return data


def serialize_effective_global_assignment(
    assignment: GlobalPolicyAssignmentRecord,
) -> dict[str, Any]:
    """Serialize one global assignment for an app effective-policy view."""

    data = {
        "assignment_id": assignment.id,
        "scope": "global",
        "policy_id": assignment.policy_id,
        "enabled": assignment.enabled,
        "created_at": assignment.created_at,
        "updated_at": assignment.updated_at,
    }
    data.update(_policy_details(assignment.policy))
    return data


def serialize_effective_app_assignment(
    assignment: AppPolicyAssignmentRecord,
) -> dict[str, Any]:
    """Serialize one app assignment for an app effective-policy view."""

    data = {
        "assignment_id": assignment.id,
        "scope": "app",
        "policy_id": assignment.policy_id,
        "enabled": assignment.enabled,
        "created_at": assignment.created_at,
        "updated_at": assignment.updated_at,
    }
    data.update(_policy_details(assignment.policy))
    return data
