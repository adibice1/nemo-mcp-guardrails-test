from dataclasses import dataclass
import json
import re
import unicodedata

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from nemo_mcp_guardrails.api.policy_schemas import PolicyCreate
from nemo_mcp_guardrails.database.models import (
    ConnectorActionRecord,
    ConnectorRecord,
    ConnectorResourceRecord,
    ConnectorToolMappingRecord,
    AppPolicyAssignmentRecord,
    GlobalPolicyAssignmentRecord,
    PolicyRecord,
)
from nemo_mcp_guardrails.policy_rule_service import refresh_compiled_policy_rule


@dataclass(frozen=True)
class ResolvedPolicy:
    """Return a reusable policy and whether it was newly created."""

    policy: PolicyRecord
    created: bool


@dataclass(frozen=True)
class PolicyConsolidation:
    """Describe one duplicate policy merged into a canonical policy."""

    canonical_policy_id: int
    removed_policy_id: int
    reassigned_app_assignments: int
    merged_app_assignments: int
    global_assignment_merged: bool


RESOURCE_PLURALS = {
    "branch": "branches",
    "issue": "issues",
    "pull request": "pull requests",
    "repository": "repositories",
}


def canonicalize_custom_resource(
    value: object,
    resource: str | None,
) -> str:
    """Convert equivalent custom-resource phrases into one identity."""

    text = unicodedata.normalize("NFKC", str(value)).casefold()
    text = re.sub(r'''["'`]''', "", text)
    text = re.sub(r"\s+", " ", text).strip()

    resource_name = (resource or "").strip().casefold().replace("_", " ")
    resource_names = {
        resource_name,
        RESOURCE_PLURALS.get(resource_name, f"{resource_name}s"),
    }
    for candidate in sorted(resource_names, key=len, reverse=True):
        if candidate:
            text = re.sub(rf"^{re.escape(candidate)}\s+", "", text)

    text = re.sub(r"^(?:name|named|called|titled)\s+", "", text)
    return text.strip(" .")


def canonicalize_policy_conditions(
    conditions: dict[str, object] | None,
    resource: str | None,
) -> dict[str, object]:
    """Return conditions with a canonical custom-resource identity."""

    normalized = dict(conditions or {})
    custom_resource = normalized.get("custom_resource")
    if custom_resource is None:
        return normalized

    canonical = canonicalize_custom_resource(custom_resource, resource)
    if canonical:
        normalized["custom_resource"] = canonical
    else:
        normalized.pop("custom_resource", None)
    return normalized


def resolve_policy_references(policy: PolicyRecord, db: Session) -> None:
    """Resolve readable connector metadata into normalized foreign keys."""

    if policy.category:
        policy.category = policy.category.strip().lower()

    if policy.policy_type == "input":
        missing_fields = [
            field
            for field in ("connector", "action", "resource")
            if not getattr(policy, field)
        ]
        if missing_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Input policy is missing required fields: "
                    + ", ".join(missing_fields)
                ),
            )

    if policy.policy_type == "output" and not policy.connector:
        policy.connector = "global"

    if not policy.connector:
        policy.connector_id = None
        policy.action_id = None
        policy.resource_id = None
        return

    connector_name = policy.connector.strip().lower()
    connector = db.scalar(
        select(ConnectorRecord).where(ConnectorRecord.name == connector_name)
    )
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown connector: {policy.connector}",
        )

    policy.connector = connector.name
    policy.connector_id = connector.id
    policy.normalized_connector = connector

    if policy.action:
        action_name = policy.action.strip().lower()
        action = db.scalar(
            select(ConnectorActionRecord).where(
                ConnectorActionRecord.connector_id == connector.id,
                ConnectorActionRecord.name == action_name,
            )
        )
        if not action:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Unknown action '{policy.action}' "
                    f"for connector '{connector.name}'"
                ),
            )
        policy.action = action.name
        policy.action_id = action.id
        policy.normalized_action = action
    else:
        policy.action_id = None
        policy.normalized_action = None

    if policy.resource:
        resource_name = policy.resource.strip().lower()
        resource = db.scalar(
            select(ConnectorResourceRecord).where(
                ConnectorResourceRecord.connector_id == connector.id,
                ConnectorResourceRecord.name == resource_name,
            )
        )
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Unknown resource '{policy.resource}' "
                    f"for connector '{connector.name}'"
                ),
            )
        policy.resource = resource.name
        policy.resource_id = resource.id
        policy.normalized_resource = resource
    else:
        policy.resource_id = None
        policy.normalized_resource = None

    policy.conditions = canonicalize_policy_conditions(
        policy.conditions,
        policy.resource,
    )

    if (
        policy.policy_type == "input"
        and policy.action_id is not None
        and policy.resource_id is not None
    ):
        tool_mapping = db.scalar(
            select(ConnectorToolMappingRecord).where(
                ConnectorToolMappingRecord.connector_id == policy.connector_id,
                ConnectorToolMappingRecord.action_id == policy.action_id,
                ConnectorToolMappingRecord.resource_id == policy.resource_id,
                ConnectorToolMappingRecord.enabled.is_(True),
            )
        )
        if not tool_mapping:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Unsupported policy combination: "
                    f"{policy.connector} + {policy.action} + {policy.resource}"
                ),
            )


