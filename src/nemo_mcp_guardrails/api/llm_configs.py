import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from nemo_mcp_guardrails.api.app_schemas import LlmConfigCreate, LlmConfigRead
from nemo_mcp_guardrails.api.management_auth import require_management_user
from nemo_mcp_guardrails.database.connection import get_db
from nemo_mcp_guardrails.database.models import LlmConfigRecord


router = APIRouter(
    prefix="/llm-configs",
    tags=["llm-configs"],
    dependencies=[Depends(require_management_user)],
)
ENV_VAR_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@router.get("", response_model=list[LlmConfigRead])
def list_llm_configs(db: Session = Depends(get_db)) -> list[LlmConfigRecord]:
    """Return readable LLM configurations for management forms."""

    return list(
        db.scalars(
            select(LlmConfigRecord).order_by(LlmConfigRecord.name)
        )
    )


@router.post("", response_model=LlmConfigRead, status_code=status.HTTP_201_CREATED)
def create_llm_config(
    payload: LlmConfigCreate,
    db: Session = Depends(get_db),
) -> LlmConfigRecord:
    """Create one Azure-compatible LLM configuration without storing a key."""

    name = payload.name.strip()
    model_name = payload.model_name.strip()
    if not name or not model_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Configuration name and deployment name are required",
        )

    credential_reference = (payload.credential_reference or "").strip() or None
    if credential_reference is not None:
        if not credential_reference.startswith("env:"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only env:VARIABLE_NAME credential references are supported",
            )
        env_var_name = credential_reference.removeprefix("env:").strip()
        if not ENV_VAR_NAME_PATTERN.fullmatch(env_var_name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Credential environment variable name is invalid",
            )
        credential_reference = f"env:{env_var_name}"

    record = LlmConfigRecord(
        name=name,
        provider=payload.provider,
        model_name=model_name,
        endpoint=(payload.endpoint or "").strip() or None,
        credential_reference=credential_reference,
        enabled=payload.enabled,
    )
    db.add(record)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An LLM configuration with this name already exists",
        ) from error

    db.refresh(record)
    return record
