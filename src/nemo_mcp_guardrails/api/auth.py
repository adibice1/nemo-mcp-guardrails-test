from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from nemo_mcp_guardrails.app_auth import authenticate_app
from nemo_mcp_guardrails.database.connection import get_db
from nemo_mcp_guardrails.database.models import AppRecord


def require_authenticated_app(
    x_app_id: Annotated[str | None, Header(alias="X-App-ID")] = None,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    db: Session = Depends(get_db),
) -> AppRecord:
    """Return the authenticated app or reject invalid credentials."""

    if not x_app_id or not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid app credentials",
        )

    app = authenticate_app(db, x_app_id, x_api_key)
    if app is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid app credentials",
        )

    return app
