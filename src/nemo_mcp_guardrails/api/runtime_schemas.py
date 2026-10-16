from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from nemo_mcp_guardrails.request_limits import MAX_MESSAGE_CHARS, MAX_HISTORY_TURNS, MAX_HISTORY_CHARS


class ConversationMessage(BaseModel):
    """One prior conversation message supplied by the client app."""

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)


class GuardrailsRunRequest(BaseModel):
    """Request body for one guarded runtime execution."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "List recent pull requests in github/github-mcp-server.",
                "conversation_id": "demo-conversation-1",
                "conversation_history": [
                    {
                        "role": "user",
                        "content": "Search for the github/github-mcp-server repo.",
                    },
                    {
                        "role": "assistant",
                        "content": "I found github/github-mcp-server.",
                    },
                ],
            }
        }
    )

    message: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)
    conversation_id: str | None = Field(default=None, min_length=1, max_length=200)
    conversation_history: list[ConversationMessage] = Field(default_factory=list, max_length=MAX_HISTORY_TURNS)

    @model_validator(mode="after")
    def validate_history_size(self):
        """Reject aggregate context growth before constructing any runtime."""
        if sum(len(turn.content) for turn in self.conversation_history) > MAX_HISTORY_CHARS:
            raise ValueError("Conversation history is too large.")
        if self.conversation_id is not None and (not self.conversation_id.strip() or any(ord(c) < 32 for c in self.conversation_id)):
            raise ValueError("Conversation ID cannot be blank.")
        if any("\x00" in text for text in [self.message, *(turn.content for turn in self.conversation_history)]):
            raise ValueError("Messages cannot contain null characters.")
        return self


class GuardrailsRunResponse(BaseModel):
    """Response body for one guarded runtime execution."""

    status: str
    app_id: int
    client_id: str
    conversation_id: str | None
    response: str
    input_rail_status: str
    input_rail_source: str | None
    input_rail_categories: list[str] = Field(default_factory=list)
    output_rail_status: str | None
    output_rail_source: str | None
    output_rail_categories: list[str] = Field(default_factory=list)
    tool_guard_status: str
    tool_guard_source: str | None
    block_stage: str | None = None
    block_reason: str | None = None
    blocked_policy_id: int | None = None
    blocked_policy_name: str | None = None
    tool_names: list[str]
    input_policy_count: int
    input_rule_count: int
    output_rule_count: int
    blocked_tools: list[str]
    history_truncated: bool
    history_messages_received: int
    history_messages_loaded: int
    history_messages_used: int
    debug_agent_response: str | None = None
    debug_output_rail_source: str | None = None
    debug_output_rule_texts: list[str] | None = None
    debug_tool_trace: list[dict[str, Any]] | None = None
