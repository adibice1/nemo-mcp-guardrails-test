from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from nemo_mcp_guardrails.api.audit_log_schemas import (
    AuditLogPageRead,
    AuditLogRead,
    AuditOutcome,
)
from nemo_mcp_guardrails.database.connection import get_db
from nemo_mcp_guardrails.database.models import ManagementAuditLogRecord
from nemo_mcp_guardrails.management_permissions import require_system_admin


router = APIRouter(
    prefix="/audit-logs",
    tags=["audit-logs"],
    dependencies=[Depends(require_system_admin)],
)


@router.get("", response_model=AuditLogPageRead)
def list_audit_logs(
    response: Response,
    entity_type: str | None = Query(default=None, min_length=1, max_length=100),
    outcome: AuditOutcome | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=10000),
    db: Session = Depends(get_db),
) -> AuditLogPageRead:
    """List sanitized management mutations for an administrator."""

    response.headers["Cache-Control"] = "no-store"
    query = select(ManagementAuditLogRecord)
    if entity_type is not None:
        query = query.where(
            ManagementAuditLogRecord.entity_type == entity_type
        )
    if outcome is not None:
        query = query.where(ManagementAuditLogRecord.outcome == outcome)

    records = list(
        db.scalars(
            query.order_by(
                ManagementAuditLogRecord.occurred_at.desc(),
                ManagementAuditLogRecord.id.desc(),
            )
            .offset(offset)
            .limit(limit + 1)
        )
    )
    return AuditLogPageRead(
        items=[AuditLogRead.model_validate(record) for record in records[:limit]],
        limit=limit,
        offset=offset,
        has_more=len(records) > limit,
    )
