from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

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
) -> list[GlobalPolicyAssignmentRecord]:
    """Return all mandatory global policy assignments."""

    return list(
        db.scalars(
            select(GlobalPolicyAssignmentRecord).order_by(
                GlobalPolicyAssignmentRecord.id
            )
        )
    )


@router.post(
    "",
    response_model=GlobalPolicyAssignmentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_global_policy_assignment(
    payload: PolicyAssignmentCreate,
    db: Session = Depends(get_db),
) -> GlobalPolicyAssignmentRecord:
    """Apply one reusable policy globally."""

    if not db.get(PolicyRecord, payload.policy_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found",
        )

    assignment = GlobalPolicyAssignmentRecord(
        policy_id=payload.policy_id,
        enabled=payload.enabled,
    )
    db.add(assignment)

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This policy already has a global assignment",
        ) from error

    db.refresh(assignment)
    return assignment


@router.put(
    "/{assignment_id}",
    response_model=GlobalPolicyAssignmentRead,
)
def update_global_policy_assignment(
    assignment_id: int,
    payload: PolicyAssignmentUpdate,
    db: Session = Depends(get_db),
) -> GlobalPolicyAssignmentRecord:
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
    return assignment


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
