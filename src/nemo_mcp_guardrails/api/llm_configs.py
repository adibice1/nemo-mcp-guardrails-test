from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from nemo_mcp_guardrails.api.app_schemas import LlmConfigCreate, LlmConfigRead
from nemo_mcp_guardrails.api.management_auth import require_management_user
from nemo_mcp_guardrails.database.connection import get_db
from nemo_mcp_guardrails.database.models import LlmConfigRecord
from nemo_mcp_guardrails.llm_credentials import LlmCredentialError, validate_llm_credential_reference
from nemo_mcp_guardrails.llm_security import LlmEndpointError, validate_llm_endpoint
from nemo_mcp_guardrails.management_permissions import require_system_admin


router = APIRouter(
    prefix="/llm-configs",
    tags=["llm-configs"],
    dependencies=[Depends(require_management_user)],
)


@router.get("", response_model=list[LlmConfigRead], dependencies=[Depends(require_system_admin)])
def list_llm_configs(db: Session = Depends(get_db)) -> list[LlmConfigRecord]:
    """Return the readable model catalogue for system administrators."""

    return list(
        db.scalars(
            select(LlmConfigRecord).order_by(LlmConfigRecord.name)
        )
    )


@router.post(
    "", response_model=LlmConfigRead, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_system_admin)],
)
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

    try:
        credential_reference = validate_llm_credential_reference(payload.credential_reference)
    except LlmCredentialError as error:
        raise HTTPException(400, "LLM credential reference is not approved by backend configuration.") from error

    endpoint = (payload.endpoint or "").strip() or None
    if endpoint is not None:
        try:
            endpoint = validate_llm_endpoint(endpoint)
        except LlmEndpointError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    record = LlmConfigRecord(
        name=name,
        provider=payload.provider,
        model_name=model_name,
        endpoint=endpoint,
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
