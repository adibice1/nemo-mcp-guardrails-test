from pydantic import BaseModel, Field


class GuardrailsRunRequest(BaseModel):
    """Request body for one guarded runtime execution."""

    message: str = Field(min_length=1)
    conversation_id: str | None = None


class GuardrailsRuntimeContextResponse(BaseModel):
    """Response body proving an app-scoped runtime context was prepared."""

    status: str
    app_id: int
    client_id: str
    input_policy_count: int
    input_rule_count: int
    output_rule_count: int
    blocked_tools: list[str]
