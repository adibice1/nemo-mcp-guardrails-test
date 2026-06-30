from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from nemo_mcp_guardrails.api.app_schemas import PolicyAssignmentResolutionRead
from nemo_mcp_guardrails.api.assignment_serializers import policy_label
from nemo_mcp_guardrails.api.policy_schemas import PolicyAssignmentResolutionCreate
from nemo_mcp_guardrails.database.connection import get_db
from nemo_mcp_guardrails.database.models import (
    AppPolicyAssignmentRecord,
    AppRecord,
    GlobalPolicyAssignmentRecord,
)
from nemo_mcp_guardrails.policy_service import resolve_or_create_policy


router = APIRouter(tags=["policy-assignment-resolution"])


def _resolution_response(
    *,
    resolution: str,
    scope: str,
    policy_id: int,
    assignment_id: int,
    display_name: str | None,
    label: str,
) -> dict[str, object]:
    return {
        "resolution": resolution,
        "scope": scope,
        "policy_id": policy_id,
        "assignment_id": assignment_id,
        "display_name": display_name,
        "policy_label": label,
    }


@router.post(
    "/apps/by-client-id/{client_id}/policy-assignments/resolve",
    response_model=PolicyAssignmentResolutionRead,
)
def resolve_app_policy_assignment(
    client_id: str,
    payload: PolicyAssignmentResolutionCreate,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """Resolve a reusable policy and ensure it applies to one app."""

    app = db.scalar(select(AppRecord).where(AppRecord.client_id == client_id))
    if app is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App not found",
        )

    try:
        resolved = resolve_or_create_policy(payload.policy, db)
        policy = resolved.policy

        global_assignment = db.scalar(
            select(GlobalPolicyAssignmentRecord).where(
                GlobalPolicyAssignmentRecord.policy_id == policy.id,
                GlobalPolicyAssignmentRecord.enabled.is_(True),
            )
        )
        if global_assignment is not None:
            db.commit()
            return _resolution_response(
                resolution="already_assigned",
                scope="global",
                policy_id=policy.id,
                assignment_id=global_assignment.id,
                display_name=global_assignment.display_name,
                label=policy_label(policy),
            )

        assignment = db.scalar(
            select(AppPolicyAssignmentRecord).where(
                AppPolicyAssignmentRecord.app_id == app.id,
                AppPolicyAssignmentRecord.policy_id == policy.id,
            )
        )
        if assignment is not None:
            was_enabled = assignment.enabled
            assignment.enabled = True
            db.commit()
            db.refresh(assignment)
            return _resolution_response(
                resolution="already_assigned" if was_enabled else "reused",
                scope="app",
                policy_id=policy.id,
                assignment_id=assignment.id,
                display_name=assignment.display_name,
                label=policy_label(policy),
            )

        assignment = AppPolicyAssignmentRecord(
            app_id=app.id,
            policy_id=policy.id,
            display_name=payload.display_name,
            enabled=True,
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return _resolution_response(
            resolution="created" if resolved.created else "reused",
            scope="app",
            policy_id=policy.id,
            assignment_id=assignment.id,
            display_name=assignment.display_name,
            label=policy_label(policy),
        )
    except (IntegrityError, ValueError) as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Policy could not be resolved and assigned",
        ) from error


