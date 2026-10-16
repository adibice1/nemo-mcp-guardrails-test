from datetime import datetime, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from nemo_mcp_guardrails.api.management_auth_schemas import (
    ManagementLoginRequest,
    ManagementPasswordChange,
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
    hash_password,
    verify_password,
    temporary_password_is_valid,
)


router = APIRouter(prefix="/management-auth", tags=["management-auth"])
bearer_scheme = HTTPBearer(auto_error=False)
from nemo_mcp_guardrails.rate_limits import limit_operation

INVALID_CREDENTIALS = "Invalid email or password"
_DUMMY_PASSWORD_HASH = hash_password("gms-unrecognized-account")


def _user_response(user: UserRecord) -> ManagementUserRead:
    """Serialize the safe management-user identity."""

    return ManagementUserRead(
        id=user.id,
        email=user.email,
        name=user.name,
        username=user.username,
        system_role=user.system_role,
        must_change_password=bool(user.must_change_password),
    )


def require_management_user(
    request: Request,
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
    try:
        decode_access_token(credentials.credentials, user=user)
    except (jwt.InvalidTokenError, RuntimeError) as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        ) from error
    if user.must_change_password and (request.method, request.url.path) not in {
        ("GET", "/management-auth/me"), ("PUT", "/management-auth/me/password"),
    }:
        raise HTTPException(403, detail="Password replacement required")
    request.state.gms_management_actor = {
        "user_id": user.id,
        "email": user.email,
        "role": user.system_role,
    }
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
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> ManagementTokenResponse:
    """Authenticate one enabled management user."""

    limit_operation(request, "login", normalize_email(payload.email), 10, 300)
    user = db.scalar(
        select(UserRecord).where(
            UserRecord.email == normalize_email(payload.email),
            UserRecord.enabled.is_(True),
        )
    )
    valid_password = verify_password(payload.password, user.password_hash if user else _DUMMY_PASSWORD_HASH)
    if user is None or not valid_password or not temporary_password_is_valid(user):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS,
        )

    response.headers["Cache-Control"] = "no-store"
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


@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_current_password(
    payload: ManagementPasswordChange,
    request: Request,
    user: UserRecord = Depends(require_management_user),
    db: Session = Depends(get_db),
) -> Response:
    """Verify the current password and atomically replace only this user's hash."""

    limit_operation(request, "password-change", str(user.id), 20, 900)
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(400, detail="Current password is incorrect")
    if not payload.new_password.strip():
        raise HTTPException(400, detail="Choose a password containing more than whitespace")
    if verify_password(payload.new_password, user.password_hash):
        raise HTTPException(400, detail="Choose a different new password")
    old_hash = user.password_hash
    new_hash = hash_password(payload.new_password)
    result = db.execute(
        update(UserRecord)
        .where(UserRecord.id == user.id, UserRecord.password_hash == old_hash,
               UserRecord.must_change_password == bool(user.must_change_password),
               or_(UserRecord.must_change_password.is_(False),
                   UserRecord.temporary_password_expires_at > datetime.now(timezone.utc)))
        .values(password_hash=new_hash, must_change_password=False, temporary_password_expires_at=None),
        execution_options={"synchronize_session": False},
    )
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(409, detail="Password changed during this request. Sign in again.")
    db.commit()
    return Response(status_code=204, headers={"Cache-Control": "no-store"})
