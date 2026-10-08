from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


AuditOutcome = Literal["succeeded", "rejected", "failed"]


class AuditLogRead(BaseModel):
    """Expose one sanitized management audit record."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    request_id: str
    occurred_at: datetime
    actor_user_id: int | None
    actor_email: str | None
    actor_role: str | None
    action: str
    entity_type: str
    target_path: str
    http_method: str
    http_status: int
    outcome: AuditOutcome
    client_ip: str | None


class AuditLogPageRead(BaseModel):
    """Return a bounded page of management audit records."""

    items: list[AuditLogRead]
    limit: int
    offset: int
    has_more: bool
