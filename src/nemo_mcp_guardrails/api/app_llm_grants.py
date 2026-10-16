"""App-scoped model options and administrator-managed grant revocation."""

import re
from collections.abc import Iterator

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from nemo_mcp_guardrails.api.app_schemas import AppLlmGrantRead, AppLlmGrantWrite, AppLlmOptions
from nemo_mcp_guardrails.database.connection import get_db
from nemo_mcp_guardrails.database.models import AppLlmGrantRecord, AppRecord, LlmConfigRecord
from nemo_mcp_guardrails.llm_access import LlmAccessError, LlmPurpose, validate_llm_choice
from nemo_mcp_guardrails.management_permissions import require_app_route_access, require_system_admin


router = APIRouter(prefix="/apps", tags=["app-llm-grants"],
                   dependencies=[Depends(require_app_route_access)])


def grant_db(db: Session = Depends(get_db)) -> Iterator[Session]:
    """Keep grant-store failures generic and roll back failed mutations."""

    try:
        yield db
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(503, "LLM grant configuration is unavailable.") from error


def client_app_id(client_id: str, db: Session = Depends(grant_db)) -> int:
    """Resolve the authorized client-ID path without accepting query aliases."""

    app_id = db.scalar(select(AppRecord.id).where(AppRecord.client_id == client_id))
    if app_id is None:
        raise HTTPException(404, "App not found")
    return app_id


def _config_id(config_ref: str) -> int | None:
    """Accept an exact default marker or a positive PostgreSQL integer ID."""

    if config_ref == "default":
        return None
    if not re.fullmatch(r"[1-9][0-9]{0,9}", config_ref) or int(config_ref) > 2147483647:
        raise HTTPException(400, "Use a positive configuration ID or default.")
    return int(config_ref)


def _grant_read(grant: AppLlmGrantRecord, config: LlmConfigRecord | None) -> dict:
    """Serialize safe grant metadata for both reads and writes."""

    return {
        "id": grant.id, "app_id": grant.app_id, "purpose": grant.purpose,
        "llm_config_id": grant.llm_config_id, "enabled": grant.enabled,
        "config_name": config.name if config else "Environment default",
        "config_enabled": config.enabled if config else grant.llm_config_id is None,
        "created_at": grant.created_at, "updated_at": grant.updated_at,
    }


def _read_grants(app_id: int, db: Session) -> list[dict]:
    """List grants, including revoked ones, without credential references."""

    rows = db.execute(select(AppLlmGrantRecord, LlmConfigRecord).outerjoin(
        LlmConfigRecord, LlmConfigRecord.id == AppLlmGrantRecord.llm_config_id,
    ).where(AppLlmGrantRecord.app_id == app_id).order_by(AppLlmGrantRecord.id))
    return [_grant_read(grant, config) for grant, config in rows]


def _options(app_id: int, purpose: LlmPurpose, db: Session) -> dict:
    """Offer only granted and currently valid choices for the requested purpose."""

    rows = db.execute(select(AppLlmGrantRecord, LlmConfigRecord).outerjoin(
        LlmConfigRecord, LlmConfigRecord.id == AppLlmGrantRecord.llm_config_id,
    ).where(AppLlmGrantRecord.app_id == app_id, AppLlmGrantRecord.purpose == purpose,
            AppLlmGrantRecord.enabled.is_(True)).order_by(LlmConfigRecord.name))
    configs = []
    default_allowed = False
    for grant, config in rows:
        if grant.llm_config_id is not None and config is None:
            continue
        try:
            validate_llm_choice(config)
        except LlmAccessError:
            continue
        if config is None:
            default_allowed = True
        else:
            configs.append(config)
    return {"purpose": purpose, "environment_default_allowed": default_allowed, "configs": configs}


