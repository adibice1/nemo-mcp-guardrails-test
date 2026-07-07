import re
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from nemo_mcp_guardrails.api.management_user_schemas import (
    ManagedUserCreate,
    ManagedUserCreateRead,
    ManagedUserPasswordResetRead,
    ManagedUserRead,
    ManagedUserUpdate,
    UserAppLinkCreate,
    UserAppLinkRead,
)
from nemo_mcp_guardrails.database.connection import get_db
from nemo_mcp_guardrails.database.models import (
    AppRecord,
    AppUserRecord,
    UserRecord,
)
from nemo_mcp_guardrails.management_auth import hash_password, normalize_email
from nemo_mcp_guardrails.management_permissions import require_system_admin


router = APIRouter(
    prefix="/management-users",
    tags=["management-users"],
    dependencies=[Depends(require_system_admin)],
)

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
TEMPORARY_PASSWORD_NOTICE = (
    "Copy this temporary password now. It will not be shown again."
)


def _temporary_password() -> str:
    """Generate one admin-issued temporary password."""

    return f"gms-{secrets.token_urlsafe(24)}"


def _require_valid_email(email: str) -> str:
    """Normalize and validate one email address."""

    normalized = normalize_email(email)
    if not EMAIL_PATTERN.fullmatch(normalized):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A valid email address is required",
        )
    return normalized


def _require_user(user_id: int, db: Session) -> UserRecord:
    """Return one user or raise a not-found response."""

    user = db.get(UserRecord, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


def _require_app(payload: UserAppLinkCreate, db: Session) -> AppRecord:
    """Return one app from a numeric ID or client ID."""

    if payload.app_id is not None:
        app = db.get(AppRecord, payload.app_id)
    else:
        app = db.scalar(
            select(AppRecord).where(AppRecord.client_id == payload.client_id)
        )

    if app is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App not found",
        )
    return app


def _serialize_user(user: UserRecord) -> ManagedUserRead:
    """Serialize one admin-managed GMS user."""

    return ManagedUserRead.model_validate(user)


def _serialize_link(link: AppUserRecord) -> UserAppLinkRead:
    """Serialize one user/app role assignment."""

    return UserAppLinkRead(
        id=link.id,
        user_id=link.user_id,
        user_email=link.user.email,
        app_id=link.app_id,
        app_name=link.app.name,
        client_id=link.app.client_id,
        role=link.role,
        created_at=link.created_at,
        updated_at=link.updated_at,
    )


@router.get("", response_model=list[ManagedUserRead])
def list_managed_users(db: Session = Depends(get_db)) -> list[ManagedUserRead]:
    """Return all GMS users for administrators."""

    users = list(
        db.scalars(select(UserRecord).order_by(UserRecord.email, UserRecord.id))
    )
    return [_serialize_user(user) for user in users]


@router.post(
    "",
    response_model=ManagedUserCreateRead,
    status_code=status.HTTP_201_CREATED,
)
def create_managed_user(
    payload: ManagedUserCreate,
    db: Session = Depends(get_db),
) -> ManagedUserCreateRead:
    """Create one admin-managed user and return its temporary password once."""

    email = _require_valid_email(payload.email)
    temporary_password = _temporary_password()
    user = UserRecord(
        email=email,
        name=(payload.name or email).strip(),
        username=(payload.username or email).strip(),
        password_hash=hash_password(temporary_password),
        system_role=payload.system_role,
        enabled=payload.enabled,
    )
    if not user.name or not user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name and username cannot be blank",
        )

    db.add(user)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email or username already exists",
        ) from error

    db.refresh(user)
    return ManagedUserCreateRead(
        **_serialize_user(user).model_dump(),
        temporary_password=temporary_password,
        temporary_password_notice=TEMPORARY_PASSWORD_NOTICE,
    )


@router.put("/{user_id}", response_model=ManagedUserRead)
def update_managed_user(
    user_id: int,
    payload: ManagedUserUpdate,
    db: Session = Depends(get_db),
) -> ManagedUserRead:
    """Update one admin-managed user."""

    user = _require_user(user_id, db)
    values = payload.model_dump(exclude_unset=True)
    for field, value in values.items():
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{field} cannot be blank",
                )
        setattr(user, field, value)

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email or username already exists",
        ) from error

    db.refresh(user)
    return _serialize_user(user)


@router.post("/{user_id}/password", response_model=ManagedUserPasswordResetRead)
def reset_managed_user_password(
    user_id: int,
    db: Session = Depends(get_db),
) -> ManagedUserPasswordResetRead:
    """Reset one user's password and return the temporary password once."""

    user = _require_user(user_id, db)
    temporary_password = _temporary_password()
    user.password_hash = hash_password(temporary_password)
    db.commit()
    db.refresh(user)
    return ManagedUserPasswordResetRead(
        user_id=user.id,
        email=user.email,
        temporary_password=temporary_password,
        temporary_password_notice=TEMPORARY_PASSWORD_NOTICE,
    )


@router.get("/{user_id}/apps", response_model=list[UserAppLinkRead])
def list_managed_user_apps(
    user_id: int,
    db: Session = Depends(get_db),
) -> list[UserAppLinkRead]:
    """Return app role assignments for one user."""

    _require_user(user_id, db)
    links = list(
        db.scalars(
            select(AppUserRecord)
            .where(AppUserRecord.user_id == user_id)
            .join(AppUserRecord.app)
            .order_by(AppRecord.name, AppUserRecord.id)
        )
    )
    return [_serialize_link(link) for link in links]


@router.post(
    "/{user_id}/apps",
    response_model=UserAppLinkRead,
    status_code=status.HTTP_201_CREATED,
)
def link_managed_user_app(
    user_id: int,
    payload: UserAppLinkCreate,
    db: Session = Depends(get_db),
) -> UserAppLinkRead:
    """Create or update one user/app role assignment."""

    user = _require_user(user_id, db)
    app = _require_app(payload, db)
    link = db.scalar(
        select(AppUserRecord).where(
            AppUserRecord.user_id == user.id,
            AppUserRecord.app_id == app.id,
        )
    )
    if link is None:
        link = AppUserRecord(user_id=user.id, app_id=app.id, role=payload.role)
        db.add(link)
    else:
        link.role = payload.role

    db.commit()
    db.refresh(link)
    return _serialize_link(link)


@router.delete("/{user_id}/apps/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
def unlink_managed_user_app(
    user_id: int,
    app_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Remove one user/app role assignment."""

    _require_user(user_id, db)
    link = db.scalar(
        select(AppUserRecord).where(
            AppUserRecord.user_id == user_id,
            AppUserRecord.app_id == app_id,
        )
    )
    if link is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not linked to this app",
        )

    db.delete(link)
    db.commit()
