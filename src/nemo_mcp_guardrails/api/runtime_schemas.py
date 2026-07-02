from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ConversationMessage(BaseModel):
    """One prior conversation message supplied by the client app."""

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


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
    input_rail_source: str | None
    input_rail_categories: list[str] = Field(default_factory=list)
    output_rail_status: str | None
    output_rail_source: str | None
    output_rail_categories: list[str] = Field(default_factory=list)
    tool_guard_status: str
    tool_guard_source: str | None
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
