"""Register an app-owned main model with its own encrypted provider key."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from nemo_mcp_guardrails.api.app_llm_grants import client_app_id, grant_db
from nemo_mcp_guardrails.api.app_schemas import AppMainModelCreate, LlmConfigRead
from nemo_mcp_guardrails.database.models import AppLlmGrantRecord, AppRecord, LlmConfigRecord
from nemo_mcp_guardrails.llm_credentials import LlmCredentialError
from nemo_mcp_guardrails.llm_security import LlmEndpointError
from nemo_mcp_guardrails.management_permissions import require_app_route_access
from nemo_mcp_guardrails.model_credentials import encrypt_model_key, owned_profile_endpoint
from nemo_mcp_guardrails.rate_limits import limit_operation


router = APIRouter(prefix="/apps", tags=["app-main-models"],
                   dependencies=[Depends(require_app_route_access)])


def _register(app_id: int, payload: AppMainModelCreate, request: Request,
              response: Response, db: Session) -> LlmConfigRecord:
    """Atomically create an owned profile and a main-only grant without selecting it."""
    app = db.get(AppRecord, app_id)
    if app is None:
        raise HTTPException(404, "App not found")
    limit_operation(request, "main-model-create", str(app_id), 20, 900)
    try:
        endpoint = owned_profile_endpoint(payload.provider, payload.endpoint)
    except (LlmEndpointError, ValueError) as error:
        raise HTTPException(400, "Model destination is not approved by backend configuration.") from error
    try:
        encrypted = encrypt_model_key(payload.api_key.get_secret_value(), app_id=app_id,
                                      provider=payload.provider, endpoint=endpoint,
                                      model_name=payload.model_name)
    except LlmCredentialError as error:
        raise HTTPException(503, "Model credential storage is unavailable.") from error
    record = LlmConfigRecord(name=payload.name, provider=payload.provider,
                             model_name=payload.model_name, endpoint=endpoint,
                             owner_app_id=app_id, encrypted_api_key=encrypted,
                             credential_reference=None, enabled=True)
    try:
        db.add(record)
        db.flush()
        db.add(AppLlmGrantRecord(app_id=app_id, purpose="main",
                                 llm_config_id=record.id, enabled=True))
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(409, "A model profile with this name already exists.") from error
    db.refresh(record)
    response.headers["Cache-Control"] = "no-store"
    return record


@router.post("/{app_id}/main-models", response_model=LlmConfigRead,
             status_code=status.HTTP_201_CREATED)
def register_main_model(app_id: int, payload: AppMainModelCreate, request: Request,
                        response: Response, db: Session = Depends(grant_db)) -> LlmConfigRecord:
    """Allow linked app developers/admins to register their own main model."""
    return _register(app_id, payload, request, response, db)


@router.post("/by-client-id/{client_id}/main-models", response_model=LlmConfigRead,
             status_code=status.HTTP_201_CREATED)
def register_client_main_model(payload: AppMainModelCreate, request: Request, response: Response,
                               app_id: int = Depends(client_app_id),
                               db: Session = Depends(grant_db)) -> LlmConfigRecord:
    """Use identical authorization and persistence for the client-ID alias."""
    return _register(app_id, payload, request, response, db)
