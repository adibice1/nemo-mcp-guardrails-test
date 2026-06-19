from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AppCreate(BaseModel):
    """Request body for creating a client app."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Test App",
                "client_id": "test-app",
                "api_key": "replace-with-strong-api-key",
                "authorized": True,
                "main_llm_config_id": None,
                "guardrail_llm_config_id": None,
            }
        }
    )

    name: str
    client_id: str
    api_key: str = Field(min_length=16)
    authorized: bool = True
    main_llm_config_id: int | None = None
    guardrail_llm_config_id: int | None = None


class AppUpdate(BaseModel):
    """Request body for updating a client app."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Updated Test App",
                "authorized": True,
                "main_llm_config_id": None,
                "guardrail_llm_config_id": None,
            }
        }
    )

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
    display_label: str
    authorized: bool
    main_llm_config_id: int | None
    guardrail_llm_config_id: int | None
    created_at: datetime
    updated_at: datetime


class AppConnectorCreate(BaseModel):
    """Request body for linking an app to a connector."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "connector_name": "github",
                "credential_reference": "env:GITHUB_PERSONAL_ACCESS_TOKEN",
                "enabled": True,
            }
        }
    )

    connector_id: int | None = None
    connector_name: str | None = None
    credential_reference: str | None = None
    enabled: bool = True


class AppConnectorUpdate(BaseModel):
    """Request body for updating one app connector link."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "credential_reference": "env:GITHUB_PERSONAL_ACCESS_TOKEN",
                "enabled": True,
            }
        }
    )

    credential_reference: str | None = None
    enabled: bool | None = None


class AppConnectorRead(BaseModel):
    """Response body for one app connector link."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    app_id: int
    app_label: str
    connector_id: int
    connector_name: str
    connector_display_name: str
    credential_reference: str | None
    enabled: bool
    connector_enabled: bool
    created_at: datetime
    updated_at: datetime


class PolicyAssignmentCreate(BaseModel):
    """Request body for assigning one or more reusable policies."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "policy_ids": [26],
                "enabled": True,
            }
        }
    )

    policy_ids: list[int] = Field(min_length=1)
    enabled: bool = True


class PolicyAssignmentUpdate(BaseModel):
    """Request body for enabling or disabling one policy assignment."""

    enabled: bool


class PolicyAssignmentBulkUpdate(BaseModel):
    """Request body for enabling or disabling multiple policy assignments."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "policy_ids": [12, 13, 26],
                "enabled": False,
            }
        }
    )

    policy_ids: list[int] = Field(min_length=1)
    enabled: bool


class PolicyAssignmentBulkDelete(BaseModel):
    """Request body for deleting multiple policy assignments."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "policy_ids": [12, 13, 26],
            }
        }
    )

    policy_ids: list[int] = Field(min_length=1)


class PolicyAssignmentBulkDeleteResponse(BaseModel):
    """Response body for deleting multiple policy assignments."""

    deleted_policy_ids: list[int]
    deleted_assignment_ids: list[int]
    deleted_count: int


class AppPolicyAssignmentRead(BaseModel):
    """Response body for one app-specific policy assignment."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    app_id: int
    app_label: str
    policy_id: int
    policy_label: str
    policy_type: str
    connector: str | None
    action: str | None
    resource: str | None
    category: str | None
    enabled: bool
    created_at: datetime
    updated_at: datetime


class GlobalPolicyAssignmentRead(BaseModel):
    """Response body for one mandatory global policy assignment."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    policy_id: int
    policy_label: str
    policy_type: str
    connector: str | None
    action: str | None
    resource: str | None
    category: str | None
    enabled: bool
    created_at: datetime
    updated_at: datetime


class EffectivePolicyAssignmentRead(BaseModel):
    """Response body for one effective app/global policy assignment."""

    assignment_id: int
    scope: str
    policy_id: int
    policy_label: str
    policy_type: str
    connector: str | None
    action: str | None
    resource: str | None
    category: str | None
    enabled: bool
    created_at: datetime
    updated_at: datetime


class EffectivePolicyAssignmentsRead(BaseModel):
    """Response body for all policies assigned to one app."""

    app_id: int
    app_label: str
    global_assignment_count: int
    app_assignment_count: int
    enabled_assignment_count: int
    disabled_assignment_count: int
    global_assignments: list[EffectivePolicyAssignmentRead]
    app_assignments: list[EffectivePolicyAssignmentRead]
