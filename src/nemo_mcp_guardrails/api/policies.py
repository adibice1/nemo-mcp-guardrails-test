from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from nemo_mcp_guardrails.api.policy_schemas import (
    PolicyCreate,
    PolicyRead,
    PolicyUpdate,
)
from nemo_mcp_guardrails.database.connection import get_db
from nemo_mcp_guardrails.database.models import PolicyRecord


router = APIRouter(prefix="/policies", tags=["policies"])


@router.get("", response_model=list[PolicyRead])
def list_policies(db: Session = Depends(get_db)) -> list[PolicyRecord]:
    """Return all stored policies."""

    return list(db.scalars(select(PolicyRecord).order_by(PolicyRecord.id)))


@router.get("/{policy_id}", response_model=PolicyRead)
def get_policy(policy_id: int, db: Session = Depends(get_db)) -> PolicyRecord:
    """Return one stored policy by ID."""

    policy = db.get(PolicyRecord, policy_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found",
        )

    return policy


@router.post("", response_model=PolicyRead, status_code=status.HTTP_201_CREATED)
def create_policy(
    payload: PolicyCreate,
    db: Session = Depends(get_db),
) -> PolicyRecord:
    """Create one policy record."""

    policy = PolicyRecord(**payload.model_dump())
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


@router.put("/{policy_id}", response_model=PolicyRead)
def update_policy(
    policy_id: int,
    payload: PolicyUpdate,
    db: Session = Depends(get_db),
) -> PolicyRecord:
    """Update one policy record."""

    policy = db.get(PolicyRecord, policy_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found",
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(policy, field, value)

    db.commit()
    db.refresh(policy)
    return policy


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_policy(policy_id: int, db: Session = Depends(get_db)) -> None:
    """Delete one policy record."""

    policy = db.get(PolicyRecord, policy_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found",
        )

    db.delete(policy)
    db.commit()