def _write_grant(
    app_id: int, purpose: LlmPurpose, config_ref: str, db: Session,
    payload: AppLlmGrantWrite | None = None,
) -> dict:
    """Upsert an explicit admin decision or revoke while retaining its row."""

    config_id = _config_id(config_ref)
    config = db.get(LlmConfigRecord, config_id) if config_id is not None else None
    if config_id is not None and config is None:
        raise HTTPException(404, "LLM configuration not found")
    enabled = payload.enabled if payload is not None else False
    if enabled:
        try:
            validate_llm_choice(config)
        except LlmAccessError as error:
            raise HTTPException(400, "LLM configuration is not available for approval.") from error
    grant = db.scalars(select(AppLlmGrantRecord).where(
        AppLlmGrantRecord.app_id == app_id, AppLlmGrantRecord.purpose == purpose,
        AppLlmGrantRecord.llm_config_id == config_id,
    ).with_for_update()).one_or_none()
    if grant is None:
        if payload is None:
            raise HTTPException(404, "LLM grant not found")
        grant = AppLlmGrantRecord(app_id=app_id, purpose=purpose, llm_config_id=config_id)
        db.add(grant)
    grant.enabled = enabled
    db.commit()
    db.refresh(grant)
    return _grant_read(grant, config)


@router.get("/{app_id}/llm-grants", response_model=list[AppLlmGrantRead])
def list_grants(app_id: int, db: Session = Depends(grant_db)) -> list[dict]:
    """Read grants for an app the management user can access."""
    return _read_grants(app_id, db)


@router.get("/by-client-id/{client_id}/llm-grants", response_model=list[AppLlmGrantRead])
def list_client_grants(app_id: int = Depends(client_app_id), db: Session = Depends(grant_db)) -> list[dict]:
    """Read the same app grants through its client-ID alias."""
    return _read_grants(app_id, db)


@router.get("/{app_id}/llm-options", response_model=AppLlmOptions)
def list_options(app_id: int, purpose: LlmPurpose, db: Session = Depends(grant_db)) -> dict:
    """Read purpose-specific model choices for an authorized app."""
    return _options(app_id, purpose, db)


@router.get("/by-client-id/{client_id}/llm-options", response_model=AppLlmOptions)
def list_client_options(
    purpose: LlmPurpose, app_id: int = Depends(client_app_id), db: Session = Depends(grant_db),
) -> dict:
    """Read the same purpose-specific choices through a client-ID alias."""
    return _options(app_id, purpose, db)


@router.put("/{app_id}/llm-grants/{purpose}/{config_ref}", response_model=AppLlmGrantRead,
            dependencies=[Depends(require_system_admin)])
def put_grant(
    app_id: int, purpose: LlmPurpose, config_ref: str, payload: AppLlmGrantWrite,
    db: Session = Depends(grant_db),
) -> dict:
    """Require a system admin for an explicit grant decision."""
    return _write_grant(app_id, purpose, config_ref, db, payload)


@router.put("/by-client-id/{client_id}/llm-grants/{purpose}/{config_ref}",
            response_model=AppLlmGrantRead, dependencies=[Depends(require_system_admin)])
def put_client_grant(
    purpose: LlmPurpose, config_ref: str, payload: AppLlmGrantWrite,
    app_id: int = Depends(client_app_id), db: Session = Depends(grant_db),
) -> dict:
    """Apply the same admin-only grant decision through a client-ID alias."""
    return _write_grant(app_id, purpose, config_ref, db, payload)


@router.delete("/{app_id}/llm-grants/{purpose}/{config_ref}", status_code=204,
               dependencies=[Depends(require_system_admin)])
def revoke_grant(
    app_id: int, purpose: LlmPurpose, config_ref: str, db: Session = Depends(grant_db),
) -> None:
    """Retain a disabled row when an administrator revokes a grant."""
    _write_grant(app_id, purpose, config_ref, db)


@router.delete("/by-client-id/{client_id}/llm-grants/{purpose}/{config_ref}", status_code=204,
               dependencies=[Depends(require_system_admin)])
def revoke_client_grant(
    purpose: LlmPurpose, config_ref: str, app_id: int = Depends(client_app_id),
    db: Session = Depends(grant_db),
) -> None:
    """Revoke the same grant through its client-ID alias."""
    _write_grant(app_id, purpose, config_ref, db)