def find_equivalent_policy(
    candidate: PolicyRecord,
    db: Session,
    *,
    exclude_policy_id: int | None = None,
) -> PolicyRecord | None:
    """Find the oldest enabled policy with equivalent enforcement behavior."""

    statement = select(PolicyRecord).where(
        PolicyRecord.policy_type == candidate.policy_type,
        PolicyRecord.connector_id == candidate.connector_id,
        PolicyRecord.action_id == candidate.action_id,
        PolicyRecord.resource_id == candidate.resource_id,
        PolicyRecord.category == candidate.category,
        PolicyRecord.effect == candidate.effect,
        PolicyRecord.priority == candidate.priority,
        PolicyRecord.enabled == candidate.enabled,
    )
    if candidate.policy_type == "output":
        statement = statement.where(
            PolicyRecord.description == candidate.description
        )
    if exclude_policy_id is not None:
        statement = statement.where(PolicyRecord.id != exclude_policy_id)

    candidate_conditions = canonicalize_policy_conditions(
        candidate.conditions,
        candidate.resource,
    )
    for policy in db.scalars(statement.order_by(PolicyRecord.id)):
        if canonicalize_policy_conditions(
            policy.conditions,
            policy.resource,
        ) == candidate_conditions:
            return policy
    return None


def policy_equivalence_key(policy: PolicyRecord) -> tuple[object, ...]:
    """Return a stable in-memory key for duplicate consolidation."""

    output_description = (
        (policy.description or "").strip()
        if policy.policy_type == "output"
        else None
    )
    return (
        policy.policy_type,
        policy.connector_id,
        policy.action_id,
        policy.resource_id,
        policy.category,
        output_description,
        policy.effect,
        policy.priority,
        json.dumps(
            canonicalize_policy_conditions(policy.conditions, policy.resource),
            sort_keys=True,
            separators=(",", ":"),
        ),
        policy.enabled,
    )


def consolidate_equivalent_policies(db: Session) -> list[PolicyConsolidation]:
    """Merge legacy duplicate definitions without losing assignments."""

    groups: dict[tuple[object, ...], list[PolicyRecord]] = {}
    for policy in db.scalars(select(PolicyRecord).order_by(PolicyRecord.id)):
        policy.conditions = canonicalize_policy_conditions(
            policy.conditions,
            policy.resource,
        )
        groups.setdefault(policy_equivalence_key(policy), []).append(policy)

    results: list[PolicyConsolidation] = []
    for policies in groups.values():
        if len(policies) < 2:
            continue

        canonical = policies[0]
        for duplicate in policies[1:]:
            if (
                canonical.policy_type == "input"
                and not (canonical.description or "").strip()
                and (duplicate.description or "").strip()
            ):
                canonical.description = duplicate.description

            canonical_by_app = {
                assignment.app_id: assignment
                for assignment in db.scalars(
                    select(AppPolicyAssignmentRecord).where(
                        AppPolicyAssignmentRecord.policy_id == canonical.id
                    )
                )
            }
            reassigned_app_assignments = 0
            merged_app_assignments = 0
            duplicate_assignments = list(
                db.scalars(
                    select(AppPolicyAssignmentRecord).where(
                        AppPolicyAssignmentRecord.policy_id == duplicate.id
                    )
                )
            )
            for assignment in duplicate_assignments:
                existing = canonical_by_app.get(assignment.app_id)
                if existing is None:
                    assignment.policy_id = canonical.id
                    canonical_by_app[assignment.app_id] = assignment
                    reassigned_app_assignments += 1
                    continue

                existing.enabled = existing.enabled or assignment.enabled
                if not existing.display_name and assignment.display_name:
                    existing.display_name = assignment.display_name
                db.delete(assignment)
                merged_app_assignments += 1

            canonical_global = db.scalar(
                select(GlobalPolicyAssignmentRecord).where(
                    GlobalPolicyAssignmentRecord.policy_id == canonical.id
                )
            )
            duplicate_global = db.scalar(
                select(GlobalPolicyAssignmentRecord).where(
                    GlobalPolicyAssignmentRecord.policy_id == duplicate.id
                )
            )
            global_assignment_merged = False
            if duplicate_global is not None:
                if canonical_global is None:
                    duplicate_global.policy_id = canonical.id
                else:
                    canonical_global.enabled = (
                        canonical_global.enabled or duplicate_global.enabled
                    )
                    if (
                        not canonical_global.display_name
                        and duplicate_global.display_name
                    ):
                        canonical_global.display_name = duplicate_global.display_name
                    db.delete(duplicate_global)
                    global_assignment_merged = True

            db.flush()
            duplicate_id = duplicate.id
            db.delete(duplicate)
            db.flush()
            results.append(
                PolicyConsolidation(
                    canonical_policy_id=canonical.id,
                    removed_policy_id=duplicate_id,
                    reassigned_app_assignments=reassigned_app_assignments,
                    merged_app_assignments=merged_app_assignments,
                    global_assignment_merged=global_assignment_merged,
                )
            )

    return results


def resolve_or_create_policy(payload: PolicyCreate, db: Session) -> ResolvedPolicy:
    """Reuse an equivalent policy or create and compile a new definition."""

    candidate = PolicyRecord(**payload.model_dump())
    resolve_policy_references(candidate, db)
    existing = find_equivalent_policy(candidate, db)
    if existing is not None:
        return ResolvedPolicy(policy=existing, created=False)

    db.add(candidate)
    db.flush()
    refresh_compiled_policy_rule(db, candidate)
    return ResolvedPolicy(policy=candidate, created=True)
