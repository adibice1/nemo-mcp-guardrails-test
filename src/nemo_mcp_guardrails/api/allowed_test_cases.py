from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from nemo_mcp_guardrails.api.policy_schemas import (
    AllowedTestCaseCreate,
    AllowedTestCaseRead,
    AllowedTestCaseUpdate,
)
from nemo_mcp_guardrails.database.connection import get_db
from nemo_mcp_guardrails.database.models import AllowedTestCaseRecord


router = APIRouter(prefix="/allowed-test-cases", tags=["allowed-test-cases"])


@router.get("", response_model=list[AllowedTestCaseRead])
def list_allowed_test_cases(
    db: Session = Depends(get_db),
) -> list[AllowedTestCaseRecord]:
    """Return all stored allowed test cases."""

    return list(
        db.scalars(select(AllowedTestCaseRecord).order_by(AllowedTestCaseRecord.id))
    )


@router.get("/{test_case_id}", response_model=AllowedTestCaseRead)
def get_allowed_test_case(
    test_case_id: int,
    db: Session = Depends(get_db),
) -> AllowedTestCaseRecord:
    """Return one stored allowed test case by ID."""

    test_case = db.get(AllowedTestCaseRecord, test_case_id)
    if not test_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Allowed test case not found",
        )

    return test_case


@router.post(
    "",
    response_model=AllowedTestCaseRead,
    status_code=status.HTTP_201_CREATED,
)
def create_allowed_test_case(
    payload: AllowedTestCaseCreate,
    db: Session = Depends(get_db),
) -> AllowedTestCaseRecord:
    """Create one allowed test case."""

    test_case = AllowedTestCaseRecord(**payload.model_dump())
    db.add(test_case)
    db.commit()
    db.refresh(test_case)
    return test_case


@router.put("/{test_case_id}", response_model=AllowedTestCaseRead)
def update_allowed_test_case(
    test_case_id: int,
    payload: AllowedTestCaseUpdate,
    db: Session = Depends(get_db),
) -> AllowedTestCaseRecord:
    """Update one allowed test case."""

    test_case = db.get(AllowedTestCaseRecord, test_case_id)
    if not test_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Allowed test case not found",
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(test_case, field, value)

    db.commit()
    db.refresh(test_case)
    return test_case


@router.delete("/{test_case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_allowed_test_case(
    test_case_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Delete one allowed test case."""

    test_case = db.get(AllowedTestCaseRecord, test_case_id)
    if not test_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Allowed test case not found",
        )

    db.delete(test_case)
    db.commit()
