from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from nemo_mcp_guardrails.api.assignment_serializers import (
    serialize_global_policy_assignment,
)
from nemo_mcp_guardrails.api.app_schemas import (
    GlobalPolicyAssignmentRead,
    PolicyAssignmentCreate,
    PolicyAssignmentUpdate,
)
from nemo_mcp_guardrails.database.connection import get_db
from nemo_mcp_guardrails.database.models import (
    GlobalPolicyAssignmentRecord,
    PolicyRecord,
)


router = APIRouter(
    prefix="/global-policy-assignments",
    tags=["global-policy-assignments"],
)


@router.get("", response_model=list[GlobalPolicyAssignmentRead])
def list_global_policy_assignments(
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    """Return all mandatory global policy assignments."""

    assignments = list(
        db.scalars(
            select(GlobalPolicyAssignmentRecord).order_by(
                GlobalPolicyAssignmentRecord.id
            )
        )
    )
    return [
        serialize_global_policy_assignment(assignment) for assignment in assignments
    ]


def _unique_policy_ids(policy_ids: list[int]) -> list[int]:
    """Return unique policy IDs while preserving request order."""

    return list(dict.fromkeys(policy_ids))


def _require_policies(policy_ids: list[int], db: Session) -> None:
    """Raise a not-found response if any requested policy ID is missing."""

    unique_ids = _unique_policy_ids(policy_ids)
    existing_ids = set(
        db.scalars(select(PolicyRecord.id).where(PolicyRecord.id.in_(unique_ids)))
    )
    missing_ids = [policy_id for policy_id in unique_ids if policy_id not in existing_ids]
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy IDs not found: {missing_ids}",
        )


@router.post(
    "",
    response_model=list[GlobalPolicyAssignmentRead],
    status_code=status.HTTP_201_CREATED,
)
def create_global_policy_assignment(
    payload: PolicyAssignmentCreate,
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    """Apply one or more reusable policies globally."""

    policy_ids = _unique_policy_ids(payload.policy_ids)
    _require_policies(policy_ids, db)

    existing_assignments = list(
        db.scalars(
            select(GlobalPolicyAssignmentRecord).where(
                GlobalPolicyAssignmentRecord.policy_id.in_(policy_ids)
            )
        )
    )
    assignments_by_policy_id = {
        assignment.policy_id: assignment for assignment in existing_assignments
    }
    assignments: list[GlobalPolicyAssignmentRecord] = []

    for policy_id in policy_ids:
        assignment = assignments_by_policy_id.get(policy_id)
        if assignment is None:
            assignment = GlobalPolicyAssignmentRecord(
                policy_id=policy_id,
                enabled=payload.enabled,
            )
            db.add(assignment)
        else:
            assignment.enabled = payload.enabled
        assignments.append(assignment)

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="One or more policies could not be assigned globally",
        ) from error

    for assignment in assignments:
        db.refresh(assignment)
    return [
        serialize_global_policy_assignment(assignment) for assignment in assignments
    ]


@router.put(
    "/{assignment_id}",
    response_model=GlobalPolicyAssignmentRead,
)
def update_global_policy_assignment(
    assignment_id: int,
    payload: PolicyAssignmentUpdate,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """Enable or disable one mandatory global assignment."""

    assignment = db.get(GlobalPolicyAssignmentRecord, assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Global policy assignment not found",
        )

    assignment.enabled = payload.enabled
    db.commit()
    db.refresh(assignment)
    return serialize_global_policy_assignment(assignment)


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_global_policy_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Delete one mandatory global policy assignment."""

    assignment = db.get(GlobalPolicyAssignmentRecord, assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Global policy assignment not found",
        )

    db.delete(assignment)
    db.commit()
