from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from nemo_mcp_guardrails.app_auth import hash_api_key
from nemo_mcp_guardrails.api.assignment_serializers import (
    serialize_app,
    serialize_app_policy_assignment,
)
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


def _require_app(app_id: int, db: Session) -> AppRecord:
    """Return one app or raise a not-found response."""

    app = db.get(AppRecord, app_id)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App not found",
        )
    return app


def _unique_policy_ids(policy_ids: list[int]) -> list[int]:
    """Return unique policy IDs while preserving request order."""

    return list(dict.fromkeys(policy_ids))


def _require_policies(policy_ids: list[int], db: Session) -> dict[int, PolicyRecord]:
    """Return policies keyed by ID or raise for missing IDs."""

    unique_ids = _unique_policy_ids(policy_ids)
    policies = list(
        db.scalars(select(PolicyRecord).where(PolicyRecord.id.in_(unique_ids)))
    )
    policies_by_id = {policy.id: policy for policy in policies}
    missing_ids = [policy_id for policy_id in unique_ids if policy_id not in policies_by_id]
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy IDs not found: {missing_ids}",
        )
    return policies_by_id


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
def list_apps(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    """Return all client apps."""

    apps = list(db.scalars(select(AppRecord).order_by(AppRecord.id)))
    return [serialize_app(app) for app in apps]


@router.post("", response_model=AppRead, status_code=status.HTTP_201_CREATED)
def create_app(payload: AppCreate, db: Session = Depends(get_db)) -> dict[str, object]:
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
    return serialize_app(app)


@router.get("/{app_id}", response_model=AppRead)
def get_app(app_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    """Return one client app by ID."""

    return serialize_app(_require_app(app_id, db))


@router.put("/{app_id}", response_model=AppRead)
def update_app(
    app_id: int,
    payload: AppUpdate,
    db: Session = Depends(get_db),
) -> dict[str, object]:
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
    return serialize_app(app)


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
) -> list[dict[str, object]]:
    """Return all policy assignments belonging to one app."""

    _require_app(app_id, db)
    assignments = list(
        db.scalars(
            select(AppPolicyAssignmentRecord)
            .where(AppPolicyAssignmentRecord.app_id == app_id)
            .order_by(AppPolicyAssignmentRecord.id)
        )
    )
    return [serialize_app_policy_assignment(assignment) for assignment in assignments]


@router.post(
    "/{app_id}/policy-assignments",
    response_model=list[AppPolicyAssignmentRead],
    status_code=status.HTTP_201_CREATED,
)
def create_app_policy_assignment(
    app_id: int,
    payload: PolicyAssignmentCreate,
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    """Assign one or more reusable policies to one client app."""

    _require_app(app_id, db)
    policy_ids = _unique_policy_ids(payload.policy_ids)
    _require_policies(policy_ids, db)

    existing_assignments = list(
        db.scalars(
            select(AppPolicyAssignmentRecord).where(
                AppPolicyAssignmentRecord.app_id == app_id,
                AppPolicyAssignmentRecord.policy_id.in_(policy_ids),
            )
        )
    )
    assignments_by_policy_id = {
        assignment.policy_id: assignment for assignment in existing_assignments
    }
    assignments: list[AppPolicyAssignmentRecord] = []

    for policy_id in policy_ids:
        assignment = assignments_by_policy_id.get(policy_id)
        if assignment is None:
            assignment = AppPolicyAssignmentRecord(
                app_id=app_id,
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
            detail="One or more policies could not be assigned to the app",
        ) from error

    for assignment in assignments:
        db.refresh(assignment)
    return [serialize_app_policy_assignment(assignment) for assignment in assignments]


@router.put(
    "/{app_id}/policy-assignments/{assignment_id}",
    response_model=AppPolicyAssignmentRead,
)
def update_app_policy_assignment(
    app_id: int,
    assignment_id: int,
    payload: PolicyAssignmentUpdate,
    db: Session = Depends(get_db),
) -> dict[str, object]:
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
    return serialize_app_policy_assignment(assignment)


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
