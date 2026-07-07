from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from nemo_mcp_guardrails.api.management_auth import require_management_user
from nemo_mcp_guardrails.database.connection import get_db
from nemo_mcp_guardrails.database.models import (
    AppRecord,
    AppUserRecord,
    UserRecord,
)


APP_MANAGE_ROLES = {"admin", "owner"}


def require_system_admin(
    user: UserRecord = Depends(require_management_user),
) -> UserRecord:
    """Require an authenticated system administrator."""

    if user.system_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )
    return user


def require_app_route_access(
    request: Request,
    user: UserRecord = Depends(require_management_user),
    db: Session = Depends(get_db),
) -> UserRecord:
    """Require an app developer link for app routes."""

    app_id = request.path_params.get("app_id")
    client_id = request.path_params.get("client_id")
    if app_id is None and client_id is None:
        return user

    if app_id is not None:
        app = db.get(AppRecord, int(app_id))
    else:
        app = db.scalar(select(AppRecord).where(AppRecord.client_id == client_id))
    if app is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App not found",
        )

    if user.system_role == "admin":
        return user

    link = db.scalar(
        select(AppUserRecord).where(
            AppUserRecord.app_id == app.id,
            AppUserRecord.user_id == user.id,
        )
    )
    if link is None or link.role not in APP_MANAGE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this app",
        )
    return user
