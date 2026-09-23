from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


RuntimeOutcome = Literal[
    "started", "passed", "blocked", "tool_error",
    "completed", "rejected", "redirected", "error",
]


class RuntimeLogRead(BaseModel):
    """Expose only approved runtime request metadata."""

    model_config = ConfigDict(from_attributes=True)

    request_id: str
    schema_version: str
    app_id: int | None
    started_at: datetime
    completed_at: datetime | None
    http_status: int | None
    outcome: str
    duration_ms: float | None


class RuntimeLogEventRead(BaseModel):
    """Expose ordered execution metadata without request content."""

    model_config = ConfigDict(from_attributes=True)

    sequence: int
    timestamp: datetime
    event: str
    severity: str
    stage: str
    outcome: str
    duration_ms: float | None
    tool_name: str | None
    reason_code: str | None


class RuntimeLogDetailRead(RuntimeLogRead):
    """Include the observed execution timeline for one request."""

    events: list[RuntimeLogEventRead]


class RuntimeLogPageRead(BaseModel):
    """Return a bounded page without an expensive total-count query."""

    items: list[RuntimeLogRead]
    limit: int
    offset: int
    has_more: bool


class RuntimeUserLogRead(BaseModel):
    """Expose the submitted input and final user-visible response."""

    model_config = ConfigDict(from_attributes=True)

    request_id: str
    conversation_id: str | None
    input_text: str
    response_text: str | None
