import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from nemo_mcp_guardrails.api.management_auth_schemas import (
    ManagementLoginRequest,
    ManagementProfileUpdate,
    ManagementSignupRequest,
    ManagementTokenResponse,
    ManagementUserRead,
)
from nemo_mcp_guardrails.database.connection import get_db
from nemo_mcp_guardrails.database.models import UserRecord
from nemo_mcp_guardrails.management_auth import (
    create_access_token,
    decode_access_token,
    normalize_email,
    verify_password,
)


router = APIRouter(prefix="/management-auth", tags=["management-auth"])
bearer_scheme = HTTPBearer(auto_error=False)
INVALID_CREDENTIALS = "Invalid email or password"


def _user_response(user: UserRecord) -> ManagementUserRead:
    """Serialize the safe management-user identity."""

    return ManagementUserRead(
        id=user.id,
        email=user.email,
        name=user.name,
        username=user.username,
        system_role=user.system_role,
    )


def require_management_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> UserRecord:
    """Require a valid bearer token for an enabled management user."""

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    try:
        user_id = decode_access_token(credentials.credentials)
    except (jwt.InvalidTokenError, RuntimeError) as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        ) from error

    user = db.get(UserRecord, user_id)
    if user is None or not user.enabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user


@router.post(
    "/signup",
    response_model=ManagementTokenResponse,
)
def signup(
    payload: ManagementSignupRequest,
    db: Session = Depends(get_db),
) -> ManagementTokenResponse:
    """Reject public signup; administrators create users now."""

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Public signup is disabled. Ask a GMS administrator to create your account.",
    )


@router.post("/login", response_model=ManagementTokenResponse)
def login(
    payload: ManagementLoginRequest,
    db: Session = Depends(get_db),
) -> ManagementTokenResponse:
    """Authenticate one enabled management user."""

    user = db.scalar(
        select(UserRecord).where(
            UserRecord.email == normalize_email(payload.email),
            UserRecord.enabled.is_(True),
        )
    )
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS,
        )

    return ManagementTokenResponse(
        access_token=create_access_token(user),
        user=_user_response(user),
    )


@router.get("/me", response_model=ManagementUserRead)
def current_user(
    user: UserRecord = Depends(require_management_user),
) -> ManagementUserRead:
    """Return the current management-user identity."""

    return _user_response(user)


@router.put("/me", response_model=ManagementUserRead)
def update_current_user(
    payload: ManagementProfileUpdate,
    user: UserRecord = Depends(require_management_user),
    db: Session = Depends(get_db),
) -> ManagementUserRead:
    """Update the current user's editable name and unique username."""

    name = payload.name.strip()
    username = payload.username.strip()
    if not name or not username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name and username are required",
        )

    user.name = name
    user.username = username
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This username is already in use",
        ) from error

    db.refresh(user)
    return _user_response(user)
