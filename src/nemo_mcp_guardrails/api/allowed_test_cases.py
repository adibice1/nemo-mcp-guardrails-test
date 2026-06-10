from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from nemo_mcp_guardrails.api.policy_schemas import (
    AllowedTestCaseCreate,
    AllowedTestCaseRead,
    AllowedTestCaseUpdate,
)
from nemo_mcp_guardrails.database.connection import get_db
from nemo_mcp_guardrails.database.models import (
    AllowedTestCaseExpectedToolRecord,
    AllowedTestCaseRecord,
    ToolMappingRecord,
)


router = APIRouter(prefix="/allowed-test-cases", tags=["allowed-test-cases"])


EXPECTED_TOOL_OPTIONS = (
    selectinload(AllowedTestCaseRecord.expected_tool_links).selectinload(
        AllowedTestCaseExpectedToolRecord.tool_mapping
    ),
)


def _resolve_tool_mappings(
    tool_names: list[str],
    db: Session,
) -> tuple[list[str], list[ToolMappingRecord]]:
    """Resolve readable tool names into enabled normalized mappings."""

    normalized_names = sorted(
        {
            tool_name.strip()
            for tool_name in tool_names
            if tool_name.strip()
        }
    )

    if not normalized_names:
        return [], []

    mappings = list(
        db.scalars(
            select(ToolMappingRecord)
            .where(
                ToolMappingRecord.tool_name.in_(normalized_names),
                ToolMappingRecord.enabled.is_(True),
            )
            .order_by(ToolMappingRecord.id)
        )
    )

    resolved_names = {mapping.tool_name for mapping in mappings}
    unknown_names = sorted(set(normalized_names) - resolved_names)

    if unknown_names:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unknown or disabled tools: " + ", ".join(unknown_names),
        )

    return normalized_names, mappings


def _replace_expected_tool_links(
    test_case: AllowedTestCaseRecord,
    tool_names: list[str],
    db: Session,
) -> None:
    """Replace normalized expected-tool links for one allowed test."""

    normalized_names, mappings = _resolve_tool_mappings(tool_names, db)

    test_case.expected_tools = ",".join(normalized_names) or None
    test_case.expected_tool_links = [
        AllowedTestCaseExpectedToolRecord(tool_mapping=mapping)
        for mapping in mappings
    ]


@router.get("", response_model=list[AllowedTestCaseRead])
def list_allowed_test_cases(
    db: Session = Depends(get_db),
) -> list[AllowedTestCaseRecord]:
    """Return all stored allowed test cases."""

    return list(
        db.scalars(
            select(AllowedTestCaseRecord)
            .options(*EXPECTED_TOOL_OPTIONS)
            .order_by(AllowedTestCaseRecord.id)
        )
    )


@router.get("/{test_case_id}", response_model=AllowedTestCaseRead)
def get_allowed_test_case(
    test_case_id: int,
    db: Session = Depends(get_db),
) -> AllowedTestCaseRecord:
    """Return one stored allowed test case by ID."""

    test_case = db.scalar(
        select(AllowedTestCaseRecord)
        .options(*EXPECTED_TOOL_OPTIONS)
        .where(AllowedTestCaseRecord.id == test_case_id)
    )
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

    values = payload.model_dump(exclude={"expected_tools"})
    test_case = AllowedTestCaseRecord(**values)
    _replace_expected_tool_links(test_case, payload.expected_tools, db)
    db.add(test_case)
    db.commit()
    return db.scalar(
        select(AllowedTestCaseRecord)
        .options(*EXPECTED_TOOL_OPTIONS)
        .where(AllowedTestCaseRecord.id == test_case.id)
    )


@router.put("/{test_case_id}", response_model=AllowedTestCaseRead)
def update_allowed_test_case(
    test_case_id: int,
    payload: AllowedTestCaseUpdate,
    db: Session = Depends(get_db),
) -> AllowedTestCaseRecord:
    """Update one allowed test case."""

    test_case = db.scalar(
        select(AllowedTestCaseRecord)
        .options(*EXPECTED_TOOL_OPTIONS)
        .where(AllowedTestCaseRecord.id == test_case_id)
    )
    if not test_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Allowed test case not found",
        )

    updates = payload.model_dump(exclude_unset=True)
    expected_tools = updates.pop("expected_tools", None)

    for field, value in updates.items():
        setattr(test_case, field, value)

    if expected_tools is not None:
        _replace_expected_tool_links(test_case, expected_tools, db)

    db.commit()
    return db.scalar(
        select(AllowedTestCaseRecord)
        .options(*EXPECTED_TOOL_OPTIONS)
        .where(AllowedTestCaseRecord.id == test_case.id)
    )


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