@router.post(
    "/global-policy-assignments/resolve",
    response_model=PolicyAssignmentResolutionRead,
)
def resolve_global_policy_assignment(
    payload: PolicyAssignmentResolutionCreate,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """Resolve a reusable policy and ensure it is globally assigned."""

    try:
        resolved = resolve_or_create_policy(payload.policy, db)
        policy = resolved.policy
        assignment = db.scalar(
            select(GlobalPolicyAssignmentRecord).where(
                GlobalPolicyAssignmentRecord.policy_id == policy.id
            )
        )
        if assignment is not None:
            was_enabled = assignment.enabled
            assignment.enabled = True
            db.commit()
            db.refresh(assignment)
            return _resolution_response(
                resolution="already_assigned" if was_enabled else "reused",
                scope="global",
                policy_id=policy.id,
                assignment_id=assignment.id,
                display_name=assignment.display_name,
                label=policy_label(policy),
            )

        assignment = GlobalPolicyAssignmentRecord(
            policy_id=policy.id,
            display_name=payload.display_name,
            enabled=True,
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return _resolution_response(
            resolution="created" if resolved.created else "reused",
            scope="global",
            policy_id=policy.id,
            assignment_id=assignment.id,
            display_name=assignment.display_name,
            label=policy_label(policy),
        )
    except (IntegrityError, ValueError) as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Policy could not be resolved and assigned globally",
        ) from error


@router.put(
    "/apps/by-client-id/{client_id}/policy-assignments/{assignment_id}/resolve",
    response_model=PolicyAssignmentResolutionRead,
)
def edit_app_policy_assignment(
    client_id: str,
    assignment_id: int,
    payload: PolicyAssignmentResolutionCreate,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """Resolve edited behavior and switch only one app assignment."""

    app = db.scalar(select(AppRecord).where(AppRecord.client_id == client_id))
    if app is None:
        raise HTTPException(status_code=404, detail="App not found")

    current = db.scalar(
        select(AppPolicyAssignmentRecord).where(
            AppPolicyAssignmentRecord.id == assignment_id,
            AppPolicyAssignmentRecord.app_id == app.id,
        )
    )
    if current is None:
        raise HTTPException(status_code=404, detail="App policy assignment not found")

    try:
        resolved = resolve_or_create_policy(payload.policy, db)
        target_policy = resolved.policy
        if target_policy.id == current.policy_id:
            current.display_name = payload.display_name
            current.enabled = True
            db.commit()
            db.refresh(current)
            return _resolution_response(
                resolution="already_assigned",
                scope="app",
                policy_id=target_policy.id,
                assignment_id=current.id,
                display_name=current.display_name,
                label=policy_label(target_policy),
            )

        target_assignment = db.scalar(
            select(AppPolicyAssignmentRecord).where(
                AppPolicyAssignmentRecord.app_id == app.id,
                AppPolicyAssignmentRecord.policy_id == target_policy.id,
            )
        )
        if target_assignment is not None:
            target_assignment.enabled = True
            target_assignment.display_name = (
                payload.display_name or target_assignment.display_name
            )
            db.delete(current)
            db.commit()
            db.refresh(target_assignment)
            return _resolution_response(
                resolution="reused",
                scope="app",
                policy_id=target_policy.id,
                assignment_id=target_assignment.id,
                display_name=target_assignment.display_name,
                label=policy_label(target_policy),
            )

        current.policy_id = target_policy.id
        current.display_name = payload.display_name
        current.enabled = True
        db.commit()
        db.refresh(current)
        return _resolution_response(
            resolution="created" if resolved.created else "reused",
            scope="app",
            policy_id=target_policy.id,
            assignment_id=current.id,
            display_name=current.display_name,
            label=policy_label(target_policy),
        )
    except (IntegrityError, ValueError) as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="App policy assignment could not be edited",
        ) from error


@router.put(
    "/global-policy-assignments/{assignment_id}/resolve",
    response_model=PolicyAssignmentResolutionRead,
)
def edit_global_policy_assignment(
    assignment_id: int,
    payload: PolicyAssignmentResolutionCreate,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """Resolve edited behavior and switch only one global assignment."""

    current = db.get(GlobalPolicyAssignmentRecord, assignment_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Global assignment not found")

    try:
        resolved = resolve_or_create_policy(payload.policy, db)
        target_policy = resolved.policy
        if target_policy.id == current.policy_id:
            current.display_name = payload.display_name
            current.enabled = True
            db.commit()
            db.refresh(current)
            return _resolution_response(
                resolution="already_assigned",
                scope="global",
                policy_id=target_policy.id,
                assignment_id=current.id,
                display_name=current.display_name,
                label=policy_label(target_policy),
            )

        target_assignment = db.scalar(
            select(GlobalPolicyAssignmentRecord).where(
                GlobalPolicyAssignmentRecord.policy_id == target_policy.id
            )
        )
        if target_assignment is not None:
            target_assignment.enabled = True
            target_assignment.display_name = (
                payload.display_name or target_assignment.display_name
            )
            db.delete(current)
            db.commit()
            db.refresh(target_assignment)
            return _resolution_response(
                resolution="reused",
                scope="global",
                policy_id=target_policy.id,
                assignment_id=target_assignment.id,
                display_name=target_assignment.display_name,
                label=policy_label(target_policy),
            )

        current.policy_id = target_policy.id
        current.display_name = payload.display_name
        current.enabled = True
        db.commit()
        db.refresh(current)
        return _resolution_response(
            resolution="created" if resolved.created else "reused",
            scope="global",
            policy_id=target_policy.id,
            assignment_id=current.id,
            display_name=current.display_name,
            label=policy_label(target_policy),
        )
    except (IntegrityError, ValueError) as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Global policy assignment could not be edited",
        ) from error
