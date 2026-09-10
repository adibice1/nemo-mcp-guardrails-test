from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from nemo_mcp_guardrails.api.runtime_log_schemas import (
    RuntimeLogDetailRead,
    RuntimeLogPageRead,
    RuntimeLogRead,
    RuntimeOutcome,
)
from nemo_mcp_guardrails.database.connection import get_db
from nemo_mcp_guardrails.database.models import RuntimeLogRecord
from nemo_mcp_guardrails.management_permissions import require_system_admin


router = APIRouter(
    prefix="/runtime-logs",
    tags=["runtime-logs"],
    dependencies=[Depends(require_system_admin)],
)


@router.get("", response_model=RuntimeLogPageRead)
def list_runtime_logs(
    response: Response,
    app_id: int | None = Query(default=None, ge=1),
    outcome: RuntimeOutcome | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=10000),
    db: Session = Depends(get_db),
) -> RuntimeLogPageRead:
    """List runtime requests across apps for an authenticated administrator."""
    response.headers["Cache-Control"] = "no-store"
    query = select(RuntimeLogRecord)
    if app_id is not None:
        query = query.where(RuntimeLogRecord.app_id == app_id)
    if outcome is not None:
        query = query.where(RuntimeLogRecord.outcome == outcome)

    records = list(db.scalars(
        query.order_by(
            RuntimeLogRecord.started_at.desc(),
            RuntimeLogRecord.request_id.desc(),
        ).offset(offset).limit(limit + 1)
    ))
    return RuntimeLogPageRead(
        items=[
            RuntimeLogRead.model_validate(record)
            for record in records[:limit]
        ],
        limit=limit,
        offset=offset,
        has_more=len(records) > limit,
    )


@router.get("/{request_id}", response_model=RuntimeLogDetailRead)
def get_runtime_log(
    response: Response,
    request_id: str = Path(pattern=r"^[0-9a-f]{32}$"),
    db: Session = Depends(get_db),
) -> RuntimeLogDetailRead:
    """Read one request and its sequence-ordered execution events."""
    response.headers["Cache-Control"] = "no-store"
    record = db.scalar(
        select(RuntimeLogRecord)
        .where(RuntimeLogRecord.request_id == request_id)
        .options(selectinload(RuntimeLogRecord.events))
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Runtime log not found")
    return RuntimeLogDetailRead.model_validate(record)
