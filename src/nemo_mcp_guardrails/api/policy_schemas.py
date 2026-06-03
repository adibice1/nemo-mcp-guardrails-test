from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


PolicyType = Literal["input", "output"]
PolicyEffect = Literal["allow", "block"]


class PolicyCreate(BaseModel):
    """Request body for creating a policy."""

    policy_type: PolicyType
    app: str | None = None
    action: str | None = None
    resource: str | None = None
    category: str | None = None
    description: str | None = None
    effect: PolicyEffect = "block"
    enabled: bool = True


class PolicyUpdate(BaseModel):
    """Request body for updating a policy."""

    policy_type: PolicyType | None = None
    app: str | None = None
    action: str | None = None
    resource: str | None = None
    category: str | None = None
    description: str | None = None
    effect: PolicyEffect | None = None
    enabled: bool | None = None


class PolicyRead(BaseModel):
    """Response body for a stored policy."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    policy_type: str
    app: str | None
    action: str | None
    resource: str | None
    category: str | None
    description: str | None
    effect: str
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
    expected_tools: str | None = None
    enabled: bool = True


class AllowedTestCaseUpdate(BaseModel):
    """Request body for updating an allowed test case."""

    name: str | None = None
    prompt: str | None = None
    expected_tools: str | None = None
    enabled: bool | None = None


class AllowedTestCaseRead(BaseModel):
    """Response body for a stored allowed test case."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    prompt: str
    expected_tools: str | None
    enabled: bool
    created_at: datetime
    updated_at: datetime
