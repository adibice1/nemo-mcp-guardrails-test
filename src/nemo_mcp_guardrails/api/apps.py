import hashlib

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from nemo_mcp_guardrails.api.app_schemas import (
    AppCreate,
    AppPolicyAssignmentRead,
    AppRead,
    AppUpdate,
    PolicyAssignmentCreate,
    PolicyAssignmentUpdate,
)
from nemo_mcp_guardrails.database.connection import get_db
from nemo_mcp_guardrails.database.models import (
    AppPolicyAssignmentRecord,
    AppRecord,
    LlmConfigRecord,
    PolicyRecord,
)


router = APIRouter(prefix="/apps", tags=["apps"])


def hash_api_key(api_key: str) -> str:
    """Hash one client app API key before persistence."""

    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def _require_app(app_id: int, db: Session) -> AppRecord:
    """Return one app or raise a not-found response."""

    app = db.get(AppRecord, app_id)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App not found",
        )
    return app


def _require_policy(policy_id: int, db: Session) -> PolicyRecord:
    """Return one reusable policy or raise a not-found response."""

    policy = db.get(PolicyRecord, policy_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found",
        )
    return policy


def _validate_llm_config_ids(values: dict[str, object], db: Session) -> None:
    """Validate any provided main-agent or guardrail LLM references."""

    for field in ("main_llm_config_id", "guardrail_llm_config_id"):
        config_id = values.get(field)
        if config_id is not None and not db.get(LlmConfigRecord, config_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown {field}: {config_id}",
            )


@router.get("", response_model=list[AppRead])
def list_apps(db: Session = Depends(get_db)) -> list[AppRecord]:
    """Return all client apps."""

    return list(db.scalars(select(AppRecord).order_by(AppRecord.id)))


@router.post("", response_model=AppRead, status_code=status.HTTP_201_CREATED)
def create_app(payload: AppCreate, db: Session = Depends(get_db)) -> AppRecord:
    """Create one client app while storing only its API-key hash."""

    values = payload.model_dump(exclude={"api_key"})
    _validate_llm_config_ids(values, db)
    app = AppRecord(**values, api_key_hash=hash_api_key(payload.api_key))
    db.add(app)

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An app with this client_id already exists",
        ) from error

    db.refresh(app)
    return app


@router.get("/{app_id}", response_model=AppRead)
def get_app(app_id: int, db: Session = Depends(get_db)) -> AppRecord:
    """Return one client app by ID."""

    return _require_app(app_id, db)


@router.put("/{app_id}", response_model=AppRead)
def update_app(
    app_id: int,
    payload: AppUpdate,
    db: Session = Depends(get_db),
) -> AppRecord:
    """Update one client app."""

    app = _require_app(app_id, db)
    values = payload.model_dump(exclude_unset=True, exclude={"api_key"})
    _validate_llm_config_ids(values, db)

    for field, value in values.items():
        setattr(app, field, value)

    if payload.api_key is not None:
        app.api_key_hash = hash_api_key(payload.api_key)

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An app with this client_id already exists",
        ) from error

    db.refresh(app)
    return app


@router.delete("/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_app(app_id: int, db: Session = Depends(get_db)) -> None:
    """Delete one client app and its dependent assignments."""

    app = _require_app(app_id, db)
    db.delete(app)
    db.commit()


@router.get(
    "/{app_id}/policy-assignments",
    response_model=list[AppPolicyAssignmentRead],
)
def list_app_policy_assignments(
    app_id: int,
    db: Session = Depends(get_db),
) -> list[AppPolicyAssignmentRecord]:
    """Return all policy assignments belonging to one app."""

    _require_app(app_id, db)
    return list(
        db.scalars(
            select(AppPolicyAssignmentRecord)
            .where(AppPolicyAssignmentRecord.app_id == app_id)
            .order_by(AppPolicyAssignmentRecord.id)
        )
    )


@router.post(
    "/{app_id}/policy-assignments",
    response_model=AppPolicyAssignmentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_app_policy_assignment(
    app_id: int,
    payload: PolicyAssignmentCreate,
    db: Session = Depends(get_db),
) -> AppPolicyAssignmentRecord:
    """Assign one reusable policy to one client app."""

    _require_app(app_id, db)
    _require_policy(payload.policy_id, db)
    assignment = AppPolicyAssignmentRecord(
        app_id=app_id,
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
            detail="This policy is already assigned to the app",
        ) from error

    db.refresh(assignment)
    return assignment


@router.put(
    "/{app_id}/policy-assignments/{assignment_id}",
    response_model=AppPolicyAssignmentRead,
)
def update_app_policy_assignment(
    app_id: int,
    assignment_id: int,
    payload: PolicyAssignmentUpdate,
    db: Session = Depends(get_db),
) -> AppPolicyAssignmentRecord:
    """Enable or disable one app-specific policy assignment."""

    assignment = db.scalar(
        select(AppPolicyAssignmentRecord).where(
            AppPolicyAssignmentRecord.id == assignment_id,
            AppPolicyAssignmentRecord.app_id == app_id,
        )
    )
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App policy assignment not found",
        )

    assignment.enabled = payload.enabled
    db.commit()
    db.refresh(assignment)
    return assignment


@router.delete(
    "/{app_id}/policy-assignments/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_app_policy_assignment(
    app_id: int,
    assignment_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Delete one app-specific policy assignment."""

    assignment = db.scalar(
        select(AppPolicyAssignmentRecord).where(
            AppPolicyAssignmentRecord.id == assignment_id,
            AppPolicyAssignmentRecord.app_id == app_id,
        )
    )
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App policy assignment not found",
        )

    db.delete(assignment)
    db.commit()
