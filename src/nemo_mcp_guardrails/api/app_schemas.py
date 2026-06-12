from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AppCreate(BaseModel):
    """Request body for creating a client app."""

    name: str
    client_id: str
    api_key: str = Field(min_length=16)
    authorized: bool = True
    main_llm_config_id: int | None = None
    guardrail_llm_config_id: int | None = None


class AppUpdate(BaseModel):
    """Request body for updating a client app."""

    name: str | None = None
    client_id: str | None = None
    api_key: str | None = Field(default=None, min_length=16)
    authorized: bool | None = None
    main_llm_config_id: int | None = None
    guardrail_llm_config_id: int | None = None


class AppRead(BaseModel):
    """Response body for one client app."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    client_id: str
    authorized: bool
    main_llm_config_id: int | None
    guardrail_llm_config_id: int | None
    created_at: datetime
    updated_at: datetime


class PolicyAssignmentCreate(BaseModel):
    """Request body for assigning one reusable policy."""

    policy_id: int
    enabled: bool = True


class PolicyAssignmentUpdate(BaseModel):
    """Request body for enabling or disabling one policy assignment."""

    enabled: bool


class AppPolicyAssignmentRead(BaseModel):
    """Response body for one app-specific policy assignment."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    app_id: int
    policy_id: int
    enabled: bool
    created_at: datetime
    updated_at: datetime


class GlobalPolicyAssignmentRead(BaseModel):
    """Response body for one mandatory global policy assignment."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    policy_id: int
    enabled: bool
    created_at: datetime
    updated_at: datetime
