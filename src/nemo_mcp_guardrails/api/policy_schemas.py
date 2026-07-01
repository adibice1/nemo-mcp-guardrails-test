from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


PolicyType = Literal["input", "output"]
PolicyEffect = Literal["allow", "block"]


class PolicyCreate(BaseModel):
    """Request body for creating a policy."""

    policy_type: PolicyType
    connector: str | None = None
    action: str | None = None
    resource: str | None = None
    category: str | None = None
    description: str | None = None
    effect: PolicyEffect = "block"
    priority: int = 100
    conditions: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class PolicyUpdate(BaseModel):
    """Request body for updating a policy."""

    policy_type: PolicyType | None = None
    connector: str | None = None
    action: str | None = None
    resource: str | None = None
    category: str | None = None
    description: str | None = None
    effect: PolicyEffect | None = None
    priority: int | None = None
    conditions: dict[str, Any] | None = None
    enabled: bool | None = None


class PolicyAssignmentResolutionCreate(BaseModel):
    """Request body for resolving and assigning one policy definition."""

    policy: PolicyCreate
    display_name: str | None = Field(default=None, max_length=300)


class PolicyResourceOption(BaseModel):
    """One resource available for a connector action."""

    value: str
    label: str


class PolicyActionOption(BaseModel):
    """One connector action and its valid resources."""

    value: str
    label: str
    resources: list[PolicyResourceOption]


class PolicyConnectorOption(BaseModel):
    """One connector and its policy-capable action catalogue."""

    value: str
    label: str
    actions: list[PolicyActionOption]


class PolicyRead(BaseModel):
    """Response body for a stored policy."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    policy_type: str
    connector_id: int | None
    action_id: int | None
    resource_id: int | None
    connector: str | None
    action: str | None
    resource: str | None
    category: str | None
    description: str | None
    effect: str
    priority: int
    conditions: dict[str, Any]
    policy_version: int
    enabled: bool
    created_at: datetime
    updated_at: datetime


class CompiledTestPrompt(BaseModel):
    """Response body for one generated blocked prompt test."""

    name: str
    prompt: str


class CompilePreviewResponse(BaseModel):
    """Response body for previewing active policy compiler output."""

    input_rules: list[str]
    blocked_tools: list[str]
    test_prompts: list[CompiledTestPrompt]
    output_rules: list[str]


class AllowedTestCaseCreate(BaseModel):
    """Request body for creating an allowed test case."""

    name: str
    prompt: str
    expected_tools: list[str] = Field(default_factory=list)
    enabled: bool = True


class AllowedTestCaseUpdate(BaseModel):
    """Request body for updating an allowed test case."""

    name: str | None = None
    prompt: str | None = None
    expected_tools: list[str] | None = None
    enabled: bool | None = None


class AllowedTestCaseRead(BaseModel):
    """Response body for a stored allowed test case."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    prompt: str
    expected_tools: str | None
    normalized_expected_tools: list[str]
    enabled: bool
    created_at: datetime
    updated_at: datetime


class CompiledPolicyRuleRead(BaseModel):
    """Response body for one compiled policy rule."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    policy_id: int
    rail_type: str
    rule_text: str
    policy_version: int
    stale: bool
    enabled: bool
    generated_at: datetime
    created_at: datetime
    updated_at: datetime


class CompileAndStoreRulesResponse(BaseModel):
    """Response body for compiling active policies into stored rail rules."""

    rules: list[CompiledPolicyRuleRead]
