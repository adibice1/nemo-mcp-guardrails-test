from typing import Literal

from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    """One prior conversation message supplied by the client app."""

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class GuardrailsRunRequest(BaseModel):
    """Request body for one guarded runtime execution."""

    message: str = Field(min_length=1)
    conversation_id: str | None = None
    conversation_history: list[ConversationMessage] = Field(default_factory=list)


class GuardrailsRunResponse(BaseModel):
    """Response body for one guarded runtime execution."""

    status: str
    app_id: int
    client_id: str
    conversation_id: str | None
    response: str
    input_rail_status: str
    output_rail_status: str | None
    tool_names: list[str]
    input_policy_count: int
    input_rule_count: int
    output_rule_count: int
    blocked_tools: list[str]
    history_truncated: bool
    history_messages_received: int
    history_messages_loaded: int
    history_messages_used: int
